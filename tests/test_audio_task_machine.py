"""Original audio-task observation boundaries and shared-memory regressions."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from audio_task_machine import AudioTaskProgram,STATE,CONTROL,RAM,RECORD,PLAY,STACK,REGIONS
from verify_audio_task import baseline,capture_fixture,put,word,Script


class AudioTaskTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.program=AudioTaskProgram()

    def machine(self,memory=None,script=None):
        return self.program.machine(memory or baseline(),script or Script())

    def test_complete_nonreturning_task_body(self):
        self.assertEqual(sum(REGIONS["task"][0]<=pc<REGIONS["task"][1] for pc in self.program.code),1264)
        self.assertEqual(len(REGIONS),6)

    def test_entry_stops_after_completed_wait(self):
        m=self.machine();r=m.resume();self.assertEqual(r["task"],(1,1,0,0))
        self.assertEqual(r["pc"],0x01C02D7A);self.assertEqual(m.value("sp"),STACK-104)
        self.assertEqual(r["calls"][0][:2],(0x02040D34,(STATE+3508,0)))

    def test_wait_preserves_unrelated_memory(self):
        memory=baseline();r=self.machine(memory).resume()
        expected=bytearray(memory[0]);put(expected,STATE-RAM+528,6)
        self.assertEqual(r["memory"],(bytes(expected),*map(bytes,memory[1:])))

    def test_frame_boundary_is_queue_poll(self):
        m=self.machine();m.resume();r=m.resume()
        self.assertEqual((r["reason"],r["pc"],r["task"]),(1,0x01C02D42,(2,1,1,0)))
        self.assertEqual(word(r["memory"][0],STATE-RAM+384),1)

    def test_queue_exhaustion_returns_to_wait(self):
        m=self.machine();m.resume();m.resume();r=m.resume()
        self.assertEqual((r["reason"],r["task"]),(0,(1,2,1,0)))

    def test_fatal_wait_path_is_not_a_native_return(self):
        memory=baseline();put(memory[0],STATE-RAM+204,1);put(memory[0],CONTROL-RAM+24,402)
        m=self.machine(memory);m.resume();r=m.resume()
        self.assertEqual(r["task"],(3,1,0,0x01C02DA2));self.assertEqual(m.value("sp"),STACK-104)
        self.assertEqual(r["calls"][-1][:2],(0x0201AAEA,(4010,0)))

    def test_watchdog_notification_threshold(self):
        for tick,present in ((201,False),(202,True)):
            memory=baseline();put(memory[0],STATE-RAM+204,1);put(memory[0],CONTROL-RAM+24,tick)
            put(memory[0],STATE-RAM+380,0);m=self.machine(memory);m.resume();r=m.resume()
            self.assertEqual(any(target==0x02002D10 for target,_,_ in r["calls"]),present)

    def test_parallel_deadline_saves_pre_add_value(self):
        m=self.machine();m.regs.update(sp=STACK-104,r0=1000,r2=23);m.pc=0x01C021B6
        m.step();self.assertEqual(m.value("r0"),1023);self.assertEqual(m.read(STACK-80,4),1000)

    def test_parallel_record_counter_uses_old_base(self):
        m=self.machine();m.regs.update(r8=STATE,r2=STATE+988,r3=17);m.pc=0x01C02054
        m.step();self.assertEqual(m.read(STATE+992,4),17);self.assertEqual(m.value("r2"),STATE+4412)

    def test_statistics_store_is_then_else(self):
        self.assertEqual(self.program.code[0x01C02844][2:],(1,1))
        for capture,address in ((0,CONTROL+56),(1,STATE+512)):
            m=self.machine();m.regs.update(r0=900,r1=capture,r2=400,r8=STATE,r15=CONTROL);m.pc=0x01C02844
            m.step();m.step()
            self.assertEqual(m.read(address,4),900 if capture==0 else 400)

    def test_fir_wraps_pair_before_signed_mac(self):
        memory=baseline();ring=STATE+3312
        for i in range(16):put(memory[0],ring-RAM+4*i,0x7FFFFFFF)
        for i in range(4):put(memory[1],i*2,32767,2)
        put(memory[1],8,0,2)
        r=self.program.execute_helper(memory,"fir",(RECORD,9,ring,0,15))
        self.assertEqual(r["value"],0xFFFFFFF8)

    def test_tap_forward_overlap_retains_native_order(self):
        memory=baseline();source=0x01C234A8
        for offset,value in ((25,1),(456,source+4),(460,0),(464,128)):put(memory[0],STATE-RAM+offset,value,1 if offset==25 else 4)
        first=memory[0][source-RAM:source-RAM+4]
        r=self.program.execute_helper(memory,"tap",(1,source))
        self.assertEqual(r["memory"][0][source-RAM+4:source-RAM+516],first*128)

    def test_effect_scan_calls_first_eligible_slot(self):
        memory=baseline();slot=0x01C2C220-RAM+15*480
        memory[0][slot]=28;memory[0][slot+2]=1;memory[0][slot+9]=1
        r=self.program.execute_helper(memory,"effect_scan",(0x01C234A8,),Script())
        self.assertEqual(r["calls"][0][:2],(0x01C19EFA,(0x01C234A8,0x01C32F50,8)))
        self.assertEqual(r["memory"][0][0x01C32DB0-RAM],1)

    def test_warmup_replication_and_small_head_extent(self):
        memory=capture_fixture(layers=1,taps=1)
        r=self.program.execute_helper(memory,"warmup",(),Script())
        ring=r["memory"][0][0x01C2A8E0-RAM:0x01C2A8E0-RAM+3048]
        self.assertEqual(ring,ring[:12]*254)
        self.assertTrue(any(target==0x01C14282 for target,_ in r["real_calls"]))

    def test_warmup_busy_limit_tests_before_increment(self):
        m=self.machine();m.regs.update(r0=4000000,r2=3999999,r7=0x01C2BFF0);m.pc=0x01C04C54
        m.write(0x01C2BFF8,1,4);m.step();m.step()
        self.assertEqual(m.pc,0x01C04C5E);self.assertEqual(m.value("r0"),4000000)

    def test_stereo_activation_resets_twice_around_clone(self):
        memory=baseline();memory[0][0x01C3448C-RAM]=memory[0][0x01C3448D-RAM]=1
        m=self.machine(memory);m.resume();r=m.resume()
        sequence=[target for target,_ in r["real_calls"] if target in (0x01C11B00,0x01C11C66,0x01C11BFA,0x01C11C7E)]
        self.assertEqual(sequence,[0x01C11B00,0x01C11C66,0x01C11B00,0x01C11BFA,0x01C11C7E])

    def test_diagnostic_two_sample_fade_reaches_zero(self):
        memory=baseline();s=STATE-RAM
        memory[0][s+18]=2
        for offset,value in ((312,PLAY),(316,2),(320,1),(324,2)):put(memory[0],s+offset,value)
        m=self.machine(memory);m.resume();r=m.resume()
        self.assertEqual((r["memory"][0][s+18],word(r["memory"][0],s+324)),(0,0))

    def test_unknown_helper_and_invalid_budgets_rejected(self):
        with self.assertRaises(ValueError):self.program.execute_helper(baseline(),"task")
        with self.assertRaises(ValueError):self.machine().resume(0,1)
        with self.assertRaises(ValueError):self.machine().resume(1,0)


if __name__=="__main__":unittest.main()
