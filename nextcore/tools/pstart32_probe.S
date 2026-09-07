/* Independently authored GNU as IA-32 fixture. Contains no Apple code.
 * Linked at physical 0x101000; checks the explicit controlled QEMU probe ABI.
 * A successful run is a CPU/loader/encoder test, not XNU or macOS execution.
 */
.intel_syntax noprefix
.code32
.section .text
.global _start

.macro say message
    mov esi, OFFSET FLAT:\message
    call serial_puts
.endm

_start:
    mov ebx, eax
    call serial_init
    say msg_entry
    mov eax, cr0
    and eax, 0x80000001
    cmp eax, 1
    jne fail_mode
    mov ecx, 0xc0000080
    rdmsr
    test eax, 0x500
    jnz fail_mode
    mov ax, cs
    cmp ax, 8
    jne fail_segments
    mov ax, ds
    cmp ax, 16
    jne fail_segments
    mov ax, ss
    cmp ax, 16
    jne fail_segments
    pushfd
    pop eax
    test eax, 0x600
    jnz fail_flags
    say msg_cpu

    /* Bound boot_args to the extra arena after our fixed image. */
    cmp ebx, 0x302000
    jb fail_args
    cmp ebx, 0x401000
    ja fail_args
    test ebx, 0xfff
    jnz fail_args
    cmp WORD PTR [ebx], 0
    jne fail_args
    cmp WORD PTR [ebx + 2], 2
    jne fail_args
    cmp BYTE PTR [ebx + 4], 64
    jne fail_args
    cmp WORD PTR [ebx + 8], 0x762d
    jne fail_args
    cmp BYTE PTR [ebx + 10], 0
    jne fail_args
    cmp DWORD PTR [ebx + 0x438], 0x100000
    jne fail_args
    mov ebp, DWORD PTR [ebx + 0x43c]
    cmp ebp, 0x203000
    jb fail_args
    add ebp, 0x100000
    jc fail_args
    cmp ebp, 0x402000
    ja fail_args
    lea eax, [ebx + 4096]
    cmp eax, ebp
    ja fail_args
    say msg_args

    /* Bounds, descriptor stride/version, and an actual loader-code range. */
    mov esi, DWORD PTR [ebx + 0x408]
    cmp esi, 0x302000
    jb fail_map
    mov ecx, DWORD PTR [ebx + 0x40c]
    test ecx, ecx
    jz fail_map
    mov eax, esi
    add eax, ecx
    jc fail_map
    cmp eax, ebp
    ja fail_map
    mov edi, DWORD PTR [ebx + 0x410]
    cmp edi, 40
    jb fail_map
    mov eax, ecx
    xor edx, edx
    div edi
    test edx, edx
    jnz fail_map
    cmp DWORD PTR [ebx + 0x414], 1
    jne fail_map
    mov ecx, eax
map_next:
    cmp DWORD PTR [esi], 1
    jne map_skip
    cmp DWORD PTR [esi + 12], 0
    jne map_skip
    cmp DWORD PTR [esi + 8], 0x100000
    ja map_skip
    cmp DWORD PTR [esi + 28], 0
    jne map_skip
    mov eax, DWORD PTR [esi + 24]
    cmp eax, 0x100000
    jae map_skip
    shl eax, 12
    add eax, DWORD PTR [esi + 8]
    jc map_skip
    cmp eax, ebp
    jae map_ok
map_skip:
    add esi, edi
    loop map_next
    jmp fail_map
map_ok:
    say msg_map

    /* Independently decode the fixture's small root/chosen flattened tree. */
    mov esi, DWORD PTR [ebx + 0x430]
    cmp esi, 0x302000
    jb fail_tree
    cmp DWORD PTR [ebx + 0x434], 140
    jne fail_tree
    mov eax, esi
    add eax, 140
    jc fail_tree
    cmp eax, ebp
    ja fail_tree
    cmp DWORD PTR [esi], 1
    jne fail_tree
    cmp DWORD PTR [esi + 4], 1
    jne fail_tree
    cmp DWORD PTR [esi + 8], 0x656d616e
    jne fail_tree
    cmp BYTE PTR [esi + 12], 0
    jne fail_tree
    cmp DWORD PTR [esi + 40], 1
    jne fail_tree
    cmp BYTE PTR [esi + 44], 0
    jne fail_tree
    cmp DWORD PTR [esi + 48], 2
    jne fail_tree
    cmp DWORD PTR [esi + 52], 0
    jne fail_tree
    cmp DWORD PTR [esi + 56], 0x656d616e
    jne fail_tree
    cmp BYTE PTR [esi + 60], 0
    jne fail_tree
    cmp DWORD PTR [esi + 88], 7
    jne fail_tree
    cmp DWORD PTR [esi + 92], 0x736f6863
    jne fail_tree
    cmp WORD PTR [esi + 96], 0x6e65
    jne fail_tree
    cmp BYTE PTR [esi + 98], 0
    jne fail_tree
    cmp DWORD PTR [esi + 100], 0x746f6f62
    jne fail_tree
    cmp DWORD PTR [esi + 104], 0x6772612d
    jne fail_tree
    cmp WORD PTR [esi + 108], 0x0073
    jne fail_tree
    cmp DWORD PTR [esi + 132], 3
    jne fail_tree
    cmp WORD PTR [esi + 136], 0x762d
    jne fail_tree
    cmp BYTE PTR [esi + 138], 0
    jne fail_tree
    say msg_tree

    /* Check every initialized byte and every byte of the BSS page. */
    mov esi, 0x300000
    mov ecx, 4096
    mov al, 3
