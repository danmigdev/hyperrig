"""Only fake CM/kernel APIs and temporary local logs; no device access."""
import contextlib
import ctypes as c
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import mini_usb_port_cycle as m


def put(pointer, value):
    pointer._obj.value = value


class FakeCM:
    def __init__(self):
        self.ids = {1: m.LEAF, 2: m.HUB}
        self.states = {1: (0x400, 43), 2: (8, 0)}
        self.port, self.property_type, self.property_size = 1, 7, 4
        self.interfaces = [r"\\?\usb#vid_1a40&pid_0101#exact-hub"]
        self.calls, self.locates, self.change_after_intent = [], 0, False

    def CM_Locate_DevNodeW(self, node, name, flags):
        self.calls.append(("locate", name, flags))
        self.locates += 1
        assert name == m.LEAF and flags == 0
        put(node, 1)
        return 0

    def CM_Get_Device_ID_Size(self, size, node, flags):
        put(size, len(self.ids[node]))
        return 0

    def CM_Get_Device_IDW(self, node, buffer, count, flags):
        buffer.value = self.ids[node]
        return 0

    def CM_Get_DevNode_Status(self, flags, problem, node, unused):
        put(flags, self.states[node][0]); put(problem, self.states[node][1])
        return 0

    def CM_Get_Parent(self, parent, leaf, flags):
        assert leaf == 1 and flags == 0
        put(parent, 2)
        return 0

    def CM_Get_DevNode_PropertyW(self, node, key, kind, data, size, flags):
        assert node == 1 and key._obj.pid == 30 and flags == 0
        assert bytes(key._obj.guid) == bytes(m.guid("a45c254e-df1c-4efd-8020-67d146a850e0"))
        put(kind, self.property_type); put(size, self.property_size)
        port = 2 if self.change_after_intent and self.locates == 3 else self.port
        data[:] = port.to_bytes(4, "little")
        return 0

    def CM_Get_Device_Interface_List_SizeW(self, count, guid, instance, flags):
        self.calls.append(("interface_size", instance, flags))
        assert instance == m.HUB and flags == 0 and bytes(guid._obj) == bytes(m.guid(m.HUB_GUID))
        put(count, len("\0".join(self.interfaces))+2)
        return 0

    def CM_Get_Device_Interface_ListW(self, guid, instance, buffer, count, flags):
        self.calls.append(("interfaces", instance, flags))
        assert instance == m.HUB and flags == 0
        value = "\0".join(self.interfaces)+"\0\0"
        assert len(value) == count
        for index, char in enumerate(value):
            buffer[index] = char
        return 0


class FakeKernel:
    def __init__(self, events, *, mode="success"):
        self.events, self.mode = events, mode
        self.calls, self.error, self.waits = [], 0, 0
        self.params = self.returned = None

    def CreateFileW(self, path, access, sharing, security, creation, flags, template):
        self.calls.append(("open", path, access, sharing, creation, flags))
        return c.c_void_p(-1).value if self.mode == "open_fail" else 101

    def CreateEventW(self, security, manual, signalled, name):
        self.calls.append(("event", manual, signalled, name))
        return 102

    def DeviceIoControl(self, handle, code, source, size, target, outsize, returned, overlapped):
        assert self.events[-1]["event"] == "cycle_intent"
        assert handle == 101 and code == 0x220444
        assert size == outsize == 8 and source._obj is target._obj
        assert source._obj.ConnectionIndex == 1 and source._obj.StatusReturned == 0xFFFFFFFF
        assert overlapped._obj.hEvent == 102
        self.calls.append(("cycle", bytes(source._obj).hex()))
        self.params, self.returned = source._obj, returned
        if self.mode in ("pending", "cancelled", "uncancellable"):
            self.error = 997
            return 0
        if self.mode == "io_fail":
            self.error = 31
            return 0
        self.params.StatusReturned = 0 if self.mode != "usbd_fail" else 0xC0000001
        put(returned, 0 if self.mode == "no_output" else 8)
        return 1

    def GetOverlappedResultEx(self, handle, overlapped, returned, timeout, alertable):
        self.calls.append(("wait", timeout))
        self.waits += 1
        assert alertable == 0
        if self.mode == "pending":
            self.params.StatusReturned = 0; put(returned, 8)
            return 1
        self.error = 995 if self.mode == "cancelled" and self.waits == 2 else 258
        return 0

    def CancelIoEx(self, handle, overlapped):
        self.calls.append(("cancel", handle))
        return 1

    def CloseHandle(self, handle):
        self.calls.append(("close", handle))
        return 1

    def GetLastError(self):
        return self.error


