/* SPDX-License-Identifier: BSD-4-Clause; minimal UEFI 2.11 ABI declarations. */
#ifndef VENFIRE_UEFI_H
#define VENFIRE_UEFI_H
#include "jit.h"
typedef uint64_t EFI_STATUS;
typedef void *EFI_HANDLE;
typedef uint16_t CHAR16;
typedef struct { uint32_t a;uint16_t b,c;uint8_t d[8]; } EFI_GUID;
#define EFI_ERROR_BIT (UINT64_C(1)<<63)
#define EFI_UNSUPPORTED (EFI_ERROR_BIT|3)
#define EFI_INVALID_PARAMETER (EFI_ERROR_BIT|2)
#define EFI_BUFFER_TOO_SMALL (EFI_ERROR_BIT|5)
#define EFI_NOT_FOUND (EFI_ERROR_BIT|14)
#define EFI_ABORTED (EFI_ERROR_BIT|21)
#define EFI_MEMORY_XP UINT64_C(0x4000)
#define EFI_MEMORY_RO UINT64_C(0x20000)
typedef struct { uint64_t Signature; uint32_t Revision, HeaderSize, CRC32, Reserved; } EFI_TABLE_HEADER;
typedef struct EFI_TEXT EFI_TEXT;
struct EFI_TEXT { void *Reset;EFI_STATUS (VF_ABI *OutputString)(EFI_TEXT *,const CHAR16 *); };
typedef struct EFI_MEMORY_ATTRIBUTE EFI_MEMORY_ATTRIBUTE;
struct EFI_MEMORY_ATTRIBUTE {
    EFI_STATUS (VF_ABI *Get)(EFI_MEMORY_ATTRIBUTE *,uint64_t,uint64_t,uint64_t *);
    EFI_STATUS (VF_ABI *Set)(EFI_MEMORY_ATTRIBUTE *,uint64_t,uint64_t,uint64_t);
    EFI_STATUS (VF_ABI *Clear)(EFI_MEMORY_ATTRIBUTE *,uint64_t,uint64_t,uint64_t);
};
typedef struct EFI_CPU_ARCH EFI_CPU_ARCH;
struct EFI_CPU_ARCH {
    void *FlushDataCache,*EnableInterrupt,*DisableInterrupt,*GetInterruptState,*Init,*RegisterInterruptHandler,*GetTimerValue;
    EFI_STATUS (VF_ABI *SetMemoryAttributes)(EFI_CPU_ARCH *,uint64_t,uint64_t,uint64_t);
};
typedef struct {
    EFI_TABLE_HEADER Hdr;
    void *RaiseTPL,*RestoreTPL;
    EFI_STATUS (VF_ABI *AllocatePages)(unsigned,unsigned,uint64_t,uint64_t *);
    EFI_STATUS (VF_ABI *FreePages)(uint64_t,uint64_t);
    void *GetMemoryMap,*AllocatePool,*FreePool,*CreateEvent,*SetTimer,*WaitForEvent,*SignalEvent,*CloseEvent,*CheckEvent;
    void *InstallProtocolInterface,*ReinstallProtocolInterface,*UninstallProtocolInterface;
    EFI_STATUS (VF_ABI *HandleProtocol)(EFI_HANDLE,EFI_GUID *,void **);
    void *Reserved,*RegisterProtocolNotify,*LocateHandle,*LocateDevicePath,*InstallConfigurationTable;
    void *LoadImage,*StartImage,*Exit,*UnloadImage,*ExitBootServices,*GetNextMonotonicCount,*Stall,*SetWatchdogTimer;
    void *ConnectController,*DisconnectController,*OpenProtocol,*CloseProtocol,*OpenProtocolInformation;
    void *ProtocolsPerHandle,*LocateHandleBuffer;
    EFI_STATUS (VF_ABI *LocateProtocol)(EFI_GUID *,void *,void **);
} EFI_BOOT_SERVICES;
typedef struct {
    EFI_TABLE_HEADER Hdr;CHAR16 *FirmwareVendor;uint32_t FirmwareRevision;
    EFI_HANDLE ConsoleInHandle;void *ConIn;EFI_HANDLE ConsoleOutHandle;EFI_TEXT *ConOut;
    EFI_HANDLE StandardErrorHandle;EFI_TEXT *StdErr;void *RuntimeServices;
    EFI_BOOT_SERVICES *BootServices;uint64_t NumberOfTableEntries;void *ConfigurationTable;
} EFI_SYSTEM_TABLE;
typedef struct {
    uint32_t Revision;EFI_HANDLE ParentHandle;EFI_SYSTEM_TABLE *SystemTable;EFI_HANDLE DeviceHandle;
    void *FilePath,*Reserved;uint32_t LoadOptionsSize;void *LoadOptions,*ImageBase;
    uint64_t ImageSize;unsigned ImageCodeType,ImageDataType;void *Unload;
} EFI_LOADED_IMAGE;
typedef struct EFI_FILE EFI_FILE;
struct EFI_FILE {
    uint64_t Revision;
    EFI_STATUS (VF_ABI *Open)(EFI_FILE *,EFI_FILE **,const CHAR16 *,uint64_t,uint64_t);
    EFI_STATUS (VF_ABI *Close)(EFI_FILE *);
    void *Delete;
    EFI_STATUS (VF_ABI *Read)(EFI_FILE *,uint64_t *,void *);
};
typedef struct EFI_FS EFI_FS;
struct EFI_FS { uint64_t Revision;EFI_STATUS (VF_ABI *OpenVolume)(EFI_FS *,EFI_FILE **); };
_Static_assert(offsetof(EFI_BOOT_SERVICES,LocateProtocol)==320,"Boot Services ABI");
_Static_assert(offsetof(EFI_SYSTEM_TABLE,BootServices)==96,"System Table ABI");
_Static_assert(offsetof(EFI_LOADED_IMAGE,LoadOptions)==56,"Loaded Image ABI");
#endif
