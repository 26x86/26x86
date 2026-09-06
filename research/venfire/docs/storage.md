# VMApple 저장 장치 계층

`storage-create`는 기존 AUX/root raw 파일을 변경하지 않고 각각 qcow2 파일을 만듭니다.
`boot-session`은 이후 게스트의 정상적인 디스크 쓰기만 이 파일에 저장합니다.
macOS 코드, 서명, PAC 또는 부트 신뢰 판단을 변경하는 기능은 없습니다.

```sh
python -m venfire storage-create --aux /path/to/aux.img --disk /path/to/disk.img --aux-offset 0x4000 --directory /path/to/new-session
python -m venfire boot-session --qemu /path/to/qemu-system-aarch64 --firmware /path/to/AVPBooter.vmapple2.bin --directory /path/to/new-session --uuid 0xYOUR_VM_ECID --output /path/to/new-evidence
```

`0x4000`은 해당 형식의 기존 Virtualization.framework AUX 메타데이터가 확인됐을 때만
사용합니다. `--uuid`는 upstream 이름과 달리 cfg의 ECID 필드입니다. 복원 중에는 같은 VM의 값을 유지합니다. 이 명령은 유효한 설치 또는
개인화된 부트 저장소를 생성하지 않습니다. 개발용 비배포 빌드에서는 실행 명령에
`--developer-host-bypass`를 명시할 수 있습니다. Intel/AVX2 조건은 유지됩니다.

`--seconds`를 생략하면 게스트 종료 또는 사용자 중단까지 실행합니다. 종료 코드 5는
증거가 기록되었지만 macOS 부팅 여부를 자동 인증하지 않았다는 뜻입니다. `serial.log`,
`backend.log`, `result.json`을 확인합니다. 기본 실행은 headless이며 선택형 GPU의 검증 범위는 `graphics.md`에 있습니다.

VMApple ROM의 BDIF/pflash와 런타임 virtio-blk는 **하나의 qcow2 node**를 공유합니다.
기본 저수준 저장 그래프는 BDIF 쓰기를 거부합니다. 정규 `boot-session`은 코어 패치 0004를
확인하고 `allow-block-writes=on` 및 동일 프로세스의 virtio `share-rw=on`을 설정해
원본 iBSS의 정상 AUX 초기화 쓰기를 COW에 받습니다. 외부 파일 잠금은 유지됩니다.
읽기 전용 `boot-probe`는 이 예외를 활성화하지 않습니다. 원본은 file/raw 두 계층 모두 읽기
전용입니다. AUX 오프셋은 raw view에 적용하며 원본을 잘라내지 않습니다.
qcow2의 헤더에는 backing 경로를 넣지 않으며 실행할 때 검사한 manifest에서 그래프를
구성합니다. 따라서 qcow2만 단독으로 열면 원본에 있던 데이터가 보이지 않습니다.
`session.json`, `bases.json`, 두 overlay와 원본 파일을 함께 보존해야 합니다.

일반 file locking을 유지하며 중복 쓰기 프로세스는 거절합니다. `werror=report`,
`rerror=report`, `cache=writeback`으로 flush를 무시하지 않도록 구성합니다.
이 설정과 QMP I/O 시험만으로 Apple 파일 시스템의 장애 복구·내구성을 입증하지 않습니다.
Apple 고유 BARRIER 명령의 전체 의미는 별도의 가상 장치 검증 항목입니다.

```sh
python tools/verify_storage.py --qemu /path/to/qemu-system-aarch64 --output /path/to/new-storage-evidence
```

이 검증은 자체 작성 바이트만 사용하여 두 인터페이스의 쓰기 공유, 재시작 후 지속,
원본 보존, pflash 쓰기 거절, 동시 overlay writer 거절을 실제 QMP로 확인합니다.
게스트는 일시 정지 상태이며 Apple OS의 실제 I/O 완료 시험과 구분합니다.

근거: [QEMU VMApple 실행 구성](https://www.qemu.org/docs/master/system/arm/vmapple.html),
[QEMU qcow2 형식과 backing 파일](https://www.qemu.org/docs/master/system/qemu-block-drivers.html).

BDIF의 실제 쓰기 경로는 DMA 읽기 → block write → flush가 모두 성공한 뒤에만 성공을
반환합니다. `tools/verify_bdif_storage.py`의 22개 실제 MMIO/DMA 시험은 기본/읽기 전용
거부, AUX/root 읽기와 재시작 지속, 잘못된 범위·DMA·길이·상태 descriptor,
주입한 flush EIO 실패 반환, 모든 원본 보존을 확인합니다. `evidence/bdif-storage.json` 참고.
