"""BLE NUS adapter/identity tests with fake scanner/client; no Bluetooth access."""
import argparse
import asyncio
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import probe_mini_app_ble as ble
from tools import probe_mini_app as usb

ADDRESS="AA:BB:CC:DD:EE:FF"
PONG=b"PONG tankm_fw M5.71 rel ble Nov 12 2026 16:04:11\r\n"
MEM=b"MEM used=128 free=1024\n"
PLIST=b"PRE 0 1 -1 0 'Clean' t=p0 s=1 col=a1b2c3 amp=1\nPLIST end current=0\n"


class FakeServices:
    def __init__(self):
        self.service=SimpleNamespace(uuid=ble.NUS["service"],characteristics=[
            SimpleNamespace(uuid=ble.NUS["rx"],properties=["write"]),
            SimpleNamespace(uuid=ble.NUS["tx"],properties=["notify"]),
            SimpleNamespace(uuid=ble.NUS["pair"],properties=["read"])])
        self.asked=[]
    def get_service(self,uuid):self.asked.append(uuid);return self.service


class FakeClient:
    def __init__(self,device,**options):
        self.device=device;self.options=options;self.is_connected=False;self.services=FakeServices()
        self.connects=self.disconnects=0;self.notifications=[];self.writes=[];self.cb=None
        self.responses={b"PING\n":PONG,b"MEM\n":MEM,b"PLIST\n":PLIST}
        self.initial=[];self.fail_connect=False;self.fail_write=False;self.block_write=False

    async def connect(self):
        self.connects+=1
        if self.fail_connect:raise OSError("mock connection failure")
        self.is_connected=True

    async def disconnect(self):
        self.disconnects+=1;self.is_connected=False;self.options["disconnected_callback"](self)

    async def start_notify(self,char,cb):
        assert char.uuid==ble.NUS["tx"]
        self.notifications.append(char.uuid);self.cb=cb
        for raw in self.initial:self.cb(char,bytearray(raw))

    async def write_gatt_char(self,char,data,*,response):
        assert char.uuid==ble.NUS["rx"] and response is True and len(data)<=20
        self.writes.append((char.uuid,bytes(data),response))
        if self.fail_write:raise OSError("mock GATT write error")
        if self.block_write:await asyncio.sleep(60)
        chunks=self.responses.get(data,[])
        if isinstance(chunks,bytes):chunks=[chunks]
        for chunk in chunks:
            self.cb(None,bytearray(chunk));await asyncio.sleep(0)


class Factory:
    def __init__(self,configure=None):self.clients=[];self.configure=configure
    def __call__(self,device,**options):
        client=FakeClient(device,**options);self.clients.append(client)
        if self.configure:self.configure(client)
        return client


class FakeScanner:
    def __init__(self):
        self.calls=[];self.device=SimpleNamespace(address=ADDRESS,name="HyperRig MINI",details={})
        self.advertisement=SimpleNamespace(local_name="HyperRig MINI",service_uuids=[ble.NUS["service"]],rssi=-44)
    async def discover(self,**options):
        self.calls.append(options);return {ADDRESS:(self.device,self.advertisement)}


class BleAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def opened(self,configure=None):
        factory=Factory(configure);device=FakeScanner().device
        transport=await ble.BleNusTransport.open(device,client_factory=factory)
        self.addAsyncCleanup(transport.aclose)
        probe=usb.ReadOnlyProbe(transport,ble.EXPECTED_VERSION)
        return transport,factory.clients[0],probe

    async def test_bridge_uses_original_parser_notify_stream_and_acknowledged_writes(self):
        def configure(client):
            text="MODEL Caf\u00e9\r\n".encode()
            client.responses[b"MODEL\n"]=[text[i:i+1] for i in range(len(text))]
        transport,client,probe=await self.opened(configure)
        self.assertIsInstance(probe,usb.ReadOnlyProbe)
        self.assertFalse(client.options["pair"])
        self.assertEqual(client.options["winrt"],{"use_cached_services":False})
        self.assertEqual(client.notifications,[ble.NUS["tx"]])
        await asyncio.to_thread(probe.identify)
        model=await asyncio.to_thread(probe.query,"MODEL")
        presets=await asyncio.to_thread(probe.query,"PLIST")
        self.assertEqual(model["lines"],["MODEL Caf\u00e9"])
        self.assertTrue(presets["parsed"]["ok"])
        self.assertEqual(presets["parsed"]["presets"][0]["name"],"Clean")
        self.assertEqual([v[1] for v in client.writes],[b"PING\n",b"MODEL\n",b"PLIST\n"])
        self.assertTrue(all(v[2] for v in client.writes))
        self.assertNotIn(ble.NUS["pair"],client.services.asked+client.notifications)

    async def test_wrong_board_stock_or_version_stop_before_query(self):
        for reply in (PONG.replace(b"tankm",b"tankg"),PONG.replace(b"tankm",b"tankb"),
                      PONG.replace(b"5.71",b"5.70"),b"PONG TANK MINI_009 Nov 12 2026 16:04:11\n"):
            transport,client,probe=await self.opened(lambda c:c.responses.update({b"PING\n":reply}))
            with self.subTest(reply=reply),self.assertRaises(usb.AppProbeError):await asyncio.to_thread(probe.identify)
            with self.assertRaises(usb.AppProbeError):await asyncio.to_thread(probe.query,"MEM")
            self.assertEqual([r[1] for r in client.writes],[b"PING\n"])
            await transport.aclose()

    async def test_identity_required_and_direct_transport_rejects_all_mutating_lines(self):
        transport,client,probe=await self.opened()
        with self.assertRaises(usb.AppProbeError):await asyncio.to_thread(probe.query,"MEM")
        for command in (b"PSAVE 0 x\n",b"FXP 0 0 5\n",b"BLE key\n",b"AUTH ?\n",b"UBOOT\n",
                        b"MEM\nPSAVE 0 x\n",b"MEM\r\n",b"PING\0\n",b"PING",bytearray(b"PING\n")):
            with self.subTest(command=command),self.assertRaises(usb.AppProbeError):
                await asyncio.to_thread(transport.write,command)
        self.assertEqual(client.writes,[])

    async def test_stale_data_are_drained_and_notification_boundaries_are_not_lines(self):
        def configure(c):
            c.initial=[PONG.replace(b"tankm",b"tankg")]
            c.responses[b"PING\n"]=[PONG[:3],PONG[3:19],PONG[19:]]
            c.responses[b"MEM\n"]=[b"@L c=4\nMEM used=128 free=1024\nMODEL stale partial"]
            c.responses[b"MODEL\n"]=b"MODEL fresh\n"
        _tr,_client,probe=await self.opened(configure)
        await asyncio.to_thread(probe.identify)
        first=await asyncio.to_thread(probe.query,"MEM")
        second=await asyncio.to_thread(probe.query,"MODEL")
        self.assertEqual(first["asynchronous_lines"],["@L c=4"])
        self.assertEqual(second["lines"],["MODEL fresh"])

    async def test_pair_required_response_is_terminal_without_pairing(self):
        tr,client,probe=await self.opened(lambda c:c.responses.update({b"MEM\n":b"ERR MEM pair\n"}))
        await asyncio.to_thread(probe.identify)
        with self.assertRaisesRegex(usb.AppProbeError,"pair"):await asyncio.to_thread(probe.query,"MEM")
        self.assertTrue(probe.failed)
        self.assertEqual([r[1] for r in client.writes],[b"PING\n",b"MEM\n"])
        self.assertFalse(client.options["pair"])

    async def test_response_timeout_and_late_notifications_never_trigger_retry(self):
        tr,client,probe=await self.opened(lambda c:c.responses.update({b"PING\n":[]}))
        with self.assertRaisesRegex(usb.AppProbeError,"timeout"):await asyncio.to_thread(probe.identify)
        client.cb(None,PONG)
        with self.assertRaises(usb.AppProbeError):await asyncio.to_thread(probe.identify)
        self.assertEqual(len(client.writes),1)

    async def test_write_error_or_timeout_poison_transport_no_second_send(self):
        for mode in ("fail_write","block_write"):
            tr,client,probe=await self.opened(lambda c,m=mode:setattr(c,m,True))
            with self.subTest(mode=mode),patch.object(ble,"WRITE_TIMEOUT",.02),self.assertRaises(usb.AppProbeError):
                await asyncio.to_thread(probe.identify)
            self.assertTrue(probe.failed);self.assertIsNotNone(tr.error)
            with self.assertRaises(usb.AppProbeError):await asyncio.to_thread(tr.write,b"PING\n")
            self.assertEqual(len(client.writes),1)

    async def test_disconnect_poison_queue_before_any_later_query(self):
        tr,client,probe=await self.opened()
        await asyncio.to_thread(probe.identify)
        client.is_connected=False;client.options["disconnected_callback"](client)
        with self.assertRaises(usb.AppProbeError):await asyncio.to_thread(probe.query,"MEM")
        self.assertTrue(probe.failed);self.assertEqual(len(client.writes),1)

    async def test_notification_flood_is_bounded_and_terminal(self):
        for kind in ("bytes","count"):
            tr,_client,probe=await self.opened()
            if kind=="bytes":tr._notification(None,b"x"*(usb.MAX_RESPONSE+1))
            else:
                for _ in range(ble.MAX_NOTIFICATIONS+1):tr._notification(None,b"x")
            with self.subTest(kind=kind),self.assertRaises(usb.AppProbeError):await asyncio.to_thread(probe.identify)
            self.assertTrue(probe.failed)
            self.assertLessEqual(tr.notifications.qsize(),ble.MAX_NOTIFICATIONS)

    async def test_read_splits_chunks_without_losing_or_reordering_bytes(self):
        tr,_client,_probe=await self.opened()
        tr._notification(None,b"abcdef");tr._notification(None,b"gh")
        got=[await asyncio.to_thread(tr.read,2) for _ in range(4)]
        self.assertEqual(got,[b"ab",b"cd",b"ef",b"gh"])
        self.assertEqual(tr.pending_bytes,0)
        with self.assertRaises(usb.AppProbeError):tr.read(1)
        with self.assertRaises(usb.AppProbeError):tr.write(b"PING\n")

    async def test_missing_nus_rx_write_or_tx_notify_disconnects_without_ping(self):
        for kind in ("service","rx","tx","duplicate"):
            def configure(c):
                if kind=="service":c.services.service=None
                elif kind=="rx":c.services.service.characteristics[0].properties=["write-without-response"]
                elif kind=="tx":c.services.service.characteristics[1].properties=["read"]
                else:c.services.service.characteristics.append(c.services.service.characteristics[0])
            factory=Factory(configure)
            with self.subTest(kind=kind),self.assertRaises(usb.AppProbeError):
                await ble.BleNusTransport.open(FakeScanner().device,client_factory=factory)
            client=factory.clients[0]
            self.assertEqual(client.disconnects,1);self.assertEqual(client.writes,[])

    async def test_connect_failure_has_no_retry_or_pair_fallback(self):
        factory=Factory(lambda c:setattr(c,"fail_connect",True))
        with self.assertRaises(OSError):await ble.BleNusTransport.open(FakeScanner().device,client_factory=factory)
        self.assertEqual(len(factory.clients),1);self.assertEqual(factory.clients[0].connects,1)
        self.assertFalse(factory.clients[0].options["pair"])
        with self.assertRaises(usb.AppProbeError):await ble.BleNusTransport.open(ADDRESS,client_factory=factory)

    async def test_explicit_scan_metadata_does_not_assert_identity_or_connect(self):
        scanner=FakeScanner();rows=await ble.discover(timeout=1,scanner=scanner)
        self.assertEqual(scanner.calls,[{"timeout":1.0,"return_adv":True}])
        self.assertFalse(rows[0][2]["identity_established"])
        self.assertIs(ble.choose(rows,ADDRESS.lower())[0],scanner.device)
        for value in ("HyperRig MINI","",ADDRESS+" ","00:00:00:00:00:01"):
            with self.assertRaises(usb.AppProbeError):ble.choose(rows,value)
        with self.assertRaises(usb.AppProbeError):ble.choose(rows+rows,ADDRESS)
        for duration in (0,-1,31,True,float("nan")):
            with self.assertRaises(usb.AppProbeError):await ble.discover(timeout=duration,scanner=scanner)

    async def test_full_runner_uses_manifest_exact_identity_and_retains_protocol_log(self):
        scanner=FakeScanner();factory=Factory()
        with tempfile.TemporaryDirectory(dir=ROOT/"build",prefix="test-ble-probe-") as temporary:
            args=argparse.Namespace(address=ADDRESS,scan_timeout=1.0,
                firmware_manifest=ROOT/"build/hyperrig-mini-audio-v2/firmware-manifest.json",
                log=Path(temporary)/"new.jsonl",queries=["MEM","PLIST"])
            result=await ble.run_read(args,scanner=scanner,client_factory=factory)
            self.assertEqual(result["commands"],["PING","MEM","PLIST"])
            self.assertFalse(result["android_app_tested"] or result["firmware_writes_tested"])
            self.assertEqual(result["identity"]["firmware_version"],ble.EXPECTED_VERSION)
            self.assertEqual(factory.clients[0].disconnects,1)
            events=[json.loads(line) for line in args.log.read_text().splitlines()]
            self.assertTrue(any(v["event"]=="identity_accepted" for v in events))
            self.assertEqual(events[-1]["event"],"ble_disconnected")
            with self.assertRaises(FileExistsError):await ble.run_read(args,scanner=scanner,client_factory=factory)
            self.assertEqual(len(scanner.calls),1)

    async def test_manifest_or_command_rejected_before_any_scan(self):
        scanner=FakeScanner();factory=Factory()
        args=argparse.Namespace(address=ADDRESS,scan_timeout=1.0,firmware_manifest=Path("unused"),
                               log=Path("unused"),queries=["MEM"])
        for version,capability in (("tankg_fw M5.71 rel ble",True),("tankm_fw M5.70 rel ble",True),(ble.EXPECTED_VERSION,False)):
            with patch.object(usb,"load_profile",return_value={"firmware_version":version,"capabilities":{"read":capability}}):
                with self.assertRaises(usb.AppProbeError):await ble.run_read(args,scanner=scanner,client_factory=factory)
        with patch.object(usb,"load_profile",return_value={"firmware_version":ble.EXPECTED_VERSION,"capabilities":{"read":True}}):
            args.queries=["MEM","MEM"]
            with self.assertRaises(usb.AppProbeError):await ble.run_read(args,scanner=scanner,client_factory=factory)
        self.assertEqual(scanner.calls,[]);self.assertEqual(factory.clients,[])


class BleOfflineTests(unittest.TestCase):
    def test_import_and_default_never_import_bleak_scan_pair_or_connect(self):
        original=__import__
        def guard(name,*args,**kwargs):
            if name=="bleak" or name.startswith("bleak."):raise AssertionError("BLE imported during offline path")
            return original(name,*args,**kwargs)
        spec=importlib.util.spec_from_file_location("mini_ble_import_guard",ble.__file__)
        module=importlib.util.module_from_spec(spec)
        with patch("builtins.__import__",side_effect=guard):
            spec.loader.exec_module(module)
            with patch.object(module,"discover",side_effect=AssertionError("scan")),contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(module.main([]),0)
        value=json.loads(output.getvalue())
        self.assertFalse(value["device_io"] or value["enumerated"])
        self.assertFalse(value["protocol"]["PAIR_characteristic_read"] or value["protocol"]["pair_requested"])
        self.assertEqual(value["protocol"]["editor_sha256"],usb.SOURCE_SHA)


if __name__=="__main__":unittest.main()
