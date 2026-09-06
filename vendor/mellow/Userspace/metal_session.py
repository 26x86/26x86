"""Native macOS Metal client connection; not a replacement Metal driver/plugin.

Uses Apple's actual Metal/Objective-C/IOKit APIs through their C ABI. An existing
MTLDevice must resolve to the expected PCI provider. No plugin is injected and
no guessed IOUserClient selector is sent. Native calls are NOT tested on Windows.
"""
import ctypes as C
import dataclasses
import hashlib
import itertools
import math
import platform
import secrets
import struct
import sys
import threading
import time

class Unavailable(RuntimeError): pass
class Busy(RuntimeError): pass
class DeviceError(RuntimeError): pass
class Size(C.Structure):
    _fields_=[('width',C.c_uint64),('height',C.c_uint64),('depth',C.c_uint64)]

SOURCE='''#include <metal_stdlib>
using namespace metal;
struct Params { uint count; uint nonce; };
kernel void mellow_runtime(device const uint *input [[buffer(0)]],
                           device uint *output [[buffer(1)]],
                           constant Params &p [[buffer(2)]],
                           device uint *nonceWitness [[buffer(3)]],
                           uint index [[thread_position_in_grid]]) {
    if (index < p.count) output[index] = input[index] * 7u + 3u;
    if (index == 0u) nonceWitness[0] = p.nonce ^ 0x7d410003u;
}
'''

def expected(values,nonce=None):
    """Acceptance transform A. ``nonce`` remains an API-compatible witness input."""
    return [(value*7+3)&0xffffffff for value in values]

def expected_witness(nonce):
    return nonce^0x7d410003

def words_sha256(values):
    return hashlib.sha256(struct.pack('<%dI'%len(values),*values)).hexdigest()

def public_metal_completion_passed(*,native,status,output_matches,evidence):
    """Bounded public-Metal gate; it does not prove Mellow's IRQ/fence backend."""
    return bool(native and status==4 and output_matches and
                evidence.get('output_changed') is True and
                evidence.get('nonce_witness_matches') is True and
                evidence.get('device_chain_matches') is True and
                evidence.get('gpu_timing_recorded') is True)

