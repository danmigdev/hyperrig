"""Observe the HYW1 gate-zero path; default/import perform no device I/O.

This client cannot send erase, program or finish-sector commands. Its single
qualification path is identity -> explicit SPI init -> first-sector backup
comparison -> ARM -> one260-byte STAGE -> exact256-byte echo -> retained audit.
The runner owns ROM entry, slot history, artifact pinning and return to stock.
No phase is retried after an error, timeout or ambiguous transport completion.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.probe_mini_recovery import MiniRamSession,WindowsRomTransport,RAM_SLOTS,validate_ram_request
from tools.build_mini_app_writer import (APP_START,APP_END,SECTOR_BYTES,PAGE_BYTES,DEFAULT_PLAN,
    validate_plan,inspect_writer_elf,validate_audit_record,workspace_file)

PROFILE="app-writer-observer"
OPCODES=(0xFC78,0xFC79,0xFC7A,0xFB7C,0xFD87,0xFC7E,0xFD7F,0xFD88)


def sha(data):return hashlib.sha256(data).hexdigest()
def crc(data):return zlib.crc32(data)&0xFFFFFFFF
def require(condition,message):
    if not condition:raise ValueError(message)
def integer(value,low,high,name):
    require(type(value) is int and low<=value<=high,"invalid "+name)
    return value
def app_range(address,length,alignment=1):
    integer(address,APP_START,APP_END-1,"application address")
    integer(length,1,APP_END-address,"application length")
    require(not address%alignment,"unaligned application address")


def simple_cdb(op):
    require(op in (0xFC78,0xFC79,0xFC7E,0xFD88),"not a simple HYW1 observer command")
    return op.to_bytes(2,"big")+b"\xff"*14


def read_cdb(address,length):
    app_range(address,length);integer(length,1,512,"read length")
    return b"\xfd\x7f"+struct.pack(">IH",address,length)+b"\xff"*8


def arm_cdb(address,preimage_crc,target_crc):
    app_range(address,SECTOR_BYTES,SECTOR_BYTES)
    integer(preimage_crc,0,0xFFFFFFFF,"preimage CRC");integer(target_crc,0,0xFFFFFFFF,"target CRC")
    return b"\xfc\x7a"+struct.pack(">III",address,preimage_crc,target_crc)+b"\xff"*2


def stage_cdb(token,sequence,address):
    integer(token,1,0xFFFFFFFF,"sector token");integer(sequence,2,0xFFFFFFFF,"next sequence")
    app_range(address,PAGE_BYTES,PAGE_BYTES)
    return b"\xfb\x7c"+struct.pack(">IIIH",token,sequence,address,PAGE_BYTES)


def echo_cdb(token,sequence,address):
    integer(token,1,0xFFFFFFFF,"sector token");integer(sequence,2,0xFFFFFFFF,"staging sequence")
    app_range(address,PAGE_BYTES,PAGE_BYTES)
    return b"\xfd\x87"+struct.pack(">III",token,sequence,address)+b"\xff"*2


def stage_packet(page):
    require(isinstance(page,bytes) and len(page)==PAGE_BYTES,"exact256-byte immutable page required")
    return page+struct.pack(">I",crc(page))


def validate_writer_observer_request(cdb,data_out,read_length,*,slot):
    require(isinstance(cdb,bytes) and type(read_length) is int,"CDB bytes and integer transfer length required")
    if cdb==bytes((0x12,0,0,0,36,0)) or cdb[:2] in (b"\xfb\x06",b"\xfd\x07",b"\xfb\x08"):
        validate_ram_request(cdb,data_out,read_length,slot=slot);return
    require(slot in RAM_SLOTS and len(cdb)==16,"HYW1 requires an exact CDB and known RAM slot")
    opcode=int.from_bytes(cdb[:2],"big")
    require(opcode in OPCODES,"command forbidden by the gate-zero observer profile")
    if opcode==0xFB7C:
        token,seq,address,n=struct.unpack_from(">IIIH",cdb,2)
        require(n==PAGE_BYTES and isinstance(data_out,bytes) and len(data_out)==260 and read_length==0,
                "STAGE requires exact OUT260 and no IN phase")
        require(data_out==stage_packet(data_out[:PAGE_BYTES]),"STAGE packet CRC differs")
        expected=stage_cdb(token,seq,address)
    else:
        require(data_out is None,"observer reply command cannot include OUT data")
        if opcode==0xFD7F:
            address,n=struct.unpack_from(">IH",cdb,2)
            require(read_length==n,"read transfer count differs")
            expected=read_cdb(address,n)
        elif opcode==0xFD87:
            require(read_length==PAGE_BYTES,"echo must return exact256 bytes")
            expected=echo_cdb(*struct.unpack_from(">III",cdb,2))
        elif opcode==0xFC7A:
            require(read_length==16,"ARM reply length differs")
            expected=arm_cdb(*struct.unpack_from(">III",cdb,2))
        else:
            require(read_length==(128 if opcode==0xFD88 else 16),"HYW1 reply length differs")
            expected=simple_cdb(opcode)
    require(cdb==expected,"HYW1 reserved bytes or field encoding differs")


@dataclass(frozen=True)
class WriterObservation:
    slot:int
    build_tag:int
    image:bytes
    image_sha256:str
    elf_sha256:str
    manifest_sha256:str
    plan_sha256:str
    candidate_sha256:str
    backup_sha256:str
    preimage:bytes
    target_sector:bytes

    def __post_init__(self):
        require(self.slot in RAM_SLOTS,"unsupported writer slot")
        integer(self.build_tag,0,0xFFFFFFFF,"writer build tag")
        require(isinstance(self.image,bytes) and self.image and sha(self.image)==self.image_sha256,"writer payload hash differs")
        require(isinstance(self.preimage,bytes) and len(self.preimage)==SECTOR_BYTES
                and isinstance(self.target_sector,bytes) and len(self.target_sector)==SECTOR_BYTES,
                "complete first-sector preimage and target required")
        for value in (self.elf_sha256,self.manifest_sha256,self.plan_sha256,self.candidate_sha256,self.backup_sha256):
            require(isinstance(value,str) and len(value)==64 and all(c in "0123456789abcdef" for c in value),"SHA256 required")

    @property
    def page(self):return self.target_sector[:PAGE_BYTES]
    @property
    def preimage_crc(self):return crc(self.preimage)
    @property
    def target_crc(self):return crc(self.target_sector)

    def summary(self):
        return {"slot":self.slot,"build_tag":self.build_tag,"image_sha256":self.image_sha256,
                "elf_sha256":self.elf_sha256,"manifest_sha256":self.manifest_sha256,"plan_sha256":self.plan_sha256,
                "candidate_sha256":self.candidate_sha256,"backup_sha256":self.backup_sha256,
                "sector_address":APP_START,"sector_bytes":SECTOR_BYTES,"page_address":APP_START,"page_bytes":PAGE_BYTES,
                "preimage_sha256":sha(self.preimage),"preimage_crc32":self.preimage_crc,
                "target_sector_sha256":sha(self.target_sector),"target_sector_crc32":self.target_crc,
                "page_sha256":sha(self.page),"page_crc32":crc(self.page),"NVM_commands_available":False}


def prepare_observation(plan_path=ROOT/DEFAULT_PLAN,writer_manifest_path=ROOT/"research/mini-app-writer.json",*,slot=RAM_SLOTS[0]):
    """Read/verify local files only. Never constructs a transport or session."""
    require(slot in RAM_SLOTS,"unsupported writer slot")
    plan_raw=workspace_file(plan_path).read_bytes();manifest_raw=workspace_file(writer_manifest_path).read_bytes()
    plan=json.loads(plan_raw);manifest=json.loads(manifest_raw)
    require(manifest.get("kind")=="bounded-app-writer-design" and manifest.get("target")=="tank-mini"
            and manifest.get("target_mutations_enabled") is False,"expected the frozen mutation-disabled MINI writer")
    require(manifest["install_plan"]["sha256"]==sha(plan_raw),"writer manifest refers to a different install plan")
    for name,digest in manifest["source_sha256"].items():
        require(sha(workspace_file(name).read_bytes())==digest,"frozen writer source changed: "+name)
    candidate=workspace_file(plan["candidate"]["path"]).read_bytes()
    backup=workspace_file(plan["unit_backup"]["path"]).read_bytes()
    rollback=workspace_file(plan["rollback"]["path"]).read_bytes()
    validate_plan(plan,candidate,backup,rollback)
    require(manifest["install_plan"]["candidate"]["sha256"]==sha(candidate)
            and manifest["install_plan"]["unit_backup"]["sha256"]==sha(backup),"manifest image/backup differs")
    artifacts=[a for a in manifest["executable_artifacts"] if a["base"]==slot]
    require(len(artifacts)==1,"writer slot artifact missing or duplicated")
    artifact=artifacts[0];image=workspace_file(artifact["file"]).read_bytes();elf=workspace_file(artifact["elf"]).read_bytes()
    require(sha(image)==artifact["payload_sha256"] and sha(elf)==artifact["elf_sha256"],"writer artifact hash differs")
    checked,metadata=inspect_writer_elf(elf,slot)
    require(checked==image and all(artifact.get(k)==v for k,v in metadata.items()),"writer ELF metadata differs")
    return WriterObservation(slot,manifest["build_tag"],image,sha(image),sha(elf),sha(manifest_raw),sha(plan_raw),
                             sha(candidate),sha(backup),backup[APP_START:APP_START+SECTOR_BYTES],candidate[:SECTOR_BYTES])


class WindowsWriterObserverTransport(WindowsRomTransport):
    """Only explicit construction opens an already identified ROM disk."""
    def __init__(self,path,*,slot):super().__init__(path,slot=slot,profile=PROFILE)


class MiniAppWriterObserverSession(MiniRamSession):
    def __init__(self,transport,observation,*,known_free_slot=False,known_uploaded_unstarted=False):
        require(isinstance(observation,WriterObservation),"verified observation plan required")
        super().__init__(transport,slot=observation.slot,known_free_slot=known_free_slot,
                         known_uploaded_unstarted=known_uploaded_unstarted)
        self.observation=observation;self.phase="created";self.token=self.sequence=self.read_bytes=0
        self.last_record=None;self.raw_records=[];self.audit_records=[];self.last_status=None;self.last_status_raw=None
        self.last_sector=b"";self.last_echo=None;self.last_result=None;self.preimage_verified=False
        self.arm_submitted=False;self.arm_consumed_for_stage=False;self.stage_submitted=False
        self.stage_confirmed=False;self.echo_requested=False;self.echo_verified=False
        self.ambiguous_operation=None;self.pending_operation=None

    def read(self,address,length):raise ValueError("HYW1 observer never exposes arbitrary FD61 memory reads")

    def _bound_image(self,image,expected_sha256):
        require(image==self.observation.image and expected_sha256==self.observation.image_sha256,
                "RAM lifecycle must use this observation's pinned writer payload")

    def upload_only(self,image,*,expected_sha256):
        self._bound_image(image,expected_sha256)
        return super().upload_only(image,expected_sha256=expected_sha256)

    def verify_upload_only(self,image,*,expected_sha256):
        self._bound_image(image,expected_sha256)
        return super().verify_upload_only(image,expected_sha256=expected_sha256)

    def start_reset_once(self,*args,**kwargs):
        raise ValueError("use a separate reset session with independently known nonlive slot history")

    def _exchange(self,cdb,*,data_out=None,read_length=0):
        validate_writer_observer_request(cdb,data_out,read_length,slot=self.slot)
        return self.transport.exchange(cdb,data_out=data_out,read_length=read_length)

    def _status_reply(self,opcode,raw,*,phase,value,token=None,sequence=None):
        self.last_status_raw=raw
        require(len(raw)==16 and raw[:2]==opcode.to_bytes(2,"big"),"HYW1 status framing differs")
        item={"opcode":opcode,"error":raw[2],"phase":raw[3],"token":int.from_bytes(raw[4:8],"big"),
              "sequence":int.from_bytes(raw[8:12],"big"),"value":int.from_bytes(raw[12:16],"big"),"raw_hex":raw.hex()}
        self.last_status=item
        require(item["error"]==0 and item["phase"]==phase and item["value"]==value
                and item["token"]==(self.token if token is None else token)
                and item["sequence"]==(self.sequence if sequence is None else sequence),"HYW1 status/state/token/sequence differs")
        return item

    def _audit(self,*,phase,last_crc,read_bytes=None,staged=0,echoed=0,initialized=True):
        raw=self._exchange(simple_cdb(0xFD88),read_length=128)
        self.last_record=raw;self.raw_records.append(raw)
        item=validate_audit_record(raw,base=self.slot,build_tag=self.observation.build_tag,expected_mutations_enabled=False)
        self.audit_records.append(item)
        require(item["error"]==0 and item["phase"]==phase and item["token"]==self.token
                and item["sequence"]==self.sequence and item["last_crc32"]==last_crc,
                "HYW1 audit state/token/sequence/CRC differs")
        require(item["read_bytes"]==(self.read_bytes if read_bytes is None else read_bytes)
                and item["status_polls"]==0 and item["page_bitmap"]==0
                and item["staged"]==staged and item["echoed"]==echoed,
                "HYW1 audit counters/staging differ")
        require(item["rx_guards_ok"]==item["stack_guards_ok"]==1,"HYW1 RX/private stack guard failed")
        if initialized:
            require(item["jedec"]==0xEB6014 and not item["sr1"]&0x7F and not item["sr2"]&0x40,
                    "HYW1 JEDEC/protection/WIP/WEL differs")
            require(item["stack_observed_bytes"]>0,"target private stack use was not observed")
        else:
            require(item["jedec"]==item["sr1"]==item["sr2"]==item["stack_observed_bytes"]==0,
                    "entry performed unexpected peripheral work")
        if self.token:
            require(item["sector"]==APP_START and item["preimage_crc32"]==self.observation.preimage_crc
                    and item["target_crc32"]==self.observation.target_crc,"armed sector/CRC differs from current plan")
        else:
            require(item["sector"]==item["preimage_crc32"]==item["target_crc32"]==0,
                    "sector already armed before this observation")
        if staged:
            require(item["page"]==APP_START and item["page_crc32"]==crc(self.observation.page)
                    and item["raw_receive_return"]==260,"staged page or raw receive result differs")
        else:
            require(item["page"]==item["page_crc32"]==0 and item["raw_receive_return"]==-2147483648,
                    "receive occurred before explicit staging")
        return item

    def _handshake(self):
        raw=self._exchange(simple_cdb(0xFC78),read_length=16)
        require(raw==b"\xfc\x78HYW1\1\0"+struct.pack(">II",self.slot,32768),"writer identity/slot/version/gate0 differs")
        audit=self._audit(phase=0,last_crc=0,initialized=False)
        self.phase="identified"
        return {"writer_identity_hex":raw.hex(),"writer_audit":audit,"target_mutations_enabled":False,
                "SPI_initialized_on_entry":False,"observer_plan":self.observation.summary()}

    def _begin(self,name,allowed_phase):
        require(self.ready and not self.failed and self.phase==allowed_phase,"fresh successful "+allowed_phase+" state required")
        self.pending_operation=name

    def _complete(self,phase,result):
        self.phase=phase;self.pending_operation=None;self.last_result=result
        return result

    def _failed(self):
        self.failed=True;self.ambiguous_operation=self.pending_operation

    def initialize_spi(self):
        self._begin("initialize_spi","identified")
        try:
            raw=self._exchange(simple_cdb(0xFC79),read_length=16)
            self._status_reply(0xFC79,raw,phase=1,value=0xEB6014)
            audit=self._audit(phase=1,last_crc=0xEB6014)
            return self._complete("initialized",{"initialized":True,"jedec_hex":"eb6014","audit":audit})
        except Exception:self._failed();raise

    def read_first_sector(self):
        self._begin("read_first_sector","initialized")
        try:
            for offset in range(0,SECTOR_BYTES,512):
                raw=self._exchange(read_cdb(APP_START+offset,512),read_length=512)
                require(len(raw)==512,"short NOR read; no retry")
                status=self._exchange(simple_cdb(0xFC7E),read_length=16)
                self._status_reply(0xFC7E,status,phase=1,value=crc(raw))
                self._audit(phase=1,last_crc=crc(raw),read_bytes=self.read_bytes+512)
                self.read_bytes+=512;self.last_sector+=raw
            require(self.last_sector==self.observation.preimage,"first-sector bytes differ from accepted backup")
            self.preimage_verified=True
            return self._complete("preimage_verified",{"sector_address":APP_START,"bytes":len(self.last_sector),
                "sha256":sha(self.last_sector),"matches_backup_byte_for_byte":True,"read_bytes":self.read_bytes})
        except Exception:self._failed();raise

    def arm_first_sector(self):
        self._begin("arm_first_sector","preimage_verified")
        require(self.preimage_verified and not self.arm_submitted,"preimage comparison and single ARM required")
        self.arm_submitted=True
        try:
            raw=self._exchange(arm_cdb(APP_START,self.observation.preimage_crc,self.observation.target_crc),read_length=16)
            self._status_reply(0xFC7A,raw,phase=2,value=self.observation.preimage_crc,token=1,sequence=1)
            self.token=self.sequence=1
            audit=self._audit(phase=2,last_crc=self.observation.preimage_crc,read_bytes=self.read_bytes+SECTOR_BYTES)
            self.read_bytes+=SECTOR_BYTES
            return self._complete("armed",{"token":self.token,"sequence":self.sequence,"audit":audit,
                                           "token_is_authentication":False})
        except Exception:self._failed();raise

    def stage_first_page(self):
        self._begin("stage_and_echo_first_page","armed")
        require(not self.arm_consumed_for_stage and not self.stage_submitted,"ARM already consumed for staging")
        self.arm_consumed_for_stage=True;self.sequence+=1
        packet=stage_packet(self.observation.page)
        try:
            self.stage_submitted=True
            raw=self._exchange(stage_cdb(self.token,self.sequence,APP_START),data_out=packet)
            require(raw==b"","STAGE unexpectedly produced an IN phase")
            raw=self._exchange(simple_cdb(0xFC7E),read_length=16)
            self._status_reply(0xFC7E,raw,phase=4,value=crc(self.observation.page))
            self._audit(phase=4,last_crc=crc(self.observation.page),staged=1,echoed=0)
            self.stage_confirmed=True;self.echo_requested=True
            echo=self._exchange(echo_cdb(self.token,self.sequence,APP_START),read_length=PAGE_BYTES)
            self.last_echo=echo
            require(echo==self.observation.page,"frozen page echo differs byte-for-byte from candidate")
            audit=self._audit(phase=4,last_crc=crc(self.observation.page),staged=1,echoed=1)
            self.echo_verified=True
            return self._complete("observed",{"observation_passed":True,"echo_sha256":sha(echo),"echo_bytes":len(echo),
                "echo_matches_candidate_byte_for_byte":True,"token":self.token,"sequence":self.sequence,
                "staging_sequence_consumed":True,"target_sector_remains_armed":True,"audit":audit,
                "wren_attempts":0,"erase_attempts":0,"program_attempts":0,"automatic_retry":False,
                "NVM_commands_available":False,"operational_writer_qualified":False})
        except Exception:self._failed();raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only",action="store_true",help="verify local plan/ELF/source hashes; no device")
    parser.add_argument("--plan",type=Path,default=ROOT/DEFAULT_PLAN)
    parser.add_argument("--writer-manifest",type=Path,default=ROOT/"research/mini-app-writer.json")
    parser.add_argument("--slot",type=lambda s:int(s,0),default=RAM_SLOTS[0])
    args=parser.parse_args()
    result={"device_io":False,"enumerated":False,"profile":PROFILE,"allowed_opcodes":[f"{op:04x}" for op in OPCODES],
            "erase_program_finish_commands_available":False,"automatic_retry":False}
    if args.check_only:result["verified_local_observation"]=prepare_observation(args.plan,args.writer_manifest,slot=args.slot).summary()
    print(json.dumps(result,indent=2))


if __name__=="__main__":main()
