// Public IOKit diagnostic client, 2026. See repository LICENSE and NOTICE.
// Build on macOS: clang -std=c11 -Wall -Wextra -Werror Userspace/tahoe_diag_client.c
//     -framework IOKit -framework CoreFoundation -o tahoe-diag-client
#include "../Mellow/TahoeDiagnosticABI.h"
#include <IOKit/IOKitLib.h>
#include <mach/mach.h>
#include <inttypes.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

static int invoke(io_connect_t connection, uint32_t selector, uint64_t handle, uint64_t bytes,
                  MellowDiagReply *reply) {
    MellowDiagRequest request = {MELLOW_DIAG_ABI_VERSION,sizeof(request),handle,bytes,0};
    size_t size = sizeof(*reply);
    memset(reply,0,sizeof(*reply));
    kern_return_t result = IOConnectCallStructMethod(connection,selector,&request,sizeof(request),reply,&size);
    if (result != KERN_SUCCESS) { fprintf(stderr,"IOConnectCallStructMethod selector=%u failed 0x%x\n",selector,result);return 0; }
    if (size != sizeof(*reply) || reply->size != sizeof(*reply) || reply->version != MELLOW_DIAG_ABI_VERSION ||
        reply->reserved || reply->gpuSubmissionSupported || reply->metalSupported ||
        reply->vendor != 0x8086 || reply->device != 0x7d41 || reply->gmdArchitecture != 12 || reply->gmdRelease != 70) {
        fprintf(stderr,"Diagnostic response has an invalid ABI, identity or unsupported GPU claim\n");return 0;
    }
    if (reply->status != MellowDiagOk) { fprintf(stderr,"Diagnostic operation status=%u state=%u\n",reply->status,reply->state);return 0; }
    return 1;
}
int main(int argc, char **argv) {
    int allocate = argc == 2 && strcmp(argv[1],"--allocate")==0;
    if (argc > 2 || (argc == 2 && !allocate)) { fprintf(stderr,"usage: %s [--allocate]\n",argv[0]);return 2; }
    if (geteuid()!=0) { fprintf(stderr,"Administrator privileges are required by this diagnostic service\n");return 2; }
    io_service_t service = IOServiceGetMatchingService(kIOMainPortDefault,IOServiceMatching(MELLOW_DIAG_SERVICE));
    if (service == IO_OBJECT_NULL) {
        fprintf(stderr,"MellowTahoeDiagnostic absent; verify -mellowdiag, physical matching, D0 and BAR0/GMD logs\n");return 3;
    }
    io_connect_t connection=IO_OBJECT_NULL;
    kern_return_t opened=IOServiceOpen(service,mach_task_self(),MELLOW_DIAG_CONNECT_TYPE,&connection);
    IOObjectRelease(service);
    if (opened!=KERN_SUCCESS) { fprintf(stderr,"IOServiceOpen failed 0x%x\n",opened);return 4; }
    MellowDiagReply reply;
    int ok=invoke(connection,MellowDiagQuery,0,0,&reply);
    uint64_t caps=ok?reply.diagnosticCapabilities:0;
    int allocationPassed=0;
    if (ok && allocate) {
        if (!(caps & MellowDiagPreparedDma)) {
            fprintf(stderr,"Prepared DMA unavailable: no admitted device mapper; identity fallback is refused\n");ok=0;
        } else {
            ok=invoke(connection,MellowDiagAllocate,0,4096,&reply);
            uint64_t handle=reply.allocationHandle;
            if (ok && (!handle || reply.allocationBytes!=4096 || reply.pageCount!=1 || reply.state!=MellowDiagAllocated)) ok=0;
            if (ok) ok=invoke(connection,MellowDiagRelease,handle,0,&reply);
            if (ok && (reply.allocationHandle || reply.allocationBytes || reply.pageCount || reply.state!=MellowDiagReady)) ok=0;
            allocationPassed=ok;
        }
    }
    const kern_return_t closed=IOServiceClose(connection);
    if (closed!=KERN_SUCCESS) { fprintf(stderr,"IOServiceClose failed 0x%x\n",closed);ok=0; }
    if (!ok) return 5;
    printf("{\"status\":\"%s\",\"diagnostic_capabilities\":%" PRIu64 ",\"prepared_dma_cycle\":%s,"
           "\"gpu_submission_tested\":false,\"guc_authenticated\":false,\"metal_tested\":false}\n",
           allocationPassed?"PASS_TAHOE_DIAGNOSTIC_DMA_CYCLE_ONLY":"PASS_TAHOE_DIAGNOSTIC_QUERY_ONLY",caps,
           allocationPassed?"true":"false");
    return 0;
}