class PortCycleTests(unittest.TestCase):
    def setUp(self):
        m._attempted = False
        m._pending.clear()

    def run_fake(self, *, mode="success", api=None, logger=None):
        events = []
        api = api or FakeCM()
        kernel = FakeKernel(events, mode=mode)
        result = m.cycle_once(logger or events.append, api=api, kernel=kernel)
        return result, events, api, kernel

    def test_offline_defaults_and_check_only_never_resolve_native_apis(self):
        for args in ([], ["--check-only"]):
            with patch.object(m, "cfgmgr32", side_effect=AssertionError("native")), \
                 patch.object(m, "kernel32", side_effect=AssertionError("native")), \
                 contextlib.redirect_stdout(io.StringIO()) as stdout:
                self.assertEqual(m.main(args), 0)
                output = json.loads(stdout.getvalue())
                self.assertFalse(output["device_access"])
                self.assertEqual(output["ioctl"], 0x220444)
                self.assertEqual(output["params_bytes"], 8)

    def test_exact_live_target_and_one_durable_ordered_cycle(self):
        result, events, api, kernel = self.run_fake()
        self.assertEqual(api.locates, 3)
        self.assertEqual([x[0] for x in kernel.calls], ["open", "event", "cycle", "close", "close"])
        self.assertEqual(kernel.calls[0][2:], (0x40000000, 3, 3, 0x40000000))
        self.assertTrue(result["cycle_submitted"] and result["ioctl_success"] and result["handles_closed"])
        self.assertEqual(result["status_returned"], 0)
        self.assertFalse(result["reenumeration_verified"] or result["ROM_verified"])
        self.assertEqual(events[-1]["event"], "finished")
        with self.assertRaisesRegex(ValueError, "consumed"):
            m.cycle_once(events.append, api=api, kernel=kernel)

    def test_wrong_leaf_parent_problem_port_or_interface_stops_before_open(self):
        for field, value in (("leaf", "USB\\OTHER"), ("hub", "USB\\OTHER"),
                             ("problem", 0), ("port", 2), ("hub_problem", 43),
                             ("interfaces", []), ("interfaces", [r"\\?\one", r"\\?\two"]),
                             ("property_type", 18), ("property_size", 2)):
            with self.subTest(field=field, value=value):
                api = FakeCM()
                if field == "leaf": api.ids[1] = value
                elif field == "hub": api.ids[2] = value
                elif field == "problem": api.states[1] = (0x400, value)
                elif field == "hub_problem": api.states[2] = (8, value)
                else: setattr(api, field, value)
                result, _, _, kernel = self.run_fake(api=api)
                self.assertFalse(result["cycle_submitted"])
                self.assertIsNotNone(result["error"])
                self.assertEqual(kernel.calls, [])

    def test_live_change_after_intent_closes_without_submitting(self):
        api = FakeCM(); api.change_after_intent = True
        result, events, _, kernel = self.run_fake(api=api)
        self.assertIn("cycle_intent", [e["event"] for e in events])
        self.assertFalse(result["cycle_submitted"])
        self.assertEqual([x[0] for x in kernel.calls], ["open", "event", "close", "close"])

    def test_journal_failure_before_ioctl_prevents_mutation(self):
        events = []
        def log(event):
            events.append(event)
            if event["event"] == "cycle_intent": raise OSError("fsync failed")
        result, _, _, kernel = self.run_fake(logger=log)
        self.assertFalse(result["cycle_submitted"])
        self.assertFalse(any(call[0] == "cycle" for call in kernel.calls))
        self.assertTrue(result["handles_closed"])

    def test_attempt_consumed_by_another_caller_during_preflight_does_not_submit(self):
        def log(event):
            if event["event"] == "cycle_intent":
                m._attempted = True
        result, _, _, kernel = self.run_fake(logger=log)
        self.assertFalse(result["cycle_submitted"])
        self.assertIn("another caller", result["error"])
        self.assertTrue(result["handles_closed"])
        self.assertFalse(any(call[0] == "cycle" for call in kernel.calls))

    def test_open_failure_has_no_cycle(self):
        result, _, _, kernel = self.run_fake(mode="open_fail")
        self.assertFalse(result["cycle_submitted"])
        self.assertEqual([x[0] for x in kernel.calls], ["open"])

    def test_device_error_is_unknown_and_never_retried(self):
        result, _, _, kernel = self.run_fake(mode="io_fail")
        self.assertEqual(result["win32_error"], 31)
        self.assertTrue(result["operation_outcome_unknown"])
        self.assertTrue(result["handles_closed"])
        self.assertEqual(sum(x[0] == "cycle" for x in kernel.calls), 1)

    def test_pending_success_waits_once_and_closes(self):
        result, _, _, kernel = self.run_fake(mode="pending")
        self.assertTrue(result["ioctl_success"])
        self.assertEqual([x for x in kernel.calls if x[0] == "wait"], [("wait", 20000)])
        self.assertFalse(any(x[0] == "cancel" for x in kernel.calls))

    def test_timeout_cancellation_is_not_a_second_cycle(self):
        result, _, _, kernel = self.run_fake(mode="cancelled")
        self.assertEqual(result["win32_error"], 995)
        self.assertTrue(result["operation_outcome_unknown"] and result["handles_closed"])
        self.assertEqual([x for x in kernel.calls if x[0] == "wait"], [("wait", 20000), ("wait", 3000)])
        self.assertEqual(sum(x[0] == "cycle" for x in kernel.calls), 1)
        self.assertEqual(sum(x[0] == "cancel" for x in kernel.calls), 1)

    def test_uncancellable_pending_io_retains_buffers_until_process_exit(self):
        result, _, _, kernel = self.run_fake(mode="uncancellable")
        self.assertFalse(result["handles_closed"])
        self.assertTrue(result["pending_io_buffers_retained_until_process_exit"])
        self.assertEqual(len(m._pending), 1)
        self.assertFalse(any(x[0] == "close" for x in kernel.calls))

    def test_usbd_status_is_separate_and_missing_output_is_not_synthetic_zero(self):
        result, _, _, _ = self.run_fake(mode="usbd_fail")
        self.assertTrue(result["ioctl_success"])
        self.assertEqual(result["status_returned"], 0xC0000001)
        m._attempted = False
        result, _, _, _ = self.run_fake(mode="no_output")
        self.assertIsNone(result["status_returned"])
        self.assertFalse(result["status_returned_observed"])

    def test_cli_log_is_exclusive_and_fsynced_before_execution_event(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"once.jsonl"
            def fake_cycle(log):
                log({"event": "cycle_intent"})
                self.assertEqual(json.loads(path.read_text()), {"event": "cycle_intent"})
                return {"ioctl_success": True, "handles_closed": True, "error": None, "status_returned": 0}
            with patch.object(m, "cycle_once", side_effect=fake_cycle) as cycle, \
                 patch.object(m.os, "fsync", wraps=m.os.fsync) as sync, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(m.main(["--execute", "--log", str(path)]), 0)
                self.assertEqual(sync.call_count, 1)
                with self.assertRaises(FileExistsError): m.main(["--execute", "--log", str(path)])
                self.assertEqual(cycle.call_count, 1)


if __name__ == "__main__":
    unittest.main()
