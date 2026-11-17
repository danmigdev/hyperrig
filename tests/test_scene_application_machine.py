"""Focused original-instruction and scene-contract checks, separate from C comparisons."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from scene_application_machine import SceneApplicationProgram,SceneApplicationMachine,STATE,GLOBAL,CALLBACKS,EFFECTS,STACK
from verify_scene_application import initial,put,Script

class SceneInstructions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.program=SceneApplicationProgram()
    def machine(self,pc,**registers):
        m=SceneApplicationMachine(self.program,initial(),'inner',(0,),Script())
        m.pc=pc;m.regs.update(registers);return m
    def test_masked_predicate_uses_low_byte(self):
        for value,taken in ((0,True),(256,True),(1,False),(0xffffffff,False)):
            m=self.machine(0x02009e6c,r5=value);m.step()
            self.assertEqual(m.pc,0x02009e70 if taken else 0x02009e74)
    def test_register_mask_branch(self):
        for a,b,taken in ((1,1,True),(1,2,False),(0x80000000,0x80000000,True)):
            m=self.machine(0x02009ee4,r5=a,r0=b);n=self.program.code[m.pc][1];m.step()
            self.assertEqual(m.pc,0x02009ee4+n+(168 if taken else 0))
    def test_slot_mask_uses_native_word(self):
        for shift in (0,1,15,31,32,63):
            m=self.machine(0x0200a01e,r0=0xffffffff,r4=shift);m.step()
            self.assertEqual(m.regs['r0'],1<<(shift&31))
    def test_unsigned_minimum(self):
        for value in (0,0x7fffff,0x80000000,0xffffffff):
            m=self.machine(0x0200a24a,r0=value,r1=0x7fffff);m.step()
            self.assertEqual(m.regs['r1'],min(value,0x7fffff))
    def test_unsigned_divide_zero(self):
        m=self.machine(0x0200a240,r2=0xffffffff,r0=0);m.step();self.assertEqual(m.regs['r0'],0)
    def test_elapsed_subtraction_wraps(self):
        m=self.machine(0x0200a234,r0=0,r4=1);m.step();self.assertEqual(m.regs['r2'],0xffffffff)
    def test_parallel_store_reads_prior_register(self):
        m=self.machine(0x02009e22,r6=123,r0=2,r1=0xabcdef01)
        m.regs['sp']=STACK-128;m.step()
        self.assertEqual(m.regs['r6'],2);self.assertEqual(m.read(STACK-96,4),0xabcdef01)
    def test_parallel_second_half_is_not_entry(self):
        m=self.machine(0x02009e24)
        with self.assertRaises(ValueError):m.step()
    def test_uninitialized_stack_read_fails(self):
        m=self.machine(0x02009e14);m.regs['sp']=STACK-16
        with self.assertRaises(ValueError):m.read(STACK-8,4)
    def test_scene_view_exceeds_old_application_state(self):
        memory=initial();memory[1]=memory[1][:4100]
        with self.assertRaises(ValueError):self.program.execute(memory,'inner',0,boundary=Script())
    def test_invalid_direct_scene_rejected(self):
        with self.assertRaises(ValueError):self.program.execute(initial(),'inner',4,boundary=Script())
    def test_invalid_selection_is_native_noop(self):
        memory=initial();r=self.program.execute(memory,'select',0xffffffff,boundary=Script())
        self.assertEqual(r['memory'],tuple(bytes(x) for x in memory));self.assertFalse(r['calls'])
    def test_report_rate_and_low_byte(self):
        r=self.program.execute(initial(),'report',0x1234abcd,0,boundary=Script())
        self.assertEqual(r['result'],(125<<8)|0xcd)
    def test_report_zero_rate(self):
        memory=initial();put(memory[0],44,0)
        r=self.program.execute(memory,'report',0x1234abcd,0,boundary=Script())
        self.assertEqual(r['result'],0xcd)
    def test_failed_application_still_publishes_scene(self):
        memory=initial([37]);memory[1][11958:11972]=bytes(14)
        r=self.program.execute(memory,'inner',0,boundary=Script({0x0202FD18:1}))
        self.assertEqual(r['result'],1);self.assertEqual(int.from_bytes(r['memory'][0][88:92],'little'),0)
        self.assertEqual(r['memory'][5][761],0)
    def test_wrapper_selector_receives_first_failure_count(self):
        memory=initial([37]);memory[1][11958:11972]=bytes(14)
        r=self.program.execute(memory,'apply',0,boundary=Script({0x0202FD18:1,0x02028EB2:1}))
        selector=[c for c in r['calls'] if c[0]==0x02028EB2]
        self.assertEqual(selector[0][1],(1,0,0,0,0));self.assertEqual(r['result'],1)
        self.assertEqual(sum(c[0]==0x02028F96 for c in r['calls']),1)
        tags=[c[1][1]>>16 for c in r['calls'] if c[0]==0x02002D10]
        self.assertEqual(tags,[3,5])
    def test_type7_final_scan_includes_unselected_slot(self):
        memory=initial([5,7]);put(memory[1],11938,1,2)
        changed=lambda a,m:m.write(EFFECTS+480+74,-32768,2)
        r=self.program.execute(memory,'inner',0,boundary=Script(mutations={(0x02008CA2,0):[changed]}))
        self.assertIn((0x020091D6,(1,0,0,0,0)),[c[:2] for c in r['calls']])
    def test_pending_counter_cleared_without_available_scene(self):
        memory=initial();put(memory[1],956,17)
        for i in range(4):memory[1][11936+260*i]=0
        r=self.program.execute(memory,'flush',boundary=Script())
        self.assertEqual(r['memory'][1][956:960],bytes(4));self.assertFalse(r['calls'])
    def test_probe_passes_signed_desired_parameter(self):
        for desired in (-32768,-2345,-1,0,32767):
            memory=initial([37]);put(memory[1],11958,desired,2)
            r=self.program.execute(memory,'inner',0,boundary=Script())
            probe=next(c for c in r['calls'] if c[0]==0x0202FD18)
            self.assertEqual(probe[1],(0,0,desired&0xffffffff,0,0))
    def test_enable_services_receive_raw_desired_byte(self):
        for mode,target in ((0,0x02030530),(2,0x020305F8)):
            for desired in (0,1,2,255):
                memory=initial([37],mode=mode);memory[2][1]=int(not desired);memory[1][11942]=desired
                r=self.program.execute(memory,'inner',0,boundary=Script())
                calls=[c for c in r['calls'] if c[0]==target]
                self.assertTrue(calls)
                for call in calls:self.assertEqual(call[1],(0,desired,0,0,0))
    def test_parameter_is_reread_after_probe(self):
        for mode,target in ((0,0x0202F07E),(2,0x0202FBA6)):
            memory=initial([37],mode=mode);put(memory[1],11958,-32768,2)
            changed=lambda a,m:m.write(STATE+11958,1234,2)
            r=self.program.execute(memory,'inner',0,boundary=Script(mutations={(0x0202FD18,0):[changed]}))
            probe=next(c for c in r['calls'] if c[0]==0x0202FD18)
            update=next(c for c in r['calls'] if c[0]==target and c[1][1]==0)
            self.assertEqual(probe[1][2],0xffff8000);self.assertEqual(update[1][2],1234)

if __name__=='__main__':unittest.main()
