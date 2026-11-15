"""Explicit read-only BLE NUS probe for HyperRig MINI M5.71.

Default/import only inspect local protocol evidence. `scan` explicitly scans;
`read --address ...` scans once for that address, connects without requesting
pairing, subscribes to NUS TX, and reuses the USB read-only parser/allowlist.
No PAIR-characteristic read, bond/auth/key command, mutation or reconnect exists.
This tests the desktop BLE protocol, not the Android application.
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.metadata
import json
from pathlib import Path
import queue
import re
import sys
import threading

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import probe_mini_app as usb

EXPECTED_VERSION="tankm_fw M5.71 rel ble"
NUS={"service":"6e400001-b5a3-f393-e0a9-e50e24dcca9e",
     "rx":"6e400002-b5a3-f393-e0a9-e50e24dcca9e",
     "tx":"6e400003-b5a3-f393-e0a9-e50e24dcca9e",
     "pair":"6e400004-b5a3-f393-e0a9-e50e24dcca9e"}
CHUNK=20
CONNECT_TIMEOUT=12.0
WRITE_TIMEOUT=1.0
CLOSE_TIMEOUT=3.0
READ_WAIT=.05
MAX_NOTIFICATIONS=512
AppProbeError=usb.AppProbeError


def source_contract():
    contract=usb.source_contract()
    source=usb.checked(usb.SOURCE/"web/tankg.html",usb.SOURCE_SHA).decode("utf-8")
    declaration='const NUS = { svc: "'+NUS["service"]+'", rx: "'+NUS["rx"]+'", tx: "'+NUS["tx"]+'", pair: "'+NUS["pair"]+'" };'
    anchors=(declaration,'name: "Bluetooth", maxLine: 190, chunk: 20',
        'txc.addEventListener("characteristicvaluechanged"', 'await txc.startNotifications();',
        'for (let i = 0; i < b.length; i += this.chunk)',
        'await this.rxc.writeValueWithResponse(part)', 'if (desk) return "ro";',
        'const rd = () => B.read({ deviceId: id, service: NUS.svc, characteristic: NUS.pair, timeout: 30000 });')
    if not all(anchor in source for anchor in anchors):
        raise AppProbeError("pinned editor BLE framing/pairing anchors changed")
    return {**contract,"transport":"ble-nus","NUS":NUS.copy(),"chunk_bytes":CHUNK,
        "writes_with_response":True,"notifications_are_text_stream":True,"expected_firmware_version":EXPECTED_VERSION,
        "source_lines":{"NUS":4298,"desktop_readonly_pair_skip":4355,"notify":4442,"write":4465},
        "PAIR_characteristic_read":False,"pair_requested":False,"auth_or_key_commands":False,
        "android_native_bridge_tested":False,"USB_transport_tested":False}


def environment_info():
    try:version=importlib.metadata.version("bleak")
    except importlib.metadata.PackageNotFoundError:version=None
    return {"current_python":sys.executable,"current_bleak_version":version,
            "existing_workspace_python":str(ROOT/".venv/Scripts/python.exe"),
            "workspace_python_exists":(ROOT/".venv/Scripts/python.exe").is_file()}


def address(value):
    if not isinstance(value,str) or not re.fullmatch(r"[0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5}",value):
        raise AppProbeError("select an explicit six-byte Bluetooth address, not a name/prefix")
    return value.upper()


def scan_timeout(value):
    if type(value) not in (int,float) or not 0<value<=30:
        raise AppProbeError("scan timeout must be positive and at most30 seconds")
    return float(value)


def advertised_record(device,advertisement):
    services=[str(u).lower() for u in (getattr(advertisement,"service_uuids",None) or [])]
    name=getattr(advertisement,"local_name",None) or getattr(device,"name",None)
    stock=bool(name and str(name).upper().startswith("TANK MINI"))
    role=("nus-candidate-needs-exact-tankm-pong" if NUS["service"] in services else
          "stock-mini-name-not-hyperrig-identity" if stock else "unidentified-advertisement")
    return {"address":str(getattr(device,"address","")),"name":name,"service_uuids":services,
            "rssi":getattr(advertisement,"rssi",None),"role":role,"identity_established":False}


async def discover(*,timeout=8.0,scanner=None):
    """Explicit, bounded scan; results never select a device automatically."""
    duration=scan_timeout(timeout)
    if scanner is None:
        try:from bleak import BleakScanner
        except ImportError as error:raise AppProbeError("use the workspace .venv Python with Bleak installed") from error
        scanner=BleakScanner
    values=await asyncio.wait_for(scanner.discover(timeout=duration,return_adv=True),duration+1)
    if not isinstance(values,dict):raise AppProbeError("Bleak did not return advertisement metadata")
    return [(device,advertisement,advertised_record(device,advertisement)) for device,advertisement in values.values()]


def choose(discovered,selected_address):
    selected_address=address(selected_address)
    matches=[row for row in discovered if row[2]["address"].upper()==selected_address]
    if len(matches)!=1:raise AppProbeError("exactly one fresh advertisement must match the selected Bluetooth address")
    return matches[0]


class BleNusTransport:
    """Async Bleak owner with a bounded synchronous adapter for ReadOnlyProbe.

    Only `open` performs Bluetooth operations. Run the existing synchronous
    parser in asyncio.to_thread; BLE callbacks stay on the owner event loop.
    Notifications are byte chunks, never assumed to coincide with text lines.
    """
    def __init__(self):
        self.client=None;self.loop=None;self.loop_thread=None;self.rxc=None;self.txc=None
        self.notifications=queue.Queue(maxsize=MAX_NOTIFICATIONS);self.lock=threading.Lock()
        self.pending_bytes=0;self.remainder=b"";self.error=None;self.closed=False;self.closing=False;self.subscribed=False

    def _poison(self,error):
        with self.lock:
            if self.error is None:self.error=error

    def _check(self):
        if self.error is not None:raise AppProbeError("BLE session stopped: "+str(self.error))
        if self.closed or self.closing:raise AppProbeError("BLE transport closed")
        if self.client is None or not self.client.is_connected:raise AppProbeError("BLE connection lost")

    def _notification(self,_sender,data):
        if self.closing or self.closed:return
        try:
            raw=bytes(data)
            if not raw:return
            with self.lock:
                if self.error is not None:return
                if self.pending_bytes+len(raw)>usb.MAX_RESPONSE:raise AppProbeError("BLE notification byte bound exceeded")
                self.notifications.put_nowait(raw);self.pending_bytes+=len(raw)
        except Exception as error:self._poison(error)

    def _disconnected(self,_client):
        if not self.closing and not self.closed:self._poison(AppProbeError("BLE connection lost; no reconnect"))

    @classmethod
    async def open(cls,device,*,client_factory=None):
        if isinstance(device,str) or not getattr(device,"address",None):
            raise AppProbeError("a freshly selected BLEDevice is required; no implicit address scan")
        if client_factory is None:
            try:from bleak import BleakClient
            except ImportError as error:raise AppProbeError("use the workspace .venv Python with Bleak installed") from error
            client_factory=BleakClient
        self=cls();self.loop=asyncio.get_running_loop();self.loop_thread=threading.get_ident()
        self.client=client_factory(device,pair=False,timeout=CONNECT_TIMEOUT,
                                  winrt={"use_cached_services":False},disconnected_callback=self._disconnected)
        try:
            await asyncio.wait_for(self.client.connect(),CONNECT_TIMEOUT)
            self._check()
            service=self.client.services.get_service(NUS["service"])
            if service is None:raise AppProbeError("selected device has no HyperRig NUS service")
            def characteristic(uuid,property_name):
                chars=[c for c in service.characteristics if str(c.uuid).lower()==uuid]
                if len(chars)!=1 or property_name not in chars[0].properties:
                    raise AppProbeError("NUS characteristic missing/ambiguous or unsupported: "+uuid)
                return chars[0]
            self.rxc=characteristic(NUS["rx"],"write");self.txc=characteristic(NUS["tx"],"notify")
            await asyncio.wait_for(self.client.start_notify(self.txc,self._notification),CONNECT_TIMEOUT)
            self.subscribed=True;self._check()
            return self
        except BaseException:
            try:await self.aclose()
            except Exception:pass
            raise

    def _worker(self):
        if threading.get_ident()==self.loop_thread:
            raise AppProbeError("run the synchronous protocol parser in asyncio.to_thread")
        self._check()

    def read(self,size):
        self._worker()
        if type(size) is not int or size<=0 or size>usb.MAX_RESPONSE:raise AppProbeError("invalid BLE read size")
        if self.remainder:raw=self.remainder
        else:
            try:raw=self.notifications.get(timeout=READ_WAIT)
            except queue.Empty:
                self._check();return b""
        self._check();part=raw[:size];self.remainder=raw[size:]
        with self.lock:self.pending_bytes-=len(part)
        return part

    async def _write(self,data):
        self._check()
        for offset in range(0,len(data),CHUNK):
            self._check()
            await self.client.write_gatt_char(self.rxc,data[offset:offset+CHUNK],response=True)
        self._check()

    def write(self,data):
        self._worker()
        allowed={(name+"\n").encode("ascii") for name in ("PING",*usb.QUERIES)}
        if not isinstance(data,bytes) or data not in allowed:
            raise AppProbeError("BLE adapter accepts only the same literal read-only commands as USB")
        future=asyncio.run_coroutine_threadsafe(self._write(data),self.loop)
        try:future.result(timeout=WRITE_TIMEOUT)
        except BaseException as error:
            future.cancel();self._poison(error)
            raise AppProbeError("BLE write failed or timed out; no retry") from error
        return len(data)

    async def aclose(self):
        if self.closed:return
        self.closing=True
        try:
            if self.client is not None:
                # Disconnect removes subscriptions; never read PAIR, unpair,
                # reset the pedal, or create a replacement client here.
                await asyncio.wait_for(self.client.disconnect(),CLOSE_TIMEOUT)
        finally:self.closed=True


async def run_read(args,*,scanner=None,client_factory=None):
    evidence=source_contract();selected_address=address(args.address);scan_timeout(args.scan_timeout)
    profile=usb.load_profile(args.firmware_manifest)
    if profile["firmware_version"]!=EXPECTED_VERSION or not profile["capabilities"]["read"]:
        raise AppProbeError("requires a read-capable manifest for exact tankm_fw M5.71 rel ble")
    if len(set(args.queries))!=len(args.queries) or any(name not in usb.QUERIES for name in args.queries):
        raise AppProbeError("queries must be unique literal read-only commands")
    journal=usb.Journal(args.log);transport=None
    try:
        journal("start",source=evidence,expected_firmware=EXPECTED_VERSION,expected_image_sha256=profile["image_sha256"],
                image_hash_attested_by_device=False,pair_requested=False,write_commands_enabled=False)
        device,_advertisement,record=choose(await discover(timeout=args.scan_timeout,scanner=scanner),selected_address)
        journal("ble_device_selected",**record)
        transport=await BleNusTransport.open(device,client_factory=client_factory)
        journal("ble_connected",service=NUS["service"],rx=NUS["rx"],tx=NUS["tx"],chunk_bytes=CHUNK,
                write_with_response=True,pair_requested=False,PAIR_characteristic_read=False)
        probe=usb.ReadOnlyProbe(transport,EXPECTED_VERSION,log=journal)
        def read_commands():
            results=[probe.identify()]
            results.extend(probe.query(name) for name in args.queries)
            return results
        results=await asyncio.to_thread(read_commands)
        summary={"read_only_session_completed":True,"target":"tank-mini","transport":"ble-nus",
            "device":record,"identity":probe.identity,"expected_image_sha256":profile["image_sha256"],
            "image_hash_attested_by_device":False,"commands":[r["command"] for r in results],
            "firmware_writes_tested":False,"audio_verified":False,"android_app_tested":False,
            "pair_requested":False,"PAIR_characteristic_read":False,"automatic_retry":False,"log":str(args.log)}
        journal("session_complete",**summary)
        return summary
    except BaseException as error:
        journal("session_failed",error_type=type(error).__name__,error=str(error),automatic_retry=False)
        raise
    finally:
        try:
            if transport is not None:
                await transport.aclose();journal("ble_disconnected")
        finally:journal.close()


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest="action")
    sub.add_parser("plan",help="local contract and Python environment only")
    scan=sub.add_parser("scan",help="explicit bounded BLE discovery; connects to nothing")
    scan.add_argument("--timeout",type=float,default=8.0)
    read=sub.add_parser("read",help="explicitly scan/select one address, connect and send read-only queries")
    read.add_argument("--address",required=True)
    read.add_argument("--firmware-manifest",type=Path,required=True)
    read.add_argument("--log",type=Path,required=True)
    read.add_argument("--scan-timeout",type=float,default=8.0)
    read.add_argument("--queries",nargs="*",choices=sorted(usb.QUERIES),default=list(usb.DEFAULT_QUERIES))
    args=parser.parse_args(argv)
    try:
        if args.action in (None,"plan"):
            result={"device_io":False,"enumerated":False,"protocol":source_contract(),"environment":environment_info(),
                    "write_commands_implemented":False,"android_app_tested":False}
        elif args.action=="scan":
            rows=asyncio.run(discover(timeout=args.timeout))
            result={"advertisements":[r[2] for r in rows],"connected":False,"pair_requested":False,"identity_established":False}
        else:result=asyncio.run(run_read(args))
        print(json.dumps(result,indent=2));return 0
    except Exception as error:
        print(json.dumps({"error_type":type(error).__name__,"error":str(error),"automatic_retry":False}),file=sys.stderr);return 1


if __name__=="__main__":raise SystemExit(main())
