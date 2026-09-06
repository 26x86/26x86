> **Historical record — preserved unedited.** Component documentation for the hand-written
> Intel Xe backend, which compiles into the kext but has no call path
> ([Mellow/RuntimeReadiness.hpp:84](../Mellow/RuntimeReadiness.hpp)). Scheduled to move to
> `docs/backends/xe/` in P1. For how these modules map onto the vendor-neutral abstraction
> see [MGAL.md](MGAL.md); for the current architecture see [ARCHITECTURE.md](ARCHITECTURE.md).

# 4단계 GPU 페이지 테이블 구성기

`Mellow/XePageTable.cpp/.hpp`는 CPU 메모리에 4 KiB system-memory GPU 페이지
테이블 계층을 실제로 구성한다. 48-bit GPU VA를 4단계의 9-bit 인덱스로 나누며,
46-bit DMA 주소의 PTE/PDE는 `XeMemory`의 검증된 인코더를 사용한다.
주소와 플래그는 Intel Xe의 `xelp_pde_encode_bo` 및 `xelp_pte_encode_addr`에
해당하는 범위로 제한했다. 이 구현은 GPU에 루트를 쓰거나 TLB를 무효화하지 않는다.

## 구현한 기능

- 호출자가 보유한 최대 128개 페이지 풀에서 루트와 하위 테이블을 할당한다.
  풀의 각 페이지는 pinned DMA 주소와 CPU 접근 포인터를 함께 제공해야 한다.
  일반 물리 주소를 DMA 주소인 것처럼 대체하는 기능은 없다.
- 전체 풀의 주소·정렬·중복 DMA·겹치는 CPU 범위를 먼저 확인한다.
  입력이 잘못되었을 때 기존 버퍼를 먼저 지우지 않는다.
- `map4K`는 필요한 하위 계층만 생성하고, 자원 부족·잘못된 부모·중복 leaf를
  발견하면 해당 호출에서 만든 부모 연결을 되돌린다. 한 페이지 매핑 단위의 원자성이다.
  여러 페이지 매핑을 하나의 GPU-visible transaction으로 게시하는 기능은 별도다.
- 부모 PDE는 풀에 속한 올바른 단계의 테이블을 가리켜야 하며 예상된 플래그와
  정확히 일치해야 한다. 커다란 페이지·DM·scratch·null PTE를 임의로 해석하지 않는다.
- 페이지 테이블 풀 자체를 데이터 leaf로 노출하지 않는다.
- `lookup`은 계층을 실제로 따라가 leaf를 읽는다. `unmap4K`는 leaf를 지우고
  비어진 하위 테이블을 반환한다. owner가 다른 요청은 거부한다.
- `seal` 이후에는 수정이 영구 차단된다. 얕은 복사가 seal과 소유권을 우회하지
  않도록 복사 생성·대입도 금지했다. GPU 사용 이후 이 클래스로 in-place 수정할 수 없다.

## 검증

호스트 검사에서 **30,698 assertions**가 통과했다. 별도 구현한 page walker로
생성된 메모리를 따라가며 결과를 대조했다. 2 MiB·1 GiB·512 GiB 경계와 마지막
48-bit 페이지, 16개 PAT 인덱스, 풀 부족 rollback, 중복 매핑, owner 오류,
잘못된 주소/CPU 범위, seal 이후 거부, 5,000단계 매핑·해제 시퀀스를 포함한다.

이 시험은 일반 CPU 배열을 사용한다. 실제 IOMMU mapping, GPU page-walk,
cache/PAT programming, forcewake, root/context publish, TLB invalidation은
실행하지 않았다. `seal` 성공은 CPU 테이블 편집을 잠갔다는 뜻이며 GPU가 사용하고
있다는 뜻이 아니다. 미게시 페이지 풀을 caller가 단독 소유하고 모든 호출을
직렬화해야 하며, GPU에서 사용하는 테이블을 이 인터페이스에 넘겨서는 안 된다.

초기화 이후 풀의 포인터·DMA 주소·테이블 내용을 caller가 외부에서 변경하는 것도
허용하지 않는다. 이 인터페이스는 사용자 공간에 노출된 raw DMA API가 아니다.
실제 드라이버 연결에는 장치 IOMapper로 pin한 페이지의 수명과 context, PAT,
전송 완료가 입증된 publish/invalidate adapter가 필요하다.

## 실제 IOKit 고정 메모리 연결 (0.3)

XePageTableIOKit은 장치별 mapper로 실제 메모리를 고정하고 CPU buffer 페이지와
IODMACommand의 DMA 주소를 TablePage로 연결한다. 비연속 DMA 페이지도 지원한다.
root 반환 전에 IODMACommand 동기화와 CPU ordering을 수행한다. 반환한 root의
정확한 owner/root 사용 종료를 입증하는 trusted backend callback 없이는 메모리를
해제하지 않는다. 부분 pin/unpin 실패는 resource를 유지한다. 실제 GPU root 등록과
TLB 완료는 구현하지 않는다.

xe_page_table_iokit_tests.cpp는 production 연결부와 페이지 테이블을 실행하며
IOKit 경계만 테스트 함수로 바꾼다. kernel 타깃은 실제 Apple 헤더와 production pin
구현으로 별도 빌드한다. 호스트 41개 검사는 비연속 DMA, PAT, owner, seal, sync
실패, root 반환 뒤 해제 차단, failed-unpin 격리·재시도를 검증했다. 실기 검사는 아니다.
