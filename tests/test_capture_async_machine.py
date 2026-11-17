"""Focused instruction and API checks for asynchronous capture."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from capture_async_machine import (CaptureAsyncProgram,REGIONS,DSP,RESULT,ENGINE,MMIO,
    DESCRIPTOR,READ,WRITE,SYNC,CALLBACK,signed)
from verify_capture_async import Platform,fixture,baseline,put,RAM,OUTPUT,INPUT,WORKER_CONTROL

class AsyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.program=CaptureAsyncProgram()
    def test_complete_return_boundaries(self):
        self.assertEqual(self.program.code[0x01C05116][0],'{pc, r15-r4} = [sp++]')
        self.assertEqual(self.program.code[0x01C04772][0],'{pc, r15-r4} = [sp++]')
        self.assertEqual(self.program.code[0x01C12606][0],'{pc, r12-r4} = [sp++]')
    def execute(self,operation,memory,args=(),**settings):
        platform=Platform(self.program,**settings)
        return self.program.execute(memory,operation,args,platform.call,platform.event),platform
    def test_bypass_retains_forward_overlap(self):
        memory=baseline();result,_=self.execute('run',memory,(INPUT,INPUT+4))
        first=memory[0][INPUT-RAM:INPUT-RAM+4]
        self.assertEqual(result['memory'][0][INPUT-RAM+4:INPUT-RAM+516],first*128)
    def test_submit_parallel_packet_stores_command_before_replacing_register(self):
        memory=fixture();put(memory[0],ENGINE-8-RAM,0xFFFFFFFF)
        result,p=self.execute('submit',memory,(123,456,12,789,9,64,14),software_dot=False)
        data=result['memory'][0]
        self.assertEqual(int.from_bytes(data[DESCRIPTOR-RAM:DESCRIPTOR-RAM+4],'little'),2657)
        self.assertEqual(int.from_bytes(data[ENGINE-8-RAM:ENGINE-4-RAM],'little'),0)
        self.assertEqual([x[0][:3] for x in p.events],[(SYNC,0,0),(WRITE,MMIO+8,0),(WRITE,MMIO+4,DESCRIPTOR),(WRITE,MMIO,329)])
    def test_submit_packs_native_low_width_fields(self):
        result,_=self.execute('submit',fixture(),(1,2,0xFFFFFFFF,3,0xFFFFFABC,0xFFFFFFED,0xFFFFFFFE),software_dot=False)
        data=result['memory'][0]
        self.assertEqual(int.from_bytes(data[DESCRIPTOR-RAM+16:DESCRIPTOR-RAM+20],'little'),0xFEFEDABC)
        self.assertEqual(int.from_bytes(data[DESCRIPTOR-RAM+20:DESCRIPTOR-RAM+24],'little'),0x4FFC00)
    def test_idle_wait_has_no_platform_events_or_writes(self):
        memory=fixture();result,p=self.execute('wait',memory)
        self.assertEqual(result['memory'],tuple(memory));self.assertEqual(result['value'],0);self.assertEqual(p.events,[])
    def test_wait_polls_then_acknowledges_and_clears_shared_busy(self):
        memory=fixture();put(memory[0],ENGINE-RAM,1)
        result,p=self.execute('wait',memory,engine_delay=2)
        self.assertEqual(p.counts[(READ,MMIO)],4)
        self.assertEqual(result['memory'][0][ENGINE-RAM:ENGINE-RAM+4],bytes(4))
        self.assertEqual(p.events[-2][0][:4],(WRITE,MMIO,192,0))
    def worker(self,memory,budget=1,handshake=1,**settings):
        p=Platform(self.program,auto_worker=False,**settings);native=self.program.machine(memory,p.call,p.event)
        result=p.run_worker(native,budget,handshake);return result,p,native
    def test_worker_stop_before_poll_clears_running_flag(self):
        memory=fixture();put(memory[1],8176,0)
        result,p,native=self.worker(memory)
        self.assertEqual(result,1);self.assertEqual(p.worker_state(),(3,0,0,WORKER_CONTROL))
        self.assertEqual(native.raw_read(DSP+28,4),0)
    def test_worker_stop_command_acknowledges_without_stopping_loop(self):
        memory=fixture();put(memory[0],DSP+8-RAM,255)
        result,p,native=self.worker(memory)
        self.assertEqual(result,0);self.assertEqual(native.raw_read(DSP+48,4),1);self.assertEqual(native.raw_read(DSP+8,4),0)
    def test_worker_unimplemented_command_executes_exact_rts(self):
        memory=fixture();put(memory[0],DSP+8-RAM,0xABCD01FE);put(memory[0],0x01C340CC+60-RAM,0xFFFFFFFF)
        result,p,native=self.worker(memory)
        self.assertEqual(result,0);self.assertEqual(native.raw_read(0x01C340CC+60,4),0)
        self.assertIn(REGIONS['command_noop'][0],p.worker.visited)
    def test_worker_handshake_observation_preserves_unreleased_lock(self):
        memory=fixture();put(memory[0],DSP+8-RAM,251);put(memory[0],DSP+4-RAM,1)
        result,p,native=self.worker(memory,handshake=2)
        self.assertEqual(result,2);self.assertEqual(native.raw_read(DSP,4),1)
        self.assertEqual(p.worker_state()[0],2);self.assertEqual(p.counts[(READ,DSP+4)],2)
        native.write(DSP+4,0,4);self.assertEqual(p.run_worker(native),0)
        self.assertEqual(native.raw_read(DSP,4),0);self.assertEqual(native.raw_read(DSP+8,4),0)
    def test_watchdog_runs_on_exact_1024th_idle_iteration(self):
        memory=fixture();put(memory[0],0x01C340C0-RAM,CALLBACK)
        result,p,native=self.worker(memory,budget=1024)
        self.assertEqual(result,0);self.assertEqual(len(p.calls),1);self.assertEqual(p.calls[0][:2],(CALLBACK,()))
        self.assertEqual(p.worker_state()[1:3],(1024,1024))
    def bias_block(self,bias,value):
        memory=fixture();put(memory[0],DSP+148-RAM,bias&0xFFFFFFFF);put(memory[0],DSP+152-RAM,bias>>32)
        for i in range(64):put(memory[0],RESULT-RAM+4*i,value)
        machine=self.program.machine(memory);machine.pc=0x01C04DDA;machine.regs.update(r13=DSP,r12=OUTPUT,r15=0)
        while machine.pc!=0x01C04EF2:
            machine.steps+=1;self.assertLess(machine.steps,5000);self.assertTrue(machine.step())
        return [machine.raw_read(OUTPUT+4*i,4) for i in range(64)]
    def test_bias_fast_path_saturates_both_signed_endpoints(self):
        self.assertEqual(self.bias_block(0x7FFFFFFF,1),[0x7FFFFFFF]*64)
        self.assertEqual(self.bias_block(0xFFFFFFFF80000000,0xFFFFFFFF),[0x80000000]*64)
    def test_bias_wide_path_clamps_large_offsets(self):
        self.assertEqual(self.bias_block(0x100000000,1),[0x7FFFFFFF]*64)
        self.assertEqual(self.bias_block(0xFFFFFFFF00000000,0xFFFFFFFF),[0x80000000]*64)
    def test_bias_wide_addition_wraps_before_saturation(self):
        self.assertEqual(self.bias_block(0x7FFFFFFFFFFFFFFF,1),[0x80000000]*64)
        self.assertEqual(self.bias_block(0x8000000000000000,0xFFFFFFFF),[0x7FFFFFFF]*64)
    def test_fast_poll_dispatch_matches_general_instruction_handlers(self):
        for release in (1,2,4,10):
            a,b=Platform(self.program,auto_worker=False,mutations=((READ,DSP+8,release,DSP+8,0,4),)),Platform(self.program,auto_worker=False,mutations=((READ,DSP+8,release,DSP+8,0,4),))
            memory=fixture();put(memory[0],DSP+8-RAM,252)
            fast,regular=self.program.machine(memory,a.call,a.event),self.program.machine(memory,b.call,b.event)
            for machine in (fast,regular):machine.pc=0x01C04D98;machine.regs.update(r13=DSP,r1=0,r14=3)
            while fast.pc not in (0x01C04DA4,0x01C04DA6):
                fast.step();regular.single_step()
                self.assertEqual((fast.pc,fast.regs,fast.flags,fast.carry),(regular.pc,regular.regs,regular.flags,regular.carry))
            self.assertEqual(a.events,b.events);self.assertEqual(fast.snapshot(),regular.snapshot())
if __name__=='__main__':unittest.main()