class NativeMetal:
    """Serialized, same-thread Objective-C ownership with a real autorelease pool."""
    native=True
    def __init__(self,registry_id):
        if sys.platform!='darwin': raise Unavailable('Native Metal requires macOS; no emulation fallback')
        if C.sizeof(C.c_void_p)!=8 or platform.machine()!='x86_64' or platform.release().split('.')[0]!='25':
            raise Unavailable('This connection profile requires x86_64 Tahoe/Darwin25')
        self.device=self.queue=self.pool=0
        self.objc=C.CDLL('/usr/lib/libobjc.A.dylib')
        self.foundation=C.CDLL('/System/Library/Frameworks/Foundation.framework/Foundation')
        self.metal=C.CDLL('/System/Library/Frameworks/Metal.framework/Metal')
        self.io=C.CDLL('/System/Library/Frameworks/IOKit.framework/IOKit')
        self.cf=C.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
        self.sel=self.function(self.objc,'sel_registerName',C.c_void_p,[C.c_char_p])
        self.cls=self.function(self.objc,'objc_getClass',C.c_void_p,[C.c_char_p])
        self.msg_address=C.cast(self.objc.objc_msgSend,C.c_void_p).value
        self.methods={}
        self.pool=self.send(self.send(self.cls(b'NSAutoreleasePool'),'alloc'),'init')
        if not self.pool: raise Unavailable('No autorelease pool')
        copy=self.function(self.metal,'MTLCopyAllDevices',C.c_void_p,[])
        array=copy()
        try:
            if not array: raise Unavailable('Metal returned no device array')
            count=self.send(array,'count',C.c_uint64)
            if count>64: raise DeviceError('Unexpected Metal device count')
            matches=[]
            for i in range(count):
                device=self.send(array,'objectAtIndex:',C.c_void_p,(C.c_uint64,),(i,))
                if self.send(device,'registryID',C.c_uint64)==registry_id: matches.append(device)
            if len(matches)!=1: raise Unavailable('No unique native MTLDevice for the supplied registry ID')
            self.identity=self.pci_identity(registry_id)
            validate_identity(self.identity)
            if self.identity.get('device-id') not in (0x7d41,0x9a49):
                raise Unavailable('Selected PCI provider is neither physical 7D41 nor the allowed 9A49 TGL spoof')
            name=self.text(self.send(matches[0],'name'))
            if not name or any(marker in name.casefold() for marker in ('software','swiftshader','llvmpipe','softpipe')):
                raise Unavailable('Selected MTLDevice has an empty or software-renderer name')
            self.selected_registry_id=registry_id
            self.device_profile={
                'name':name,
                'registry_id':self.send(matches[0],'registryID',C.c_uint64),
                'location':self.send(matches[0],'location',C.c_uint64),
                'location_number':self.send(matches[0],'locationNumber',C.c_uint64),
                'low_power':bool(self.send(matches[0],'isLowPower',C.c_bool)),
                'removable':bool(self.send(matches[0],'isRemovable',C.c_bool)),
                'headless':bool(self.send(matches[0],'isHeadless',C.c_bool)),
                'enumerated_device_count':count,
            }
            self.device=self.send(matches[0],'retain')
            self.queue=self.send(self.device,'newCommandQueue')
            if not self.queue: raise Unavailable('Metal command queue creation failed')
            queue_device=self.send(self.queue,'device')
            if self.send(queue_device,'registryID',C.c_uint64)!=registry_id:
                raise Unavailable('Metal command queue belongs to a different GPU')
        except Exception:
            self.close();raise
        finally:
            if array:self.send(array,'release',None)

    @staticmethod
    def function(lib,name,result,args):
        f=getattr(lib,name);f.restype=result;f.argtypes=args;return f
    def send(self,obj,selector,result=C.c_void_p,args=(),values=()):
        if not obj: raise DeviceError('Null Objective-C receiver')
        key=(result,args)
        if key not in self.methods:
            self.methods[key]=C.CFUNCTYPE(result,C.c_void_p,C.c_void_p,*args)(self.msg_address)
        return self.methods[key](obj,self.sel(selector.encode('ascii')),*values)
    def text(self,obj):
        if not obj:return ''
        ptr=self.send(obj,'UTF8String',C.c_char_p)
        return ptr.decode('utf-8',errors='replace') if ptr else ''
    def error(self,error):
        return self.text(self.send(error,'localizedDescription')) if error else 'Metal operation failed without NSError'
    def pci_identity(self,registry_id):
        match=self.function(self.io,'IORegistryEntryIDMatching',C.c_void_p,[C.c_uint64])
        find=self.function(self.io,'IOServiceGetMatchingService',C.c_uint32,[C.c_uint32,C.c_void_p])
        conforms=self.function(self.io,'IOObjectConformsTo',C.c_bool,[C.c_uint32,C.c_char_p])
        parent=self.function(self.io,'IORegistryEntryGetParentEntry',C.c_int32,[C.c_uint32,C.c_char_p,C.POINTER(C.c_uint32)])
        release=self.function(self.io,'IOObjectRelease',C.c_int32,[C.c_uint32])
        prop=self.function(self.io,'IORegistryEntryCreateCFProperty',C.c_void_p,[C.c_uint32,C.c_void_p,C.c_void_p,C.c_uint32])
        cf_release=self.function(self.cf,'CFRelease',None,[C.c_void_p])
        cf_type=self.function(self.cf,'CFGetTypeID',C.c_ulong,[C.c_void_p])
        data_type=self.function(self.cf,'CFDataGetTypeID',C.c_ulong,[])
        number_type=self.function(self.cf,'CFNumberGetTypeID',C.c_ulong,[])
        string_type=self.function(self.cf,'CFStringGetTypeID',C.c_ulong,[])
        data_len=self.function(self.cf,'CFDataGetLength',C.c_long,[C.c_void_p])
        data_ptr=self.function(self.cf,'CFDataGetBytePtr',C.c_void_p,[C.c_void_p])
        number=self.function(self.cf,'CFNumberGetValue',C.c_bool,[C.c_void_p,C.c_int,C.c_void_p])
        string=self.function(self.cf,'CFStringGetCString',C.c_bool,[C.c_void_p,C.c_void_p,C.c_long,C.c_uint32])
        registry=self.function(self.io,'IORegistryEntryGetRegistryEntryID',C.c_int32,[C.c_uint32,C.POINTER(C.c_uint64)])
        def read(entry,key):
            name=self.send(self.cls(b'NSString'),'stringWithUTF8String:',C.c_void_p,(C.c_char_p,),(key.encode(),))
            value=prop(entry,name,None,0)
            if not value:return None
            try:
                kind=cf_type(value)
                if kind==data_type() and data_len(value)==4:return int.from_bytes(C.string_at(data_ptr(value),4),'little')
                if kind==number_type():
                    result=C.c_int64()
                    return result.value if number(value,4,C.byref(result)) else None # kCFNumberSInt64Type
                if kind==string_type():
                    buffer=C.create_string_buffer(256)
                    return buffer.value.decode() if string(value,buffer,256,0x08000100) else None
                return None
            finally:cf_release(value)
        entry=find(0,match(registry_id))
        if not entry:raise Unavailable('Metal registry entry is missing')
        try:
            seen=set()
            for _ in range(32):
                rid=C.c_uint64()
                if registry(entry,C.byref(rid)) or rid.value in seen:raise DeviceError('Invalid registry ancestry')
                seen.add(rid.value)
                if conforms(entry,b'IOPCIDevice'):
                    return {'metal_registry_id':registry_id,'pci_registry_id':rid.value,
                            **{key:read(entry,key) for key in ('vendor-id','device-id','MellowPhysicalVendorID',
                            'MellowPhysicalDeviceID','MellowPhysicalBDF','MellowPhysicalIdentitySource')}}
                next_entry=C.c_uint32()
                if parent(entry,b'IOService',C.byref(next_entry)) or not next_entry.value:
                    raise Unavailable('No PCI ancestor')
                release(entry);entry=next_entry.value
            raise DeviceError('Registry ancestry limit')
        finally:release(entry)
    def compile(self):
        source=self.send(self.cls(b'NSString'),'stringWithUTF8String:',C.c_void_p,(C.c_char_p,),(SOURCE.encode(),))
        name=self.send(self.cls(b'NSString'),'stringWithUTF8String:',C.c_void_p,(C.c_char_p,),(b'mellow_runtime',))
        error=C.c_void_p();library=function=pipeline=0
        try:
            library=self.send(self.device,'newLibraryWithSource:options:error:',C.c_void_p,
                              (C.c_void_p,C.c_void_p,C.POINTER(C.c_void_p)),(source,None,C.byref(error)))
            if not library:raise DeviceError(self.error(error.value))
            function=self.send(library,'newFunctionWithName:',C.c_void_p,(C.c_void_p,),(name,))
            if not function:raise DeviceError('Compiled function is missing')
            pipeline=self.send(self.device,'newComputePipelineStateWithFunction:error:',C.c_void_p,
                               (C.c_void_p,C.POINTER(C.c_void_p)),(function,C.byref(error)))
            if not pipeline:raise DeviceError(self.error(error.value))
            return pipeline
        finally:
            if function:self.send(function,'release',None)
            if library:self.send(library,'release',None)
    def submit(self,pipeline,values,nonce):
        n=len(values);size=n*4;buffers=[];command=0
        try:
            for length in (size,size,4):
                buffer=self.send(self.device,'newBufferWithLength:options:',C.c_void_p,(C.c_uint64,C.c_uint64),(length,0))
                if not buffer:raise DeviceError('Shared buffer allocation failed')
                buffers.append(buffer)
            src=self.send(buffers[0],'contents');dst=self.send(buffers[1],'contents');witness=self.send(buffers[2],'contents')
            if not src or not dst or not witness:raise DeviceError('Shared buffer has no CPU mapping')
            inputs=(C.c_uint32*n)(*values);C.memmove(src,inputs,size)
            poison=secrets.token_bytes(size)
            C.memmove(dst,poison,size)
            witness_poison=nonce^0xdeadbeef
            C.cast(witness,C.POINTER(C.c_uint32))[0]=witness_poison
            command=self.send(self.send(self.queue,'commandBuffer'),'retain')
            command_device=self.send(command,'device')
            command_queue=self.send(command,'commandQueue')
            command_registry_id=self.send(command_device,'registryID',C.c_uint64)
            queue_registry_id=self.send(self.send(command_queue,'device'),'registryID',C.c_uint64)
            if command_registry_id!=self.selected_registry_id or queue_registry_id!=self.selected_registry_id:
                raise DeviceError('Command buffer ownership changed to a different GPU')
            challenge_id=secrets.token_hex(16)
            label=self.send(self.cls(b'NSString'),'stringWithUTF8String:',C.c_void_p,(C.c_char_p,),
                            (('Mellow7D41-'+challenge_id).encode(),))
            self.send(command,'setLabel:',None,(C.c_void_p,),(label,))
            encoder=self.send(command,'computeCommandEncoder')
            if not encoder:raise DeviceError('Compute encoder unavailable')
            self.send(encoder,'setComputePipelineState:',None,(C.c_void_p,),(pipeline,))
            self.send(encoder,'setBuffer:offset:atIndex:',None,(C.c_void_p,C.c_uint64,C.c_uint64),(buffers[0],0,0))
            self.send(encoder,'setBuffer:offset:atIndex:',None,(C.c_void_p,C.c_uint64,C.c_uint64),(buffers[1],0,1))
            params=(C.c_uint32*2)(n,nonce)
            self.send(encoder,'setBytes:length:atIndex:',None,(C.c_void_p,C.c_uint64,C.c_uint64),(C.cast(params,C.c_void_p),8,2))
            self.send(encoder,'setBuffer:offset:atIndex:',None,(C.c_void_p,C.c_uint64,C.c_uint64),(buffers[2],0,3))
            maximum=self.send(pipeline,'maxTotalThreadsPerThreadgroup',C.c_uint64)
            width=min(64,maximum)
            if not width:raise DeviceError('Invalid workgroup limit')
            self.send(encoder,'dispatchThreadgroups:threadsPerThreadgroup:',None,(Size,Size),(Size((n+width-1)//width,1,1),Size(width,1,1)))
            self.send(encoder,'endEncoding',None)
            # Returning this receipt is mandatory even when commit acceptance is
            # uncertain. Construct it BEFORE invoking the GPU-facing commit.
            receipt={'command':command,'buffers':buffers,'count':n,'committed':False,
                     'challenge_id':challenge_id,'nonce':nonce,
                     'input_sha256':words_sha256(values),
                     'initial_output_sha256':hashlib.sha256(poison).hexdigest(),
                     'expected_output_sha256':words_sha256(expected(values)),
                     'initial_witness':witness_poison,
                     'expected_witness':expected_witness(nonce),
                     'command_registry_id':command_registry_id,
                     'queue_registry_id':queue_registry_id}
        except Exception:
            if command:self.send(command,'release',None)
            for buffer in buffers:self.send(buffer,'release',None)
            raise
        try:
            self.send(command,'commit',None);receipt['committed']=True
        except BaseException:
            receipt['acceptance_error']='commit acceptance uncertain; query the retained command'
        return receipt
    def status(self,receipt):
        return self.send(receipt['command'],'status',C.c_uint64)
    def result(self,receipt):
        address=self.send(receipt['buffers'][1],'contents')
        if not address:raise DeviceError('Completed buffer mapping missing')
        return list((C.c_uint32*receipt['count']).from_address(address))
    def witness(self,receipt):
        address=self.send(receipt['buffers'][2],'contents')
        if not address:raise DeviceError('Completed nonce witness mapping missing')
        return C.cast(address,C.POINTER(C.c_uint32))[0]
    def completion_evidence(self,receipt,result,witness):
        command=receipt['command']
        command_device=self.send(command,'device')
        command_queue=self.send(command,'commandQueue')
        command_registry_id=self.send(command_device,'registryID',C.c_uint64)
        queue_registry_id=self.send(self.send(command_queue,'device'),'registryID',C.c_uint64)
        gpu_start=self.send(command,'GPUStartTime',C.c_double)
        gpu_end=self.send(command,'GPUEndTime',C.c_double)
        current_identity=self.pci_identity(self.selected_registry_id)
        validate_identity(current_identity)
        identity_keys=('pci_registry_id','vendor-id','device-id','MellowPhysicalVendorID',
                       'MellowPhysicalDeviceID','MellowPhysicalBDF','MellowPhysicalIdentitySource')
        identity_unchanged=all(current_identity.get(key)==self.identity.get(key) for key in identity_keys)
        output_digest=words_sha256(result)
        device_chain=(command_registry_id==self.selected_registry_id==queue_registry_id and identity_unchanged)
        timing=(math.isfinite(gpu_start) and math.isfinite(gpu_end) and gpu_start>0 and gpu_end>=gpu_start)
        return {
            'challenge_id':receipt['challenge_id'],'nonce':receipt['nonce'],
            'input_sha256':receipt['input_sha256'],
            'initial_output_sha256':receipt['initial_output_sha256'],
            'expected_output_sha256':receipt['expected_output_sha256'],
            'output_sha256':output_digest,
            'output_changed':output_digest!=receipt['initial_output_sha256'],
            'nonce_witness':witness,'expected_nonce_witness':receipt['expected_witness'],
            'nonce_witness_matches':witness==receipt['expected_witness'],
            'command_registry_id':command_registry_id,'queue_registry_id':queue_registry_id,
            'device_chain_matches':device_chain,'identity_unchanged':identity_unchanged,
            'gpu_start_time':gpu_start,'gpu_end_time':gpu_end,'gpu_timing_recorded':timing,
            'device':dict(self.device_profile),'pci':dict(current_identity),
            'hardware_irq_fence_verified':False,
            'cpu_fallback_excluded_by_hardware_evidence':False,
        }
    def release(self,receipt):
        self.send(receipt['command'],'release',None)
        for buffer in receipt['buffers']:self.send(buffer,'release',None)
    def release_program(self,program):self.send(program,'release',None)
    def close(self):
        if self.queue:self.send(self.queue,'release',None);self.queue=0
        if self.device:self.send(self.device,'release',None);self.device=0
        if self.pool:self.send(self.pool,'drain',None);self.pool=0

def validate_identity(identity):
    if not isinstance(identity,dict) or not identity.get('metal_registry_id') or not identity.get('pci_registry_id'):
        raise Unavailable('Missing Metal/PCI registry association')
    # PCI properties may already be spoofed. Require the driver's recorded
    # pre-spoof identity in addition to Intel ancestry. Not cryptographic proof.
    wanted={'vendor-id':0x8086,'MellowPhysicalVendorID':0x8086,'MellowPhysicalDeviceID':0x7d41,
            'MellowPhysicalBDF':0x1000,'MellowPhysicalIdentitySource':'pci-config-before-spoof'}
    if any(identity.get(k)!=v for k,v in wanted.items()):raise Unavailable('Unproven physical8086:7D41 at00:02.0')

@dataclasses.dataclass(frozen=True)
class Ticket:
    session:int
    sequence:int

# A timed-out or abandoned session remains reachable, so pending resource
# ownership is never discarded by Python GC. The process must remain alive.
_live_sessions={}
class MetalSession:
    def __init__(self,registry_id,*,_test_backend=None):
        if type(registry_id) is not int or not 0<registry_id<2**64:raise ValueError('registry_id')
        self.thread=threading.get_ident();self.id=secrets.randbits(128);self.sequence=0
        self.backend=_test_backend if _test_backend is not None else NativeMetal(registry_id)
        self.native=_test_backend is None and type(self.backend) is NativeMetal
        try:
            validate_identity(self.backend.identity)
            if self.backend.identity['metal_registry_id']!=registry_id:raise Unavailable('Selected registry differs')
        except Exception:
            self.backend.close();raise
        self.program=None;self.pending={};self.closed=False
        _live_sessions[self.id]=self
    def check(self):
        if self.closed:raise DeviceError('Session closed')
        if threading.get_ident()!=self.thread:raise DeviceError('Use owning thread/autorelease pool')
    def compile(self):
        self.check()
        if self.program is None:self.program=self.backend.compile()
    def submit(self,values,nonce):
        self.check()
        if len(self.pending)>=16:raise Busy('Outstanding command limit')
        values=tuple(itertools.islice(values,65537))
        if not 1<=len(values)<=65536 or any(type(v) is not int or not 0<=v<2**32 for v in values):raise ValueError('u32 input bounds')
        if type(nonce) is not int or not 0<=nonce<2**32:raise ValueError('u32 nonce')
        self.compile();self.sequence+=1
        ticket=Ticket(self.id,self.sequence)
        job={'receipt':None,'expected':expected(values,nonce),'timed_out':False}
        self.pending[ticket]=job
        try:
            # Backend may only throw before commit; uncertain acceptance returns
            # a retained receipt. NativeMetal enforces that boundary.
            job['receipt']=self.backend.submit(self.program,values,nonce)
        except BaseException:
            del self.pending[ticket];raise
        return ticket
    def poll(self,ticket):
        self.check()
        if ticket not in self.pending:raise ValueError('Unknown/foreign/completed ticket')
        job=self.pending[ticket];receipt=job['receipt'];status=self.backend.status(receipt)
        # Metal's terminal statuses are completed=4 and error=5. Scheduled=3,
        # elapsed time, CTB ACKs and object existence cannot retire a job.
        if status not in (4,5):return self._result(status=status,timed_out=job['timed_out'])
        result=None;valid=False;evidence={};witness=None
        try:
            if status==4:
                result=self.backend.result(receipt);valid=result==job['expected']
                if self.native:
                    witness=self.backend.witness(receipt)
                    evidence=self.backend.completion_evidence(receipt,result,witness)
        finally:
            self.backend.release(receipt);del self.pending[ticket]
        passed=public_metal_completion_passed(native=self.native,status=status,output_matches=valid,evidence=evidence)
        return self._result(terminal=True,status=status,output=result,output_matches=valid,
                            output_changed=evidence.get('output_changed',False),
                            nonce_witness_matches=evidence.get('nonce_witness_matches',False),
                            device_chain_matches=evidence.get('device_chain_matches',False),
                            gpu_timing_recorded=evidence.get('gpu_timing_recorded',False),
                            native_metal_command_completed=bool(self.native and status==4),
                            public_metal_target_compute_verified=passed,
                            native_metal_executed=passed,target_probe_passed=passed,evidence=evidence)
    @staticmethod
    def _result(**updates):
        result={'schema_version':2,'terminal':False,'status':None,'timed_out':False,
                'resources_retained':False,'output':None,'output_matches':False,
                'output_changed':False,'nonce_witness_matches':False,
                'device_chain_matches':False,'gpu_timing_recorded':False,
                'native_metal_command_completed':False,
                'public_metal_target_compute_verified':False,'native_metal_executed':False,
                'target_probe_passed':False,'hardware_irq_fence_verified':False,
                'cpu_fallback_excluded_by_hardware_evidence':False,'evidence':{}}
        result.update(updates)
        result['resources_retained']=not result['terminal']
        return result
    def wait(self,ticket,timeout=10):
        if not isinstance(timeout,(float,int)) or not 0<=timeout<=60:raise ValueError('timeout')
        start=time.monotonic()
        while True:
            result=self.poll(ticket)
            if result['terminal']:return result
            if time.monotonic()-start>=timeout:
                self.pending[ticket]['timed_out']=True
                return self._result(status=self.backend.status(self.pending[ticket]['receipt']),timed_out=True)
            time.sleep(0.002)
    def cancel(self,ticket):
        self.check()
        if ticket not in self.pending:raise ValueError('Unknown/foreign/completed ticket')
        raise Unavailable('Metal exposes no safe cancellation for a committed command buffer; retain and poll the ticket')
    def close(self):
        self.check()
        if self.pending:raise Busy('GPU commands remain unresolved; poll them before close')
        if self.program is not None:self.backend.release_program(self.program);self.program=None
        self.backend.close();self.closed=True;_live_sessions.pop(self.id,None)
