L0:
(W)     mov (8|M0)               r127.0<1>:ud  0x0:ud                             
(W)     and (1|M0)               r127.2<1>:ud  r0.0<0;1,0>:ud    0xFFFFFFC0:ud             
(W)     and (1|M0)               r127.0<1>:uw  r0.4<0;1,0>:uw    0xFF:uw             
(W)     add (1|M0)               r127.2<1>:ud  r127.2<0;1,0>:ud  0x20:ud              {I@2}
(W)     add (1|M0)               r127.2<1>:ud  r127.2<0;1,0>:ud  0x0:ud              {I@1}
(W)     mad (1|M0)               r127.2<1>:ud  r127.2<0;0>:ud    r127.0<0;0>:uw    0xC0:uw              {I@1}
(W)     mov (8|M0)               r7.0<1>:ud    r1.0<1;1,0>:ud                  
(W)     send.dc0 (8|M0)          r1       r127    null:0  0x0            0x024844FD           {A@1,$0} // wr:1h+0, rd:4; oword aligned block read x8
(W)     add (1|M0)               r127.2<1>:ud  r127.2<0;1,0>:ud  0x80:uw              {$0.src}
(W)     send.dc0 (8|M0)          r5       r127    null:0  0x0            0x022843FD           {A@1,$1} // wr:1h+0, rd:2; oword aligned block read x4
        nop                    
        nop                    
(W)     mov (8|M0)               r127.0<1>:ud  0x0:ud                              {$1.src}
(W)     and (1|M0)               r127.2<1>:ud  r0.0<0;1,0>:ud    0xFFFFFFC0:ud             
(W)     add (1|M0)               r127.2<1>:ud  r127.2<0;1,0>:ud  0x0:ud              {I@1}
(W)     send.dc0 (8|M0)          r8       r127    null:0  0x0            0x021842FD           {A@1,$2} // wr:1h+0, rd:1; oword aligned block read x2
(W)     mov (8|M0)               r3.0<1>:ud    r0.0<1;1,0>:ud                   {$0.dst}
(W)     or (1|M0)                cr0.0<1>:ud   cr0.0<0;1,0>:ud   0x4C0:uw              {A@1}
(W)     mul (1|M0)               acc0.0<1>:d   r7.3<0;1,0>:d     r3.2<0;1,0>:uw   {A@1}
(W)     mach (1|M0)              r4.0<1>:d     r7.3<0;1,0>:d     r3.1<0;1,0>:d   
        sync.nop                             null                             {Compacted,$1.dst}
        add3 (16|M0)             r5.0<1>:d     r4.0<0;0>:d       r1.0<1;0>:uw      r7.0<0>:d        {I@1}
        add3 (16|M16)            r9.0<1>:d     r4.0<0;0>:d       r2.0<1;0>:uw      r7.0<0>:d       
        sync.nop                             null                             {Compacted,$2.dst}
        cmp (16|M0)   (lt)f0.0   null<1>:d     r5.0<1;1,0>:ud    r8.3<0;1,0>:ud   {I@2}
        cmp (16|M16)  (lt)f0.0   null<1>:d     r9.0<1;1,0>:ud    r8.3<0;1,0>:ud   {I@2}
(W)     csel (4|M0)   (eq)f0.0   r1.0<1>:w     r1.0<4;1>:w       r1.0<4;1>:w       r1.0<1>:w       
(W)     csel (4|M0)   (eq)f0.0   r1.4<1>:f     r1.4<4;1>:f       r1.4<4;1>:f       r1.4<1>:f        {A@1}
(~f0.0) goto (32|M0)                         L880                  L880                
L448:
(W)     mov (1|M0)               a0.0<1>:ud    r8.4<0;1,0>:d                    {A@1}
        shl (16|M0)              r11.0<1>:d    r5.0<1;1,0>:d     2:w               {Compacted}
        shl (16|M16)             r13.0<1>:d    r9.0<1;1,0>:d     2:w               {Compacted}
        send.ugm (16|M0)         r15      r11     null:0  a0.0        0x24280500           {ExBSO,A@2,$3} // wr:2+0, rd:2; load.ugm.d32.a32.ca.ca.bss[a0.0]
        send.ugm (16|M16)        r17      r13     null:0  a0.0        0x24280500           {ExBSO,A@1,$4} // wr:2+0, rd:2; load.ugm.d32.a32.ca.ca.bss[a0.0]
