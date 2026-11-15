"""Bounded HYW1 installer API. CLI/import only inspect local artifacts.

An external runner must explicitly construct the operational transport, prove
ROM/slot history, persist the journal, and qualify the candidate/recovery path.
This module never enumerates, enters ROM, resets, boots, or retries on its own.
A failed/ambiguous command permanently ends the installation session.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import probe_mini_app_writer as observer
from tools import build_mini_app_writer as frozen
from tools import build_mini_app_writer_operational as builder
from tools.probe_mini_recovery import MiniRamSession,WindowsRomTransport,RAM_SLOTS

sha,crc,require=observer.sha,observer.crc,observer.require
APP_START,APP_END,PAGE_BYTES,SECTOR_BYTES=builder.APP_START,builder.APP_END,256,4096
PROFILE="app-writer-operational"
MUTATIONS=(0xFC7B,0xFC7D)


def mutation_cdb(opcode,token,sequence,address):
    require(opcode in (0xFC7B,0xFC7D,0xFC80),"unknown installer action")
    observer.integer(token,1,0xFFFFFFFF,"sector token");observer.integer(sequence,2,0xFFFFFFFF,"next sequence")
    length=PAGE_BYTES if opcode==0xFC7D else SECTOR_BYTES
    observer.app_range(address,length,length)
    return opcode.to_bytes(2,"big")+struct.pack(">III",token,sequence,address)+b"\xff\xff"


def validate_writer_operational_request(cdb,data_out,read_length,*,slot):
    require(isinstance(cdb,bytes),"CDB must be immutable bytes")
    opcode=int.from_bytes(cdb[:2],"big")
    if opcode not in (0xFC7B,0xFC7D,0xFC80):
        observer.validate_writer_observer_request(cdb,data_out,read_length,slot=slot);return
    require(slot in RAM_SLOTS and len(cdb)==16 and data_out is None and type(read_length) is int
            and read_length==16,"action requires exact IN16 with no OUT payload")
    require(cdb==mutation_cdb(opcode,*struct.unpack_from(">III",cdb,2)),"action padding or bounds differ")


@dataclass(frozen=True)
class Installation:
    slot:int
    build_tag:int
    image:bytes
    image_sha256:str
    elf_sha256:str
    manifest_sha256:str
    plan_sha256:str
    candidate:bytes
    preimage:bytes
    backup_sha256:str
    sector_order:tuple
    purpose:str="install-candidate"
    fresh_full_read_sha256:str|None=None

    def __post_init__(self):
        require(self.slot in RAM_SLOTS,"unknown RAM slot")
        require(self.purpose in ("install-candidate","restore-stock"),"unknown installation purpose")
        observer.integer(self.build_tag,0,0xFFFFFFFF,"build tag")
        require(isinstance(self.image,bytes) and self.image and sha(self.image)==self.image_sha256,"writer image hash differs")
        require(isinstance(self.candidate,bytes) and isinstance(self.preimage,bytes)
                and len(self.candidate)==len(self.preimage)==APP_END-APP_START,"complete application bytes required")
        for value in (self.elf_sha256,self.manifest_sha256,self.plan_sha256,self.backup_sha256):
            require(isinstance(value,str) and len(value)==64 and all(c in "0123456789abcdef" for c in value),"SHA256 required")
        if self.fresh_full_read_sha256 is not None:
            value=self.fresh_full_read_sha256
            require(isinstance(value,str) and len(value)==64 and all(c in "0123456789abcdef" for c in value),"fresh full-read SHA256 required")
        require(self.purpose!="restore-stock" or self.fresh_full_read_sha256 is not None,
                "stock restoration requires a distinct fresh full-read hash")
        changed=[a for a in range(APP_START,APP_END,4096) if self.old_sector(a)!=self.new_sector(a)]
        order=[a for a in changed if a!=APP_START]+([APP_START] if APP_START in changed else [])
        require(type(self.sector_order) is tuple and self.sector_order==tuple(order),"changed sectors must be exact, unique and header-last")

    def old_sector(self,address):return self.preimage[address-APP_START:address-APP_START+4096]
    def new_sector(self,address):return self.candidate[address-APP_START:address-APP_START+4096]
    def page(self,address):return self.candidate[address-APP_START:address-APP_START+256]

    def summary(self):
        return {"slot":self.slot,"build_tag":self.build_tag,"image_sha256":self.image_sha256,
            "elf_sha256":self.elf_sha256,"manifest_sha256":self.manifest_sha256,"plan_sha256":self.plan_sha256,
            "candidate_sha256":sha(self.candidate),"preimage_sha256":sha(self.preimage),"backup_sha256":self.backup_sha256,
            "application_range":[APP_START,APP_END],"changed_sectors":len(self.sector_order),
            "sector_order":list(self.sector_order),"header_sector_page_order":builder.page_order(APP_START),
            "power_loss_atomicity_proven":False,"initial_header_invalidation":False,
            "target_mutations_enabled":True,"hardware_readiness_asserted":False,
            "purpose":self.purpose,"fresh_full_read_sha256":self.fresh_full_read_sha256}


def prepare_installation(plan_path=builder.DEFAULT_PLAN,manifest_path=builder.REPORT,*,slot=RAM_SLOTS[0]):
    """Verify local sources, exact plan, images, ELF gate1 and page order only."""
    inputs=builder.checked_inputs(plan_path);raw=frozen.workspace_file(manifest_path).read_bytes();manifest=json.loads(raw)
    require(manifest.get("kind")=="bounded-app-writer-operational" and manifest.get("target")=="tank-mini"
            and manifest.get("target_mutations_enabled") is True,"operational MINI writer manifest required")
    require(manifest["install_plan"]["sha256"]==inputs["plan_sha256"],"installer plan differs from operational build")
    for name,digest in manifest["source_sha256"].items():
        require(sha(frozen.workspace_file(name).read_bytes())==digest,"operational source changed: "+name)
    expected=builder.contract(inputs)
    for name in ("install_plan","sectors","derivation","pio_derivation","observer_evidence","timing_model","frozen_observer_manifest","physical_write_allowlist",
                 "header_sector_last","header_page_last","separate_early_header_invalidation","power_loss_atomicity_proven"):
        require(manifest[name]==expected[name],"operational contract changed: "+name)
    artifacts=[item for item in manifest["executable_artifacts"] if item["base"]==slot]
    require(len(artifacts)==1,"missing/duplicate operational slot")
    artifact=artifacts[0];image=frozen.workspace_file(artifact["file"]).read_bytes();elf=frozen.workspace_file(artifact["elf"]).read_bytes()
    checked,metadata=builder.inspect_operational_elf(elf,slot)
    require(checked==image and all(artifact.get(k)==v for k,v in metadata.items()),"operational ELF/payload/hash differs")
    return Installation(slot,manifest["build_tag"],image,sha(image),sha(elf),sha(raw),inputs["plan_sha256"],
        inputs["data"]["candidate"],inputs["data"]["rollback"],sha(inputs["data"]["unit_backup"]),tuple(inputs["plan"]["proposed_sector_order"]))


class WindowsAppWriterTransport(WindowsRomTransport):
    """Explicitly selected operational profile; never used by the offline CLI."""
    def __init__(self,path,*,slot):super().__init__(path,slot=slot,profile=PROFILE)


class MiniAppInstallerSession(MiniRamSession):
    def __init__(self,transport,installation,*,journal,known_free_slot=False,known_uploaded_unstarted=False):
        require(isinstance(installation,Installation) and callable(journal),"verified installation and durable journal callback required")
        super().__init__(transport,slot=installation.slot,known_free_slot=known_free_slot,
                         known_uploaded_unstarted=known_uploaded_unstarted)
        self.installation=installation;self.journal=journal;self.phase="created"
        self.expected={name:0 for name in ("phase","token","sequence","sector","page","preimage_crc32","target_crc32",
            "page_crc32","last_crc32","jedec","wren_attempts","erase_attempts","program_attempts","read_bytes",
            "status_polls","page_bitmap","staged","echoed")}
        self.expected["raw_receive_return"]=-2147483648
        self.next_token=1;self.pending_operation=None;self.ambiguous_operation=None;self.history=[]
        self.last_record=None;self.raw_records=[];self.last_audit=None;self.last_status_raw=None
        self.last_status=None;self.last_echo=None;self.last_page_readback=None
        self.initial_readback=bytearray();self.final_readback=bytearray();self.verified_sectors=[]
        self.preimage_verified=False;self.image_verified=False;self.mutation_command_submitted=False
        self.mutation_completion_unknown=False;self.journal_error=None;self.last_result=None

    @property
    def token(self):return self.expected["token"]
    @property
    def sequence(self):return self.expected["sequence"]

    def _event(self,event,**details):
        item={"event":event,"host_phase":self.phase,"pending_operation":self.pending_operation,
              "token":self.token,"sequence":self.sequence,**details}
        self.history.append(item);self.journal(item)

    def _image(self,image,expected_sha256):
        require(image==self.installation.image and expected_sha256==self.installation.image_sha256,"pinned operational payload required")

    def upload_only(self,image,*,expected_sha256):
        self._image(image,expected_sha256)
        self._event("ram_upload_intent",image_sha256=expected_sha256,slot=self.slot)
        return super().upload_only(image,expected_sha256=expected_sha256)

    def verify_upload_only(self,image,*,expected_sha256):
        self._image(image,expected_sha256)
        return super().verify_upload_only(image,expected_sha256=expected_sha256)

    def verify_and_start(self,image,*,expected_sha256):
        # The base routine consumes its one jump before exchange. The runner's
        # journal must mark execution unknown before that routine can submit it.
        self._image(image,expected_sha256);self._event("ram_verify_and_jump_intent",slot=self.slot)
        return super().verify_and_start(image,expected_sha256=expected_sha256)

    def read(self,*args):raise ValueError("operational writer exposes no arbitrary FD61 memory read")
    def start_reset_once(self,*args,**kwargs):raise ValueError("installer never resets or boots; use independent runner policy")

    def _exchange(self,cdb,*,data_out=None,read_length=0):
        validate_writer_operational_request(cdb,data_out,read_length,slot=self.slot)
        opcode=int.from_bytes(cdb[:2],"big")
        self._event("command_intent",opcode=f"{opcode:04x}",cdb_hex=cdb.hex(),read_length=read_length,
                    data_out_sha256=sha(data_out) if data_out is not None else None)
        if opcode in MUTATIONS:
            self.mutation_command_submitted=True;self.mutation_completion_unknown=True
        raw=self.transport.exchange(cdb,data_out=data_out,read_length=read_length)
        self._event("command_reply",opcode=f"{opcode:04x}",bytes=len(raw),sha256=sha(raw))
        return raw

    def _status(self,opcode,raw):
        self.last_status_raw=raw
        require(len(raw)==16 and raw[:2]==opcode.to_bytes(2,"big"),"HYW1 status framing differs")
        item={"error":raw[2],"phase":raw[3],"token":int.from_bytes(raw[4:8],"big"),
              "sequence":int.from_bytes(raw[8:12],"big"),"last_crc32":int.from_bytes(raw[12:16],"big")}
        self.last_status=item
        require(item["error"]==0 and all(item[k]==self.expected[k] for k in ("phase","token","sequence","last_crc32")),
                "HYW1 status failed/stale; no retry")
        return item

    def _audit(self,*,mutation=False,initialized=True):
        raw=self._exchange(observer.simple_cdb(0xFD88),read_length=128)
        self.last_record=raw;self.raw_records.append(raw)
        self._event("audit_raw",record_hex=raw.hex(),sha256=sha(raw))
        item=frozen.validate_audit_record(raw,base=self.slot,build_tag=self.installation.build_tag,expected_mutations_enabled=True)
        self.last_audit=item
        require(item["error"]==0 and item["rx_guards_ok"]==item["stack_guards_ok"]==1,"HYW1 error or guard failure")
        for name,value in self.expected.items():
            if name=="status_polls" and mutation:
                require(1<=item[name]-value<=65536,"mutation WIP polling count differs")
            else:require(item[name]==value,"HYW1 audit differs: "+name)
        require(not item["sr1"]&0x7F and not item["sr2"]&0x40,"NOR WIP/WEL/protection set")
        require(item["stack_observed_bytes"]>0 if initialized else item["stack_observed_bytes"]==0,"private stack observation differs")
        if not initialized:require(item["sr1"]==item["sr2"]==0,"SPI used on entry")
        if mutation:
            self.expected["status_polls"]=item["status_polls"]
            self.mutation_completion_unknown=False
        self._event("audit_verified",phase=item["phase"],wren=item["wren_attempts"],erase=item["erase_attempts"],program=item["program_attempts"])
        return item

    def _handshake(self):
        raw=self._exchange(observer.simple_cdb(0xFC78),read_length=16)
        require(raw==b"\xfc\x78HYW1\1\1"+struct.pack(">II",self.slot,32768),"operational gate1 identity differs")
        audit=self._audit(initialized=False);self.phase="identified"
        return {"writer_identity_hex":raw.hex(),"writer_audit":audit,"target_mutations_enabled":True,
                "SPI_initialized_on_entry":False,"installation":self.installation.summary()}

    def _begin(self,name,phase):
        require(self.ready and not self.failed and self.phase==phase,"fresh successful "+phase+" state required")
        self.pending_operation=name

    def _fail(self,error):
        self.failed=True;self.ambiguous_operation=self.pending_operation
        try:self._event("terminal_error",error_type=type(error).__name__,message=str(error),
                        mutation_completion_unknown=self.mutation_completion_unknown,automatic_retry=False,automatic_reset=False)
        except Exception as journal_error:self.journal_error=repr(journal_error)

    def initialize_spi(self):
        self._begin("initialize_spi","identified")
        try:
            raw=self._exchange(observer.simple_cdb(0xFC79),read_length=16)
            self.expected.update(phase=1,jedec=0xEB6014,last_crc32=0xEB6014)
            self._status(0xFC79,raw);audit=self._audit()
            self.phase="initialized";self.pending_operation=None
            return {"initialized":True,"audit":audit}
        except Exception as error:self._fail(error);raise

    def _read(self,address,length,expected_bytes):
        raw=self._exchange(observer.read_cdb(address,length),read_length=length)
        require(len(raw)==length,"short application read; no retry")
        self.expected["read_bytes"]+=length;self.expected["last_crc32"]=crc(raw)
        self._status(0xFC7E,self._exchange(observer.simple_cdb(0xFC7E),read_length=16));self._audit()
        require(raw==expected_bytes,"application readback differs byte-for-byte")
        return raw

    def verify_complete_preimage(self):
        self._begin("verify_complete_preimage","initialized")
        try:
            for offset in range(0,APP_END-APP_START,512):
                raw=self._read(APP_START+offset,512,self.installation.preimage[offset:offset+512])
                self.initial_readback.extend(raw)
            self.preimage_verified=True;self.phase="preimage_verified";self.pending_operation=None
            self._event("whole_preimage_verified",bytes=len(self.initial_readback),sha256=sha(self.initial_readback))
            return {"preimage_verified":True,"bytes":len(self.initial_readback),"sha256":sha(self.initial_readback)}
        except Exception as error:self._fail(error);raise

    def _stage_echo(self,address):
        page=self.installation.page(address)
        self.expected["sequence"]+=1
        self._event("stage_sequence_consumed",address=address,page_sha256=sha(page))
        raw=self._exchange(observer.stage_cdb(self.token,self.sequence,address),data_out=observer.stage_packet(page))
        require(raw==b"","STAGE returned unexpected IN data")
        self.expected.update(phase=4,page=address,page_crc32=crc(page),last_crc32=crc(page),raw_receive_return=260,staged=1,echoed=0)
        self._status(0xFC7E,self._exchange(observer.simple_cdb(0xFC7E),read_length=16));self._audit()
        self.last_echo=self._exchange(observer.echo_cdb(self.token,self.sequence,address),read_length=256)
        require(self.last_echo==page,"staging echo differs byte-for-byte; no WREN allowed")
        self.expected["echoed"]=1;self._audit()
        self._event("page_echo_verified",address=address,sha256=sha(page))

    def _erase(self,address):
        self.expected["sequence"]+=1
        self._event("erase_sequence_consumed",address=address)
        raw=self._exchange(mutation_cdb(0xFC7B,self.token,self.sequence,address),read_length=16)
        self.expected["wren_attempts"]+=1;self.expected["erase_attempts"]+=1
        self.expected["read_bytes"]+=8192;self.expected["last_crc32"]=crc(b"\xff"*4096)
        self._status(0xFC7B,raw);self._audit(mutation=True)
        for offset in range(0,4096,512):self._read(address+offset,512,b"\xff"*512)

    def _program(self,address):
        page=self.installation.page(address);self.expected["sequence"]+=1
        self._event("program_sequence_consumed",address=address,sha256=sha(page))
        raw=self._exchange(mutation_cdb(0xFC7D,self.token,self.sequence,address),read_length=16)
        self.expected.update(phase=3,staged=0,echoed=0,last_crc32=crc(page))
        self.expected["wren_attempts"]+=1;self.expected["program_attempts"]+=1;self.expected["read_bytes"]+=512
        self.expected["page_bitmap"]|=1<<((address-self.expected["sector"])//256)
        self._status(0xFC7D,raw);self._audit(mutation=True)
        self.last_page_readback=self._read(address,256,page)
        self._event("page_program_verified",address=address,sha256=sha(self.last_page_readback))

    def _sector(self,address):
        old=self.installation.old_sector(address);new=self.installation.new_sector(address)
        for offset in range(0,4096,512):self._read(address+offset,512,old[offset:offset+512])
        raw=self._exchange(observer.arm_cdb(address,crc(old),crc(new)),read_length=16)
        self.expected.update(phase=2,token=self.next_token,sequence=1,sector=address,preimage_crc32=crc(old),
                             target_crc32=crc(new),staged=0,echoed=0,page_bitmap=0,last_crc32=crc(old))
        self.expected["read_bytes"]+=4096;self.next_token+=1
        self._status(0xFC7A,raw);self._audit()
        order=builder.page_order(address)
        self._stage_echo(order[0]);self._erase(address)
        for index,page in enumerate(order):
            if index:self._stage_echo(page)
            self._program(page)
        self.expected["sequence"]+=1
        raw=self._exchange(mutation_cdb(0xFC80,self.token,self.sequence,address),read_length=16)
        self.expected.update(phase=5,token=0,last_crc32=crc(new));self.expected["read_bytes"]+=4096
        self._status(0xFC80,raw);self._audit()
        for offset in range(0,4096,512):self._read(address+offset,512,new[offset:offset+512])
        self.verified_sectors.append(address)
        self._event("sector_verified",address=address,sha256=sha(new),program_page_order=order)

    def install_application(self):
        self._begin("install_application","preimage_verified")
        require(self.preimage_verified,"whole preimage comparison required before mutation")
        try:
            self.phase="installing"
            for address in self.installation.sector_order:
                self.pending_operation=f"sector_{address:08x}";self._sector(address)
            self.phase="verifying_final";self.pending_operation="verify_complete_application"
            for offset in range(0,APP_END-APP_START,512):
                raw=self._read(APP_START+offset,512,self.installation.candidate[offset:offset+512])
                self.final_readback.extend(raw)
            require(bytes(self.final_readback)==self.installation.candidate,"final whole image differs")
            self.image_verified=True;self.phase="complete";self.pending_operation=None
            self.last_result={"application_verified":True,"application_sha256":sha(self.final_readback),
                "bytes":len(self.final_readback),"verified_sectors":self.verified_sectors.copy(),
                "wren_attempts":self.expected["wren_attempts"],"erase_attempts":self.expected["erase_attempts"],
                "program_attempts":self.expected["program_attempts"],"rom_session_remains_active":True,
                "application_boot_attempted":False,"automatic_reset":False,"automatic_retry":False,
                "power_loss_atomicity_proven":False,"hardware_runtime_qualified":False}
            self._event("application_verified",**self.last_result)
            return self.last_result
        except Exception as error:self._fail(error);raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only",action="store_true",help="verify local plan/artifact/source hashes")
    parser.add_argument("--plan",type=Path,default=builder.DEFAULT_PLAN)
    parser.add_argument("--manifest",type=Path,default=builder.REPORT)
    parser.add_argument("--slot",type=lambda value:int(value,0),default=RAM_SLOTS[0])
    args=parser.parse_args()
    result={"device_io":False,"enumerated":False,"profile":PROFILE,"automatic_retry":False,
            "automatic_reset":False,"CLI_executes_installation":False}
    if args.check_only:result["verified_local_installation"]=prepare_installation(args.plan,args.manifest,slot=args.slot).summary()
    print(json.dumps(result,indent=2))


if __name__=="__main__":main()