data_next:
    cmp BYTE PTR [esi], al
    jne fail_data
    add al, 17
    inc esi
    loop data_next
    say msg_data
    mov edi, 0x301000
    mov ecx, 1024
    xor eax, eax
    repe scasd
    jne fail_bss
    say msg_bss
    say msg_ok
    mov eax, 0x10
    jmp finish

fail_mode:
    say msg_fail_mode
    jmp failed
fail_segments:
    say msg_fail_segments
    jmp failed
fail_flags:
    say msg_fail_flags
    jmp failed
fail_args:
    say msg_fail_args
    jmp failed
fail_map:
    say msg_fail_map
    jmp failed
fail_tree:
    say msg_fail_tree
    jmp failed
fail_data:
    say msg_fail_data
    jmp failed
fail_bss:
    say msg_fail_bss
failed:
    mov eax, 0x11
finish:
    mov dx, 0xf4
    out dx, eax
halt:
    cli
    hlt
    jmp halt

serial_init:
    pushad
    mov dx, 0x3f9
    xor al, al
    out dx, al
    mov dx, 0x3fb
    mov al, 0x80
    out dx, al
    mov dx, 0x3f8
    mov al, 1
    out dx, al
    mov dx, 0x3f9
    xor al, al
    out dx, al
    mov dx, 0x3fb
    mov al, 3
    out dx, al
    mov dx, 0x3fa
    mov al, 7
    out dx, al
    mov dx, 0x3fc
    mov al, 0x0b
    out dx, al
    popad
    ret

serial_puts:
    pushad
serial_next:
    mov al, BYTE PTR [esi]
    test al, al
    jz serial_done
    mov ah, al
    mov ecx, 65536
    mov dx, 0x3fd
serial_wait:
    in al, dx
    test al, 0x20
    jnz serial_ready
    loop serial_wait
    jmp serial_done
serial_ready:
    mov al, ah
    mov dx, 0x3f8
    out dx, al
    inc esi
    jmp serial_next
serial_done:
    popad
    ret

msg_entry: .asciz "NXPROBE: ENTRY\r\n"
msg_cpu: .asciz "NXPROBE: CPU_STATE_OK\r\n"
msg_args: .asciz "NXPROBE: BOOT_ARGS_OK\r\n"
msg_map: .asciz "NXPROBE: MEMORY_MAP_OK\r\n"
msg_tree: .asciz "NXPROBE: DEVICE_TREE_OK\r\n"
msg_data: .asciz "NXPROBE: DATA_OK\r\n"
msg_bss: .asciz "NXPROBE: BSS_OK\r\n"
msg_ok: .asciz "NXPROBE: PSTART32_OK\r\n"
msg_fail_mode: .asciz "NXPROBE: FAIL_MODE\r\n"
msg_fail_segments: .asciz "NXPROBE: FAIL_SEGMENTS\r\n"
msg_fail_flags: .asciz "NXPROBE: FAIL_FLAGS\r\n"
msg_fail_args: .asciz "NXPROBE: FAIL_BOOT_ARGS\r\n"
msg_fail_map: .asciz "NXPROBE: FAIL_MEMORY_MAP\r\n"
msg_fail_tree: .asciz "NXPROBE: FAIL_DEVICE_TREE\r\n"
msg_fail_data: .asciz "NXPROBE: FAIL_DATA\r\n"
msg_fail_bss: .asciz "NXPROBE: FAIL_BSS\r\n"
fixture_identity: .asciz "NEXTCORE_AUTHORED_PSTART32_PROBE_V1"