(W)     mov (1|M0)               a0.0<1>:ud    r8.5<0;1,0>:d                    {A@1}
        xor (16|M0)              r19.0<1>:d    r15.0<1;1,0>:d    r8.2<0;1,0>:d    {Compacted,$3.dst}
(W)     mul (8|M0)               acc0.0<1>:d   r19.0<1;1,0>:d    0x660D:uw              {I@1}
        xor (16|M16)             r21.0<1>:d    r17.0<1;1,0>:d    r8.2<0;1,0>:d    {Compacted,$4.dst}
        mach (8|M0)              r19.0<1>:d    r19.0<1;1,0>:d    1664525:d              
(W)     mul (8|M8)               acc0.0<1>:d   r20.0<1;1,0>:d    0x660D:uw             
        mach (8|M8)              r20.0<1>:d    r20.0<1;1,0>:d    1664525:d              
(W)     mul (8|M16)              acc0.0<1>:d   r21.0<1;1,0>:d    0x660D:uw              {I@4}
        mach (8|M16)             r21.0<1>:d    r21.0<1;1,0>:d    1664525:d              
(W)     mul (8|M24)              acc0.0<1>:d   r22.0<1;1,0>:d    0x660D:uw             
        mach (8|M24)             r22.0<1>:d    r22.0<1;1,0>:d    1664525:d              
(W)     mul (8|M0)               acc0.0<1>:d   r5.0<1;1,0>:d     0x79B1:uw             
        mach (8|M0)              r23.0<1>:d    r5.0<1;1,0>:d     -1640531535:d              
(W)     mul (8|M8)               acc0.0<1>:d   r6.0<1;1,0>:d     0x79B1:uw             
        mach (8|M8)              r24.0<1>:d    r6.0<1;1,0>:d     -1640531535:d              
(W)     mul (8|M16)              acc0.0<1>:d   r9.0<1;1,0>:d     0x79B1:uw             
        mach (8|M16)             r25.0<1>:d    r9.0<1;1,0>:d     -1640531535:d              
(W)     mul (8|M24)              acc0.0<1>:d   r10.0<1;1,0>:d    0x79B1:uw             
        add (16|M0)              r19.0<1>:d    r19.0<1;1,0>:d    1013904223:d              
        add (16|M16)             r21.0<1>:d    r21.0<1;1,0>:d    1013904223:d               {I@7}
        mach (8|M24)             r26.0<1>:d    r10.0<1;1,0>:d    -1640531535:d              
        xor (16|M0)              r19.0<1>:d    r19.0<1;1,0>:d    r23.0<1;1,0>:d   {Compacted,I@3}
        xor (16|M16)             r21.0<1>:d    r21.0<1;1,0>:d    r25.0<1;1,0>:d   {Compacted,I@2}
        send.ugm (16|M0)         null     r11     r19:2   a0.0        0x24040504           {ExBSO,A@2,$5} // wr:2+2, rd:0; store.ugm.d32.a32.uc.wb.bss[a0.0]
        send.ugm (16|M16)        null     r13     r21:2   a0.0        0x24040504           {ExBSO,A@1,$6} // wr:2+2, rd:0; store.ugm.d32.a32.uc.wb.bss[a0.0]
L880:
        join (32|M0)                         L896                                
L896:
(W)     mov (8|M0)               r127.0<1>:f   r3.0<1;1,0>:f                    {Compacted}
(W)     send.ugm (1|M0)          r27      r3      null:0  0x0            0x0210641F           {$7} // wr:1+0, rd:1; fence invalid flush type scoped to tile
(W)     mov (8|M0)               null<1>:ud    r27.0<1;1,0>:ud                  {$7.dst}
        sync.nop                             null                             {Compacted,F@1}
(W)     send.gtwy (1|M0)         null     r127    null:0  0x0            0x02000010           {EOT} // wr:1+0, rd:0; end of thread
L960:
        nop                    
(W)     mov (16|M0)              null<1>:ud    0xE56B373D:ud                             
(W)     mov (16|M0)              null<1>:ud    0x33C8A34E:ud                             
(W)     mov (16|M0)              null<1>:ud    0x0:ud                             
(W)     mov (16|M0)              null<1>:ud    0x1:ud                             
        illegal                
        illegal                
        illegal                
        illegal                
        illegal                
        illegal                
        illegal                
        illegal                
        illegal                
        illegal                
        illegal                
