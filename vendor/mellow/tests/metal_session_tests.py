"""Real session lifecycle with an explicit fake OS boundary; no Metal runtime."""
import importlib.util,json,sys,threading,unittest
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'Userspace/metal_session.py'
s=importlib.util.spec_from_file_location('metal_session',p);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)
class Fake:
    native=True # Deliberate lie: injected backends MUST NOT produce native pass.
    def __init__(self):
        self.identity={'metal_registry_id':1,'pci_registry_id':2,'vendor-id':0x8086,
                       'MellowPhysicalVendorID':0x8086,'MellowPhysicalDeviceID':0x7d41,
                       'MellowPhysicalBDF':0x1000,'MellowPhysicalIdentitySource':'pci-config-before-spoof'}
        self.closed=0;self.released=[];self.compiled=0;self.program_released=0;self.fail=False
    def compile(self):self.compiled+=1;return 123
    def submit(self,program,values,nonce):
        if self.fail:raise m.DeviceError('Rejected before commit')
        return {'status':1,'data':m.expected(values,nonce)}
    def status(self,r):return r['status']
    def result(self,r):return r['data']
    def release(self,r):self.released.append(r)
    def release_program(self,p):self.program_released+=1
    def close(self):self.closed+=1
class Tests(unittest.TestCase):
    def setUp(self):self.b=Fake();self.s=m.MetalSession(1,_test_backend=self.b)
    def tearDown(self):
        for ticket in list(self.s.pending):self.s.pending[ticket]['receipt']['status']=5;self.s.poll(ticket)
        if not self.s.closed:self.s.close()
    def test_success_is_not_native(self):
        ticket=self.s.submit([1,2,3],99);self.s.pending[ticket]['receipt']['status']=4
        r=self.s.poll(ticket);self.assertTrue(r['output_matches']);self.assertFalse(r['target_probe_passed'])
        self.assertFalse(r['native_metal_executed']);self.assertEqual(len(self.b.released),1)
        self.assertFalse(r['native_metal_command_completed'])
    def test_requested_acceptance_transform(self):
        self.assertEqual(m.expected([1,2,3,4],0x12345678),[10,17,24,31])
        self.assertEqual(m.expected_witness(0x12345678),0x12345678^0x7d410003)
    def test_every_nonterminal_holds_resources(self):
        ticket=self.s.submit([7],8)
        for status in (0,1,2,3,6,0xffffffff):
            self.s.pending[ticket]['receipt']['status']=status
            self.assertFalse(self.s.poll(ticket)['terminal']);self.assertFalse(self.b.released)
            with self.assertRaises(m.Busy):self.s.close()
    def test_timeout_late_completion(self):
        ticket=self.s.submit([7],9);r=self.s.wait(ticket,0)
        self.assertTrue(r['resources_retained']);self.assertIn(self.s.id,m._live_sessions)
        self.s.pending[ticket]['receipt']['status']=4
        self.assertTrue(self.s.poll(ticket)['output_matches'])
        self.s.close();self.assertNotIn(self.s.id,m._live_sessions)
    def test_gpu_error_retires_without_output_read(self):
        ticket=self.s.submit([7],9);self.s.pending[ticket]['receipt']['status']=5
        self.b.result=lambda _:self.fail('Error command output must not be read')
        r=self.s.poll(ticket);self.assertFalse(r['output_matches']);self.assertIsNone(r['output'])
    def test_wrong_output_fails(self):
        ticket=self.s.submit([7],9);receipt=self.s.pending[ticket]['receipt'];receipt['status']=4;receipt['data']=[0]
        self.assertFalse(self.s.poll(ticket)['output_matches'])
    def test_identity_each_field(self):
        for key in self.b.identity:
            identity=dict(self.b.identity);identity[key]=None
            with self.subTest(key=key),self.assertRaises(m.Unavailable):m.validate_identity(identity)
    def test_foreign_ticket(self):
        ticket=self.s.submit([7],9)
        with self.assertRaises(ValueError):self.s.poll(m.Ticket(self.s.id+1,ticket.sequence))
    def test_completion_cannot_repeat(self):
        ticket=self.s.submit([7],9);self.s.pending[ticket]['receipt']['status']=4;self.s.poll(ticket)
        with self.assertRaises(ValueError):self.s.poll(ticket)
    def test_precommit_failure_leaves_no_job(self):
        self.b.fail=True
        with self.assertRaises(m.DeviceError):self.s.submit([7],9)
        self.assertFalse(self.s.pending)
    def test_input_bounds_and_snapshot(self):
        for values in ([],[-1],[2**32],[True],range(65537)):
            with self.subTest(values=str(values)[:40]),self.assertRaises(ValueError):self.s.submit(values,2)
        for nonce in (-1,2**32,True):
            with self.assertRaises(ValueError):self.s.submit([1],nonce)
        values=[1,2];t=self.s.submit(values,9);values[:]=[9,9]
        self.s.pending[t]['receipt']['status']=4;self.assertTrue(self.s.poll(t)['output_matches'])
    def test_outstanding_bound(self):
        for _ in range(16):self.s.submit([1],0)
        with self.assertRaises(m.Busy):self.s.submit([1],0)
        self.assertEqual(self.b.compiled,1)
    def test_thread_affinity(self):
        errors=[]
        def worker():
            try:self.s.submit([1],0)
            except m.DeviceError:errors.append(True)
        t=threading.Thread(target=worker);t.start();t.join();self.assertEqual(errors,[True])
    def test_platform_refusal(self):
        if sys.platform!='darwin':
            with self.assertRaises(m.Unavailable):m.NativeMetal(1)
    def test_invalid_timeout(self):
        ticket=self.s.submit([1],0)
        for value in (-1,float('nan'),float('inf'),61):
            with self.assertRaises(ValueError):self.s.wait(ticket,value)
    def test_native_submit_acceptance_receipt(self):
        native=object.__new__(m.NativeMetal);native.device=11;native.queue=12;native.selected_registry_id=77
        native.cls=lambda _:400
        buffers={};calls=[]
        def send(obj,selector,result=None,args=(),values=()):
            calls.append((selector,values))
            if selector=='newBufferWithLength:options:':
                key=100+len(buffers);buffers[key]=m.C.create_string_buffer(values[0]);return key
            if selector=='contents':return m.C.addressof(buffers[obj])
            if selector=='commandBuffer':return 200
            if selector=='retain':return obj
            if selector=='device':return 11
            if selector=='commandQueue':return 12
            if selector=='registryID':return 77
            if selector=='stringWithUTF8String:':return 401
            if selector=='computeCommandEncoder':return 300
            if selector=='maxTotalThreadsPerThreadgroup':return 64
            if selector=='commit':raise KeyboardInterrupt('Uncertain commit boundary')
            return None
        native.send=send
        receipt=native.submit(123,[1,2,3],55)
        self.assertIn('acceptance_error',receipt);self.assertEqual(receipt['buffers'],[100,101,102])
        self.assertNotIn('release',[x[0] for x in calls])
        self.assertEqual(list((m.C.c_uint32*3).from_buffer(buffers[100])),[1,2,3])
        self.assertEqual(m.C.c_uint32.from_buffer(buffers[102]).value,55^0xdeadbeef)
        self.assertEqual(receipt['expected_output_sha256'],m.words_sha256([10,17,24]))
        groups=next(args for selector,args in calls if selector=='dispatchThreadgroups:threadsPerThreadgroup:')
        self.assertEqual((groups[0].width,groups[1].width),(1,64))
    def test_native_precommit_failure_unwinds(self):
        native=object.__new__(m.NativeMetal);native.device=11;native.queue=12;releases=[];created=[]
        def send(obj,selector,result=None,args=(),values=()):
            if selector=='newBufferWithLength:options:':created.append(1);return 100 if len(created)==1 else 0
            if selector=='release':releases.append(obj)
        native.send=send
        with self.assertRaises(m.DeviceError):native.submit(123,[1],55)
        self.assertEqual(releases,[100])
    def test_public_completion_gate_needs_every_native_signal(self):
        evidence={'output_changed':True,'nonce_witness_matches':True,
                  'device_chain_matches':True,'gpu_timing_recorded':True}
        self.assertTrue(m.public_metal_completion_passed(native=True,status=4,output_matches=True,evidence=evidence))
        for key in evidence:
            broken=dict(evidence);broken[key]=False
            with self.subTest(key=key):
                self.assertFalse(m.public_metal_completion_passed(native=True,status=4,output_matches=True,evidence=broken))
        self.assertFalse(m.public_metal_completion_passed(native=False,status=4,output_matches=True,evidence=evidence))
        self.assertFalse(m.public_metal_completion_passed(native=True,status=5,output_matches=True,evidence=evidence))
        self.assertFalse(m.public_metal_completion_passed(native=True,status=4,output_matches=False,evidence=evidence))
    def test_cancel_is_explicitly_unavailable(self):
        ticket=self.s.submit([1],1)
        with self.assertRaises(m.Unavailable):self.s.cancel(ticket)
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    report={'passed':result.wasSuccessful(),'methods':result.testsRun,'native_metal_tested':False,
            'scope':'Actual Python session lifecycle; explicit fake Objective-C/Metal boundary'}
    (p.parents[1]/'validation/metal-session-tests.json').write_text(json.dumps(report,indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
