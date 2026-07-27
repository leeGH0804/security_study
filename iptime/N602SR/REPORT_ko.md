# 🔧 Firmware 비교 보고서 — ipTIME N602SR

> Hardware Dump vs. Official Firmware — raw byte 비교부터 ELF header,
> calibration 데이터까지 파고드는 다계층·근거 기반 리버스 엔지니어링 비교 분석.

## 📌 프로젝트 개요

이 문서는 **실장비(ipTIME N602SR)에서 하드웨어적으로 직접 추출한 SPI flash
dump**와 **제조사가 배포하는 공식 firmware 파일**을 여러 관점에서 비교하고,
각 비교 결과가 *왜* 그런 모습으로 나타나는지, 그리고 그것이 *무엇을
의미하는지*를 설명하는 firmware 비교 분석 보고서입니다.

- **분석 목적** — 실장비 dump가 공식 배포본과 구조적으로 얼마나 같고
  다른지 규명하고, 그 차이의 원인과 의미를 근거를 들어 설명합니다.

- **분석 대상**

| 구분          | 정보                                         |
| ----------- | ------------------------------------------ |
| 기기          | ipTIME N602SR                              |
| 하드웨어 dump   | `iptime_dump_2.bin` (SPI flash 칩 raw read) |
| 공식 firmware | `n602sr_ml_15_258.bin` (v15.258 공식 배포 이미지) |

- **분석 범위** — 파일 단위 → binwalk/entropy → flash layout → rootfs →
  binary(ELF) → configuration/calibration까지, 총 6단계의 계층적 비교.

- **사용 도구** — `binwalk`, `sha256sum`/`md5sum`, `file`, `strings`,
  `diff`/`cmp`, `unsquashfs`, `readelf`, `objdump`, `xxd`, 그리고 이번에
  새로 설치해 추가로 사용한 `diffoscope`, `sasquatch`, `vbindiff`,
  `radare2`/`rabin2`, `ent` (`rizin`은 본 환경에 패키지가 없어 `radare2`로
  대체) — [🔬 추가 도구 기반 교차 검증](#-추가-도구-기반-교차-검증) 참고

- **분석 흐름** — 아래 각 장은 항상 **① 비교 목적 → ② 비교 결과(표) → ③
  분석 → ④ 결론 → ⑤ 핵심 요약** 순서로 구성되어, 각 장만 읽어도 해당
  주제의 차이와 의미를 이해할 수 있도록 작성했습니다.

> [!NOTE]
> 본 문서는 **구조적 비교(structural comparison)** 보고서이며, 취약점
> 분석(vulnerability assessment)이 아닙니다. 모든 결론은 이 저장소의
> `analysis/` 아래에 실제로 저장된 산출물을 근거로 작성되었으며, 근거가
> 간접적이거나 불확실한 부분은 본문에서 "추정"으로 명확히 표기합니다.

---

## 🎯 분석 목표

이 비교는 다음 네 가지 질문에 근거를 가지고 답하는 것을 목표로 합니다.

1. 하드웨어 dump는 **SPI flash 전체**를 온전히 캡처한 것인가?
2. 공식 배포 이미지는 **전체 칩 이미지**인가, **실제 크기에 맞춘 update
   이미지**인가?
3. **Bootloader, Kernel, RootFS, Binary, Configuration** 각각의 수준에서
   두 이미지가 일치하는가? 일치하지 않는다면 어느 부분에서, 왜 다른가?
4. 순정 이미지와 구분되는 **장치별 설정/calibration/MAC 데이터**가
   존재하는가?

---

## 📑 목차

- [🖥 분석 환경](#-분석-환경)
- [📂 Firmware 정보 비교](#-firmware-정보-비교)
- [🔍 Binwalk & Entropy 비교](#-binwalk--entropy-비교)
- [📦 Flash Memory Layout 비교](#-flash-memory-layout-비교)
- [🗂 RootFS 비교](#-rootfs-비교)
- [🧩 Binary 비교](#-binary-비교)
- [⚙ Configuration 비교](#-configuration-비교)
- [📖 종합 분석](#-종합-분석)
- [🔬 추가 도구 기반 교차 검증](#-추가-도구-기반-교차-검증)
- [🗣 분석자 의견](#-분석자-의견)
- [✅ 최종 결론](#-최종-결론)

---

## 🖥 분석 환경

| 항목 | 내용 |
|---|---|
| Device | ipTIME N602SR |
| Dump Method | SPI flash 칩 하드웨어 프로그래머를 이용한 raw read |
| Firmware Version | v15.258 (양쪽 모두, [Firmware 정보 비교](#-firmware-정보-비교) §4에서 rootfs 내부 문자열로 재확인) |
| OS | Linux (WSL2) |
| Tools | `binwalk`, `sha256sum`/`md5sum`, `file`, `strings`, `diff`, `cmp`, `unsquashfs`, `readelf`, `objdump`, `xxd` + 추가 설치: `diffoscope`, `sasquatch`, `vbindiff`, `radare2`/`rabin2`, `ent` |

- 전체 워크플로우는 `scripts/01_hash.sh` → `scripts/05_strings.sh`로 이어지는
  고정된 5단계 script pipeline이며, 절차 전체는
  [docs/methodology.md](docs/methodology.md)에 문서화되어 있습니다.
- 이번 리팩토링 과정에서 binwalk entropy scan, ELF header/program
  header/dynamic section 비교, SquashFS superblock 조회, rootfs
  파일/디렉터리 통계, calibration 영역 hex 분석을 **추가로 수행**했으며,
  원본 출력은 각각 `analysis/entropy/`, `analysis/elf/`,
  `analysis/squashfs/`, `analysis/rootfs_stats/`, `analysis/config/`
  아래에 저장되어 있습니다. 이 문서에는 핵심 결과만 요약합니다.
- Firmware 바이너리 자체는 저장소에 **커밋하지 않으며**, `analysis/`
  아래의 파생 텍스트/Markdown 산출물만 보관합니다.

---

## 📂 Firmware 정보 비교

### ① 비교 목적
두 파일이 전체적으로 동일한지 아닌지를 가장 저렴한 비용으로 먼저
확인합니다. 이후 모든 심화 분석은 이 결과에서 출발합니다.

### ② 비교 결과

| 비교 항목 | Hardware Dump (`iptime_dump_2.bin`) | Official Firmware (`n602sr_ml_15_258.bin`) |
|---|---|---|
| File Size | 8,388,608 bytes (8 MiB) | 8,163,328 bytes |
| SHA-256 | `4b5b060492c13033265d154abaac4798ea15d90d7f33e6975aa1ed4d0cd4a074` | `e6c6847f2f735d345d830e6f16d918498d7a05661c62fefabbab7eef705ab815` |
| MD5 | `bc51c837de03195a9b497ad092dd3160` | `018b21e0580996ecd284253bc27fc72d` |
| File Type (`file`) | `data` (컨테이너 헤더 없는 raw flash 이미지) | `data` (컨테이너 헤더 없는 raw flash 이미지) |
| 내부 버전 문자열 (`home/httpd/version`) | `15.258` | `15.258` |
| 내부 빌드 일시 (`home/httpd/build_date`) | `2025.09.22 13:53:18` | `2025.09.22 13:53:18` |

📄 출처: [analysis/hashes/firmware_hashes.txt](analysis/hashes/firmware_hashes.txt), [samples/README.md](samples/README.md)

### ③ 분석
- 전체 파일 크기와 hash는 다르지만, 그 차이는 정확히 **225,280 bytes**로
  고정되어 있습니다 — 이는 임의의 손상이나 무작위 변형이 아니라 규칙적인
  차이라는 뜻이며, 뒤에 나올 Flash Layout 비교에서 그 정체(trailing
  erased flash)를 규명합니다.
- rootfs 내부에 저장된 버전 문자열(`15.258`)과 빌드 일시가 두 이미지에서
  **완전히 동일**합니다. 즉 하드웨어 dump는 파일명이 암시하는 수준이
  아니라, rootfs 내부적으로도 스스로 "v15.258"이라고 기록하고 있는
  이미지입니다.
- `file` 명령은 두 이미지 모두 컨테이너 포맷(예: TAR, ZIP 등)이 아닌
  raw 이진 데이터로 판별합니다 — 벤더가 자체 헤더 포맷(§Flash Layout의
  Header 영역)을 사용함을 시사합니다.

### ④ 결론
파일 전체 단위 비교만으로는 두 이미지가 "다르다"는 사실 외에는 알 수
없지만, 크기 차이가 고정값이라는 점과 rootfs 내부 버전 문자열이
동일하다는 점은 두 이미지가 **같은 소프트웨어 릴리스의 서로 다른
포장 형태**일 가능성을 강하게 시사합니다. 이는 이후 장에서 구조적으로
검증됩니다.

> [!IMPORTANT]
> ### 핵심 요약
> - 두 파일은 byte 단위로 동일하지 않지만, 크기 차이는 정확히
>   225,280 bytes로 고정되어 있습니다.
> - rootfs에 내장된 버전 문자열(`15.258`)과 빌드 일시가 두 이미지에서
>   동일하여, 같은 릴리스임을 파일명이 아닌 내용으로도 확인했습니다.

---

## 🔍 Binwalk & Entropy 비교

### ① 비교 목적
두 이미지의 내부 구조(임베디드 파일 타입, offset, 압축 여부)가
동일한지, 그리고 그 구조가 압축/평문 경계 관점에서도 일치하는지를
확인합니다.

### ② 비교 결과

**Binwalk signature scan**

| 항목 | Hardware Dump | Official Firmware |
|---|---|---|
| Signature 개수 | 3개 (Header, Loader blob, Kernel) + 내부 SquashFS | 동일 |
| Signature offset | `0x8B14`, `0x9A60`, `0x42860`, `0x230000` | **완전히 동일** |
| Partition table 존재 여부 | 별도 partition table 미발견 | 별도 partition table 미발견 |

📄 출처: [analysis/binwalk/dump_binwalk.txt](analysis/binwalk/dump_binwalk.txt), [analysis/binwalk/official_binwalk.txt](analysis/binwalk/official_binwalk.txt) — 두 파일을 `diff`한 결과 **차이 없음**.

**Entropy scan (`binwalk -E`, 신규 추가 분석)**

| Offset (hex) | Offset (dec) | Edge | Dump | Official |
|---|---|---|:---:|:---:|
| `0x000000` | 0 | Falling (0.5935) | ✅ | ✅ |
| `0x00A000` | 40,960 | Rising (0.9898) | ✅ | ✅ |
| `0x012000` | 73,728 | Falling (0.5138) | ✅ | ✅ |
| `0x043000` | 274,432 | Rising (0.9944) | ✅ | ✅ |
| `0x22B000` | 2,273,280 | Falling (0.7694) | ✅ | ✅ |
| `0x230000` | 2,293,760 | Rising (0.9909) | ✅ | ✅ |
| `0x7C8000` | 8,159,232 | Falling (0.7012) | ✅ | ✅ |

📄 출처: [analysis/entropy/dump_entropy.txt](analysis/entropy/dump_entropy.txt), [analysis/entropy/official_entropy.txt](analysis/entropy/official_entropy.txt)

### ③ 분석
- Binwalk signature scan 결과, 두 이미지의 **모든 offset이 byte 단위로
  동일**합니다 — 즉 두 이미지는 Header, Loader blob, Kernel, RootFS가
  같은 위치에 배치된 동일한 구조적 골격을 가지고 있습니다.
- 신규로 수행한 entropy scan에서도 **모든 entropy edge(압축/평문 경계)가
  동일한 offset에서 발생**합니다. 이는 binwalk signature 기반 구조
  분석 결과를 독립적인 통계적 방법(byte 분포의 무작위성 측정)으로
  다시 한번 교차 검증한 것입니다.
- 마지막 falling edge(`0x7C8000` = 8,159,232)는 공식 이미지의 실제 끝
  (8,163,328 bytes)과 거의 맞닿아 있어, 압축된 실제 데이터가 그 지점
  근방에서 끝나고 이후는 낮은 entropy(=반복 패턴, 즉 erased flash)임을
  보여줍니다 — [Flash Memory Layout 비교](#-flash-memory-layout-비교)의
  trailing erased flash 판단과 정확히 부합합니다.
- 두 이미지 모두에서 별도의 device-specific partition을 암시하는 추가
  signature나 별도의 entropy 구간은 발견되지 않았습니다.

### ④ 결론
Binwalk 구조 스캔과 entropy 통계 분석이라는 **서로 다른 두 가지
방법**이 동일한 결론(같은 구조, 같은 압축/평문 경계)에 도달했습니다.
이는 두 이미지가 우연히 비슷한 것이 아니라, 실제로 동일한 빌드
파이프라인에서 만들어진 같은 firmware 임을 강하게 뒷받침합니다.

> [!IMPORTANT]
> ### 핵심 요약
> - Binwalk signature와 entropy edge가 두 이미지에서 **모두 동일한
>   offset**에 나타납니다.
> - 두 가지 독립적인 분석 방법이 같은 결론에 도달함으로써 신뢰도를
>   상호 검증했습니다.
> - 별도의 device-specific partition을 암시하는 추가 구조는 발견되지
>   않았습니다.

---

## 📦 Flash Memory Layout 비교

### ① 비교 목적
Binwalk/entropy에서 식별한 offset들을 실제 flash 메모리 맵으로
재구성하여, Bootloader/Kernel/RootFS/여백 영역이 두 이미지에서 어떻게
배치되어 있는지 비교합니다.

### ② 비교 결과

| Offset (hex) | 영역 | 크기 (bytes) | Dump | Official | 경계 산정 근거 |
|---|---|---|:---:|:---:|---|
| `0x000000` | Header / boot 영역 | 35,604 | ✅ | ✅ | Binwalk signature |
| `0x008B14` | CRC32 polynomial table | 3,916 | ✅ | ✅ | Binwalk signature |
| `0x009A60` | Gzip 압축 loader blob (Bootloader) | 232,960 | ✅ | ✅ | Binwalk signature |
| `0x042860` | LZMA 압축 Kernel | 약 1,748,736 *(추정)* | ✅ | ✅ | 다음 signature offset으로부터 추정 |
| `0x230000` | SquashFS RootFS | 5,867,940 | ✅ | ✅ | Binwalk signature + SquashFS 보고 크기 |
| `0x7C7C00` | 유효 데이터의 끝 | — | — | ✅ (공식 이미지 EOF) | 공식 파일 EOF |
| `0x7C7C00`–`0x7FFFFF` | Trailing erased flash | 225,280 | ✅ (dump만) | ❌ | Byte 검사로 `0xFF` 채움 확인 + entropy falling edge |
| 별도 Configuration/Calibration partition | — | — | ❌ 미발견 | ❌ 미발견 | 스캔 범위 내 별도 영역 없음 |

📄 출처: [docs/memory_map.md](docs/memory_map.md), [analysis/entropy/dump_entropy.txt](analysis/entropy/dump_entropy.txt)

### ③ 분석
- Header, Bootloader(loader blob), Kernel, RootFS 네 영역은 **offset,
  크기, 내용 모두 두 이미지에서 동일**합니다.
- Dump에만 존재하는 225,280 bytes는 전부 `0xFF`(erased flash)이며,
  entropy scan에서도 이 구간은 별도의 rising edge 없이 낮은 entropy로
  유지됩니다 — 즉 "숨겨진 데이터"가 아니라 **기록되지 않은 빈 flash
  공간**입니다.
- Dump 전체 크기(8,388,608 bytes = 정확히 8 MiB)는 표준 SPI NOR flash
  칩 용량과 일치하여, dump가 **칩 전체를 raw로 읽은 캡처본**임을
  뒷받침합니다.
- 공식 이미지는 정확히 실제 데이터가 끝나는 지점(`0x7C7C00`)에서
  종료되어, **실제 크기에 맞춰 packaging된 update 이미지**로 보입니다.
- Kernel 영역의 정확한 끝 경계는 다음 signature(SquashFS 시작점)로부터
  **역산 추정**한 것이며, 별도의 bootloader partition table로 확증된
  값이 아님을 명시합니다.
- 스캔된 범위 내에서 별도의 Configuration/Calibration partition은
  발견되지 않았습니다 — 이는 이 장치의 설정/calibration 데이터가 이
  flash 영역 밖(예: 별도 NVRAM 칩/영역)에 있거나, RootFS 내부의 파일로
  포함되어 있을 가능성을 시사하며 [Configuration 비교](#-configuration-비교)
  장에서 이어서 다룹니다.
  > [!NOTE]
  > **(2차 갱신)** `diffoscope` 설치 후 진행한 정밀 재분석 결과, "Loader
  > blob"으로 뭉뚱그려졌던 `0x9A60`–`0x42860` 구간 안에 실제로는 별도의
  > 미압축 레코드(`0x020000`, `hwparam.bin`과 같은 헤더 포맷)와 64KB
  > 예비 블록(`0x030000`)이 있음이 새로 확인되었습니다. 상세 내용은
  > [🔬 추가 도구 기반 교차 검증 §diffoscope](#-diffoscope)
  > 참고.

### ④ 결론
실장비 Dump는 **8 MiB SPI flash 전체를 캡처한 raw dump**이며, 공식
Firmware는 **동일한 콘텐츠를 실제 크기에 맞게 packaging한 update
이미지**입니다. 두 이미지의 실질적인 flash 콘텐츠(Header~RootFS)는
동일하고, 차이는 오직 dump에만 존재하는 trailing erased flash뿐입니다.

> [!IMPORTANT]
> ### 핵심 요약
> - Dump = 8 MiB 전체 flash 캡처, Official = 실제 크기로 packaging된
>   update 이미지.
> - Header/Bootloader/Kernel/RootFS 네 영역 모두 offset·내용 동일.
> - 유일한 차이(225,280 bytes)는 dump에만 존재하는 erased flash이며,
>   숨겨진 데이터가 아님을 entropy로 재확인.
> - 스캔 범위 내 별도 Configuration/Calibration partition은 발견되지
>   않음 (→ RootFS 비교로 이어짐).

---

## 🗂 RootFS 비교

### ① 비교 목적
SquashFS로 패키징된 RootFS 자체의 메타데이터와 파일 구성이 두 이미지
간에 실제로 동일한지, 그리고 부팅/초기화 관련 파일 구성은 어떤지
확인합니다.

### ② 비교 결과

**SquashFS Superblock 메타데이터** *(신규 추가 분석)*

| 항목 | Dump | Official |
|---|---|---|
| Compression | xz | xz |
| Block size | 131,072 | 131,072 |
| Number of inodes | 831 | 831 |
| Number of fragments | 40 | 40 |
| Number of ids | 1 | 1 |
| Creation/append time | 2025-09-22 13:53:19 | 2025-09-22 13:53:19 |
| Filesystem size | 5,867,940 bytes | 5,867,940 bytes |
| SquashFS 이미지 SHA-256 | `05e3f283…c7bbca` | `05e3f283…c7bbca` (동일) |

📄 출처: [analysis/squashfs/squashfs_superblock.txt](analysis/squashfs/squashfs_superblock.txt)

**Directory / File 통계** *(신규 추가 분석)*

| Metric | Dump | Official |
|---|---|---|
| 총 파일 수 | 415 | 415 |
| 총 디렉터리 수 | 105 | 105 |
| 총 symlink 수 | 279 | 279 |
| 총 추출 크기 (bytes) | 20,202,517 | 20,202,517 |
| 최상위 디렉터리 구성 | `bin cgibin data default dev etc home lib linuxrc mnt proc sbin sys tmp usr var` | 동일 (`diff` 결과 차이 없음) |

📄 출처: [analysis/rootfs_stats/rootfs_stats.md](analysis/rootfs_stats/rootfs_stats.md)

**BusyBox 버전 / 빌드 정보**

| 항목 | Dump | Official |
|---|---|---|
| BusyBox 버전 | v1.25.1 | v1.25.1 |
| 빌드 일시 | 2025-09-22 13:40:17 KST | 2025-09-22 13:40:17 KST |

**Binary/RootFS 내용 diff**

| 비교 항목 | 결과 |
|---|---|
| `diff -rq` (rootfs 트리 전체) | 실질적 차이 **없음** (양쪽 모두 동일한 `libgomp.so` dangling symlink 안내만 출력) |
| 파일별 SHA-256 전수 비교 | 모든 파일 동일 |

📄 출처: [analysis/diff/diff_summary.md](analysis/diff/diff_summary.md), [analysis/hashes/file_hashes.txt](analysis/hashes/file_hashes.txt)

**Init / 부팅 구성**

| 항목 | 관찰 내용 |
|---|---|
| `/etc` | 두 이미지 모두 `/tmp/etc`를 가리키는 symlink (binwalk가 안전을 위해 `/dev/null`로 재작성) |
| `/etc/inittab` | 정적 이미지에는 존재하지 않음 — 런타임에 tmpfs(`/tmp/etc`)에 생성되는 것으로 추정 |
| `/sbin/init` | ELF 실행 파일(MIPS32, 아래 [Binary 비교](#-binary-비교) 참고), 양쪽 동일 |

📄 출처: [analysis/rootfs_stats/rootfs_stats.md](analysis/rootfs_stats/rootfs_stats.md), [analysis/diff/extraction_log.txt](analysis/diff/extraction_log.txt)

### ③ 분석
- SquashFS superblock 메타데이터(압축 방식, block size, inode/fragment
  개수, 생성 시각)가 **완전히 동일**하며, 심지어 생성 시각(초 단위)까지
  일치합니다 — 이는 두 이미지의 RootFS가 재압축이나 재빌드 없이
  **동일한 빌드 산출물을 그대로 재사용**했음을 의미합니다.
- 디렉터리 수, 파일 수, symlink 수, 추출 총 크기까지 모두 동일하여,
  RootFS 수준에서 **파일이 추가/삭제/치환된 흔적이 전혀 없습니다.**
- BusyBox 빌드 시각(13:40:17)은 SquashFS 생성 시각(13:53:19)보다 약
  13분 앞서 있고, `home/httpd/build_date`(13:53:18)와는 1초 이내로
  일치합니다 — 이는 "BusyBox 컴파일 → 각 컴포넌트 빌드 → 최종 이미지
  패키징"이라는 **하나의 연속된 빌드 파이프라인**의 흔적으로 해석할 수
  있습니다.
- `/etc`가 `/tmp/etc`를 가리키는 symlink라는 점은, 이 장치가 **RootFS를
  읽기 전용으로 두고 설정 파일을 런타임에 tmpfs로 전개하는** 임베디드
  라우터의 전형적인 설계를 따른다는 것을 보여줍니다. 정적 이미지에서
  `/etc/inittab` 등을 직접 확인할 수 없는 것은 결함이 아니라 이 설계의
  자연스러운 결과입니다.
- 유일하게 출력된 diff 메시지(`libgomp.so`, `libgomp.so.1` 관련)는
  양쪽에 동일하게 존재하는 dangling symlink이며, binwalk 추출기가 안전
  때문에 재작성한 것으로 실제 내용 차이가 아닙니다.

### ④ 결론
RootFS는 메타데이터, 파일 구성, 개별 파일 내용 모두에서 **사실상
완전히 동일**하며, 빌드 타임스탬프의 정합성은 두 이미지가 같은 빌드
결과물임을 추가로 뒷받침합니다. RootFS 수준에서 식별된 유의미한 차이는
없습니다.

> [!IMPORTANT]
> ### 핵심 요약
> - SquashFS superblock, 파일/디렉터리/symlink 개수, 전체 파일 hash가
>   모두 동일 — RootFS는 사실상 **완전히 동일**.
> - BusyBox 빌드 시각과 SquashFS 생성 시각이 초 단위로 정합 → 하나의
>   빌드 파이프라인의 산출물임을 시사.
> - `/etc`는 런타임 tmpfs로 전개되는 symlink — 정적 이미지에서
>   inittab이 보이지 않는 것은 설계상 자연스러운 현상.

---

## 🧩 Binary 비교

### ① 비교 목적
RootFS 안의 실제 실행 파일(ELF 바이너리)들이 아키텍처, 헤더, 의존
라이브러리 수준에서도 동일한지 확인하고, firmware 전체의 printable
string에서도 차이가 없는지 재확인합니다.

### ② 비교 결과

**ELF Header 비교** *(신규 추가 분석 — 대표 바이너리 4종)*

| 파일 | Class | Machine | Type | Entry Point | Program Headers | Section Headers | Dump vs Official |
|---|---|---|---|---|---|---|:---:|
| `bin/busybox` | ELF32 LSB | MIPS R3000 (mips32r2) | EXEC | `0x403530` | 9 | 31 | 동일 |
| `sbin/httpd` | ELF32 LSB | MIPS R3000 (mips32r2) | EXEC | `0x401c80` | 9 | 32 | 동일 |
| `sbin/init` | ELF32 LSB | MIPS R3000 (mips32r2) | EXEC | `0x400c70` | 9 | 27 | 동일 |
| `lib/libuClibc-0.9.33.so` | ELF32 LSB | MIPS R3000 (mips32r2) | DYN (공유 라이브러리) | `0xb550` | — | — | 동일 |

📄 출처: [analysis/elf/elf_header_comparison.txt](analysis/elf/elf_header_comparison.txt)

> `lib/libc.so`는 실제 ELF가 아니라 uClibc 툴체인 표준 방식의 GNU ld
> **linker script**(`GROUP ( libc.so.0 uclibc_nonshared.a ... )`)입니다
> — 정상적인 uClibc 구성입니다.

**Dynamic Section (NEEDED 라이브러리)**

| 바이너리 | NEEDED 라이브러리 (dump 기준, official과 동일) |
|---|---|
| `bin/busybox` | `libcrypt.so.0`, `libm.so.0`, `libc.so.0` |
| `sbin/httpd` | `libelog.so`, `libsha256.so`, `libgcc_s.so.1`, `libc.so.0` |

**Binary Metadata (Build ID / strip 여부)**

| 파일 | Build ID (SHA1) | Strip 여부 |
|---|---|---|
| `bin/busybox` | `84d7027c8ecc015453998bc1751f6eaa14e6af84` | Stripped |
| `sbin/init` | `5cb231a1497dc55a10eddbc3e64472c1c5ccffb0` | Stripped |

📄 출처: [analysis/elf/elf_header_comparison.txt](analysis/elf/elf_header_comparison.txt) (Build ID는 두 이미지에서 동일한 값으로 확인됨 — 파일 SHA-256이 이미 동일하므로 당연한 결과이나, 대표 파일에 대해 재확인)

**Firmware 전체 Strings 비교**

| 항목 | 결과 |
|---|---|
| 총 라인 수 | 2,020줄 (양쪽 동일) |
| 차이 라인 수 | 2줄 |
| 차이 위치 | 모두 Bootloader/loader blob 영역(`0x9A60`) 내부 |
| 버전 배너 / 빌드 날짜 / URL / credential 차이 | 없음 |

📄 출처: [analysis/strings/dump_strings.txt](analysis/strings/dump_strings.txt), [analysis/strings/official_strings.txt](analysis/strings/official_strings.txt)

### ③ 분석
- 대표적으로 선정한 4개 바이너리(`busybox`, `httpd`, `init`,
  `libuClibc-0.9.33.so`)의 ELF Header, Program Header, Dynamic Section이
  **모두 동일**합니다. 전체 RootFS가 이미 파일 단위 hash로 동일함이
  확인되었으므로 이는 예상된 결과이지만, 실제 헤더 수준까지 내려가
  검증함으로써 "hash가 같다"는 결과를 아키텍처/링킹 정보 수준에서도
  **교차 확인**한 것입니다.
- 아키텍처는 **MIPS32 (mips32r2, little-endian, o32 ABI)**이며,
  `uClibc` 기반 동적 링킹을 사용합니다 — 가정용 라우터에서 흔히
  사용되는 임베디드 MIPS SoC 구성과 일치합니다.
- `busybox`, `init` 등 주요 바이너리는 **stripped**되어 있어 디버그
  심볼이 제거된 상태입니다 — 이는 상용 펌웨어의 일반적인 배포 방식이며,
  두 이미지에서 동일하게 나타나 이 역시 특별한 차이점은 아닙니다.
- Firmware 전체 strings 비교에서 차이가 발견된 2줄은 모두 이미
  [Binwalk & Entropy 비교](#-binwalk--entropy-비교)에서 식별된 재압축
  loader blob 영역 내부에 위치합니다 — 즉 바이너리 레벨 분석과 strings
  레벨 분석이 **동일한 영역을 가리키는 일관된 결과**를 보여줍니다.

### ④ 결론
바이너리 수준(ELF Header, Program Header, Dynamic Section, Build ID)과
텍스트 수준(strings) 모두에서 실질적인 차이는 발견되지 않았습니다.
발견된 유일한 문자열 차이도 이미 알려진 재압축 loader blob 내부에
국한되어 있어, 실행 코드 자체에는 어떠한 변경도 없다는 결론을 다시 한번
뒷받침합니다.

> [!IMPORTANT]
> ### 핵심 요약
> - 대표 바이너리 4종의 ELF Header/Program Header/Dynamic Section이
>   모두 동일 — MIPS32 mips32r2, uClibc 동적 링킹 구성.
> - 주요 실행 파일은 stripped 상태이며, 이는 양쪽에서 동일해 특별한
>   차이가 아님.
> - Firmware 전체 strings 비교(2,020줄 중 2줄 차이)도 이미 알려진
>   loader blob 재압축 영역에 국한됨 — 새로운 차이 없음.

---

## ⚙ Configuration 비교

### ① 비교 목적
장치별 설정(configuration) 파일과 calibration/MAC 주소 데이터가 두
이미지 간에 어떻게 존재하는지, 그리고 이것이 "장치 고유값"인지
"공장 기본값(factory default) 템플릿"인지를 구분합니다.

### ② 비교 결과

**Configuration 파일 비교**

| 항목 | 결과 |
|---|---|
| `default/etc/econf/*` (DHCP, interface, wireless, DNS 등) | 두 이미지 간 SHA-256 완전 동일 |
| `default/etc/econf/node.default` | 동일 — 무선 기본 SSID `ipTIME_MESH` 등 **공장 기본값** 포함 |
| `default/etc/econf/interface.wan1.conf` | 동일 — WAN 기본 타입 `dhcp`, MTU 1500 등 기본 설정 |

📄 출처: [analysis/hashes/file_hashes.txt](analysis/hashes/file_hashes.txt)

**Calibration / MAC 주소 영역 (`default/hwparam/hwparam.bin`)** *(신규 추가 분석)*

| 항목 | Dump | Official |
|---|---|---|
| 크기 | 16,384 bytes | 16,384 bytes |
| SHA-256 | `af79b580…f4d` | `af79b580…f4d` (동일) |

```
00000000: 4836 3031 1394 0190 9f33 0011 0046 544d  H601.....3...FTM
00000010: 0000 0090 9f33 0011 0092 9f33 0011 0092  .....3.....3....
00000020: 9f33 0111 0092 9f33 0211 0000 e04c 8196  .3.....3.....L..
00000030: c500 e04c 8196 c600 e04c 8196 c700 e04c  ...L.....L.....L
```

📄 출처: [analysis/config/hwparam_analysis.md](analysis/config/hwparam_analysis.md)

### ③ 분석
- `default/etc/econf/` 아래 설정 파일들은 두 이미지에서 완전히
  동일하며, 내용을 열어보면 실사용자 값이 아니라 `ipTIME_MESH` 같은
  **공장 기본값(factory default)** 임을 알 수 있습니다. 파일 경로가
  `default/` 아래에 있다는 점 자체가 이것이 "기본 템플릿"임을 이름으로도
  보여줍니다.
- `hwparam.bin`에는 `"H601"` 모델 계열 태그, `"FTM"` 마커, 그리고
  `e0:4c:81:96:c5:00` → `...c6:00` → `...c7:00`처럼 **마지막 옥텟이
  순차적으로 증가하는 6바이트 그룹**이 반복됩니다. 이는 LAN/WAN/Wi-Fi
  대역 등 여러 인터페이스에 순차 할당되는 **MAC 주소 블록 구조와
  일치하는 패턴**입니다. *(어느 벤더의 OUI인지는 본 분석에서 확정하지
  않으며, 바이트 구조상의 관찰로만 제시합니다.)*
- 이 파일이 dump와 공식 이미지에서 **byte 단위로 완전히 동일**하다는
  점은 언뜻 "장치 고유 설정이 없다"는 뜻으로 오해할 수 있지만, 실제로는
  그 반대의 의미로 해석해야 합니다: 이 파일은 `default/` 경로, 즉
  **모든 개체(unit)가 공유하는 SquashFS RootFS 안에 박혀 있는 공장
  출하 시 템플릿**이기 때문에 두 이미지에서 같은 것이 당연합니다.
  실제 장치 고유의 MAC 주소나 calibration 값은 이 SquashFS 밖의 별도
  writable 영역(예: 전용 NVRAM)에 저장되는 것이 임베디드 라우터의
  일반적인 설계이며, 이는 [Flash Memory Layout 비교](#-flash-memory-layout-비교)에서
  스캔 범위 내에 별도 partition이 발견되지 않은 것과도 일관됩니다.
  > [!NOTE]
  > **(2차 갱신)** `diffoscope` 정밀 재분석 결과, 위 문단의 "스캔 범위
  > 내에 별도 partition 없음"이라는 전제는 부분 수정이 필요합니다 —
  > raw flash 절대offset `0x020000`에 `hwparam.bin`과 같은 헤더 포맷을
  > 가지지만 **일부 필드 값이 dump·official 간에 실제로 다른** 별도
  > 레코드가 발견되었습니다. 이 레코드가 진짜 장치별 calibration 슬롯인지
  > 여부는 추정 수준이며, 상세 근거는
  > [🔬 추가 도구 기반 교차 검증 §diffoscope](#-diffoscope)
  > 참고.

### ④ 결론
스캔된 flash 범위 안에서 확인 가능한 Configuration/Calibration
데이터는 모두 **장치 고유값이 아니라 공장 기본값 템플릿**이며, 두
이미지에서 동일한 것이 자연스럽습니다. 이 사실은 "장치별 실제 설정이
없다"가 아니라, "장치별 실제 설정은 이 비교 대상 범위 밖에 저장된다"는
의미로 해석해야 합니다.

> [!IMPORTANT]
> ### 핵심 요약
> - `econf/*` 설정과 `hwparam.bin`은 두 이미지에서 완전히 동일하지만,
>   이는 모두 `default/` 경로의 **공장 기본값 템플릿**이기 때문입니다.
> - `hwparam.bin`에는 MAC 주소 구조와 일치하는 순차적 6바이트 패턴이
>   존재하지만, 특정 벤더 OUI로 단정하지는 않습니다 (추정).
> - 장치 고유의 실제 MAC/calibration 값은 이 SquashFS 밖의 별도
>   영역에 있을 것으로 추정되며, 본 분석 범위에서는 확인되지 않습니다.

---

## 📖 종합 분석

지금까지의 모든 비교 결과를 하나의 표로 정리합니다.

| 비교 항목 | 결과 | 근거 |
|---|---|---|
| File Size | 다름 (225,280 bytes 차이, 고정값) | §Firmware 정보 비교 |
| Hash (SHA-256/MD5) | 다름 (전체 파일 기준) | §Firmware 정보 비교 |
| File Type | 동일 (`data`) | §Firmware 정보 비교 |
| 내부 버전 문자열 | 동일 (`15.258`) | §Firmware 정보 비교 |
| Binwalk Signature | 동일 | §Binwalk & Entropy 비교 |
| Entropy 경계 | 동일 | §Binwalk & Entropy 비교 |
| Bootloader / Loader Blob | gzip 스트림 자체는 압축 byte·해제 결과 모두 동일; 그 뒤 미압축 영역에 일부 필드가 다른 레코드 + 채움값만 다른 64KB 블록 존재 *(2차 갱신)* | §Flash Memory Layout 비교, §추가 도구 기반 교차 검증 ① |
| Kernel | 동일 (byte 단위) | §Flash Memory Layout 비교 |
| RootFS (SquashFS 이미지) | 동일 (byte 단위, 2개 독립 추출기로 교차 검증) | §Flash Memory Layout / RootFS 비교, §추가 도구 기반 교차 검증 ② |
| Flash 여백 (Trailing erased flash) | **Dump에만 존재** (225,280 bytes, `0xFF`) | §Flash Memory Layout 비교, §추가 도구 기반 교차 검증 ⑤ |
| Post-SquashFS tail *(신규 식별)* | 동일 (1,628 bytes, 전부 `0x00`) | §추가 도구 기반 교차 검증 ① |
| Loader blob 내부 `0x020000` 레코드 *(신규 발견)* | `hwparam.bin`과 같은 헤더 포맷이나 MAC-like 그룹·숫자열 등 일부 필드가 실제로 **다름** *(추정: 장치별/빌드별 슬롯 가능성)* | §추가 도구 기반 교차 검증 ①③ |
| Loader blob 내부 `0x030000` 64KB 블록 *(신규 발견)* | dump=`0xFF`, official=`0x00` — 내용 없는 예비 섹터로 판단 | §추가 도구 기반 교차 검증 ①⑤ |
| 별도 Configuration/Calibration Partition | 스캔 범위 내에서 기존에는 **미발견** → diffoscope 재분석으로 위 `0x020000` 레코드를 **부분적으로 재발견** (성격은 추정) *(2차 갱신)* | §Flash Memory Layout 비교, §추가 도구 기반 교차 검증 ① |
| SquashFS Metadata | 동일 | §RootFS 비교 |
| Directory Structure / File Count | 동일 (415 files, 105 dirs, 279 symlinks — sasquatch로도 동일하게 재현) | §RootFS 비교, §추가 도구 기반 교차 검증 ② |
| BusyBox 버전/빌드일시 | 동일 (v1.25.1, 2025-09-22 13:40:17 KST) | §RootFS 비교 |
| Init 구성 (`/etc`) | 동일 — 런타임 tmpfs symlink 구조 (sasquatch로 `/etc→/tmp/etc` 원본 대상 직접 확인) | §RootFS 비교, §추가 도구 기반 교차 검증 ② |
| ELF Header / Program Header / Dynamic Section | 동일 (readelf, rabin2 두 도구로 교차 확인) | §Binary 비교, §추가 도구 기반 교차 검증 ④ |
| Binary Metadata (Build ID, strip) | 동일 | §Binary 비교 |
| Strings (firmware 전체) | 거의 동일 (2,020줄 중 2줄, loader blob 내부) | §Binary 비교 |
| `httpd` 위험 함수 import (`strcpy`/`sprintf`/`execve` 등) *(신규 확인)* | dump·official 동일 존재 — 정적 분석상 추가 검토 대상 (취약점 확정 아님) | §추가 도구 기반 교차 검증 ④ |
| Configuration 파일 (`econf/*`) | 동일 (공장 기본값 템플릿) | §Configuration 비교 |
| Calibration/MAC 데이터 (`hwparam.bin`, SquashFS 내부) | 동일 (공장 기본값 템플릿, byte 단위) | §Configuration 비교 |

---

## 🔬 추가 도구 기반 교차 검증

> [!NOTE]
> 이전 버전 보고서는 `diffoscope`, `sasquatch`, `vbindiff`, `rizin`/`radare2`,
> `ent`가 설치되어 있지 않아 이 절이 "⚠ 한계"로 남아 있었습니다. 이번에
> WSL 환경에 해당 도구를 모두 설치(`rizin`은 패키지가 없어 `radare2`로
> 대체)하고 실제로 실행한 결과를 아래에 정리합니다. 각 절은 기존 장과
> 동일하게 **① 목적 → ② 결과(표) → ③ 분석 → ④ 결론** 흐름을 따릅니다.
> 원본 산출물은 `analysis/diffoscope/`, `analysis/sasquatch/`,
> `analysis/vbindiff/`, `analysis/radare2/`, `analysis/ent/`에 저장했습니다.

### ① diffoscope

**목적** — 기존 결론("실질적인 차이는 trailing erased flash 및 loader
재압축 아티팩트에 국한됨")을, byte 단위를 넘어 컨테이너 포맷까지 인식하는
deep-diff 도구로 검증합니다. 전체 파일 비교(180초 내 완료)와, 5개
영역(header/boot, loader blob, kernel, SquashFS rootfs, trailing 영역에
대응하는 post-squashfs tail)별 비교를 모두 수행했습니다.

**결과**

| 영역 | Offset 범위 | 크기 (bytes) | diffoscope 결과 |
|---|---|---|---|
| Header/boot | `0x000000`–`0x009A60` | 39,520 | 동일 |
| Loader blob | `0x009A60`–`0x042860` | 232,960 | **차이 있음** — 아래 참고 |
| Kernel | `0x042860`–`0x230000` | 2,021,280 | 동일 |
| SquashFS rootfs | `0x230000`–`0x7C89A4` | 5,867,940 | 동일 |
| Post-SquashFS tail *(신규 식별)* | `0x7C89A4`–`0x7C9000` | 1,628 | 동일 (전부 `0x00`) |
| Trailing erased flash | `0x7C9000`–`0x800000` | 225,280 | 공식 이미지에 대응 데이터 없음(dump 전용, 전부 `0xFF`) |

📄 출처: [analysis/diffoscope/README.md](analysis/diffoscope/README.md), [analysis/diffoscope/identical_regions.txt](analysis/diffoscope/identical_regions.txt)

**분석**

- diffoscope는 `loader_blob` 조각을 gzip 컨테이너로 인식해 자동
  압축 해제를 시도했으나 `exit code 2 (No output)`로 실패했습니다 — 이는
  우리가 "loader blob 영역"이라 불러온 232,960 bytes 전체가 **하나의
  gzip 스트림이 아니라는 신호**였습니다.
- `zlib`으로 직접 스트림 경계를 추적한 결과, 실제 gzip 스트림은
  `0x009A60`에서 시작해 **`0x0126A0`에서 끝났습니다**(압축 35,904
  bytes → 압축 해제 101,264 bytes). **이 gzip 스트림 자체(압축 바이트,
  압축 해제 결과 모두)는 dump·official에서 완전히 동일**했습니다.
- `0x0126A0`부터 kernel 시작(`0x042860`)까지 197,056 bytes는 지금까지
  "loader blob(재압축)"으로 뭉뚱그려 다뤄졌지만, 실제로는 다음과 같이
  세분화됩니다.

  | Sub-offset 범위 | 크기 | dump vs official |
  |---|---|---|
  | `0x0126A0`–`0x020000` | 55,648 | 동일 (거의 전부 `0xFF` padding) |
  | `0x020000`–`0x021400` | 5,120 | **부분적으로 다름** (`hwparam.bin`과 같은 헤더 포맷의 레코드) |
  | `0x021400`–`0x030000` | 60,416 | 동일 (거의 전부 `0x00` padding) |
  | `0x030000`–`0x040000` | 65,536 | **완전히 다름** — dump는 전부 `0xFF`, official은 전부 `0x00` (64KB 예비 블록) |
  | `0x040000`–`0x042860` | 10,336 | 동일 (이미지 메타데이터 태그 `"n602sr"`, `"15.258"`, `"kernel"` 포함) |

- `0x020000` 레코드는 `default/hwparam/hwparam.bin`(SquashFS 내부, 공장
  기본 템플릿)과 **동일한 헤더 태그**(`H601` + `13 94 01`)로 시작하지만,
  그 직후 MAC 주소 형태의 6바이트 그룹이 dump(`b0:38:6c:52/53/54:fe:c0`
  계열)와 official(`90:9f:33:00/01/02:11:00` 계열)에서 **서로 다릅니다.**
  반면 그 뒤에 이어지는 `e0:4c:81:96:c5/c6/c7:00` 시퀀스는 dump·official
  동일하며, 이는 이미 `default/hwparam/hwparam.bin`에서 본 값과 같습니다.
  `0x020800` 부근의 ASCII 숫자열도 dump(`"...59107866..."`)와
  official(`"...12684564..."`)이 다릅니다.
- `0x030000`–`0x040000`의 64KB는 dump=`0xFF`(소거된 미기록 flash),
  official=`0x00`(0으로 채운 placeholder)로, **내용이 있는 데이터가
  아니라 "비어 있음"을 표현하는 convention만 다른 예비 섹터**로
  판단됩니다 (entropy도 0에 가까움 — §ent 참고).
- kernel과 SquashFS rootfs가 byte 단위로 완전히 동일하다는 기존 결론은
  diffoscope로도 **다시 확인**되었습니다.

**결론** — 기존 결론("차이는 trailing erased flash와 loader 재압축
아티팩트에 국한")은 **큰 틀에서는 유지**되지만, "재압축 아티팩트"라는
설명 하나로는 부족했습니다. diffoscope 기반 정밀 분석으로 loader blob
영역 내부에 (1) 완전히 동일한 gzip 스트림, (2) `hwparam.bin`과 같은
포맷이지만 일부 필드가 실제로 다른 별도 레코드, (3) 채움 값만 다른
64KB 예비 블록이 섞여 있음을 새로 확인했습니다 — 결론을 **뒤집지는
않지만 원인 설명을 더 정확하게 교정**합니다.

---

### ② sasquatch

**목적** — 지금까지의 RootFS 비교는 binwalk에 내장된 SquashFS 추출기
결과에 의존했습니다. 독립 실행형 `sasquatch`로 같은 이미지를 다시
추출해, RootFS 동일성 결론이 특정 추출기에 의존한 결과가 아님을
검증합니다.

**결과**

| 항목 | binwalk 내장 추출기 (기존) | sasquatch (신규) |
|---|---|---|
| Dump: 파일 / 디렉터리 / symlink | 415 / 105 / 279 | 415 / 105 / 279 |
| Official: 파일 / 디렉터리 / symlink | 415 / 105 / 279 | 415 / 105 / 279 |
| RootFS 전체 tree hash *(주: 파일별 SHA-256 목록을 다시 SHA-256)* | `006ac8db…e93` | `006ac8db…e93` (4가지 조합 모두 동일) |
| `diff -rq --no-dereference` (sasquatch: dump vs official) | — | 차이 없음 (exit 0) |
| symlink 대상 처리 | 안전하지 않은 대상은 `/dev/null`로 재작성 | 원본 대상 문자열 그대로 보존 |

📄 출처: [analysis/sasquatch/README.md](analysis/sasquatch/README.md), [analysis/sasquatch/counts_and_treehash.txt](analysis/sasquatch/counts_and_treehash.txt)

**분석**

- 두 개의 **서로 다른 구현체**로 같은 이미지를 추출했을 때 정규 파일
  tree hash가 완전히 일치한다는 것은, RootFS 동일성 결론이 추출기
  버그·우연에 기인한 것이 아니라는 강력한 교차 검증입니다.
- sasquatch는 안전을 위한 재작성 없이 symlink 원본 대상을 그대로
  보여주므로, 기존 보고서가 "추정"으로 표기했던 `/etc → /tmp/etc`
  런타임 tmpfs 리다이렉트를 **직접적인 근거로 승격**시켰습니다. 추가로
  `/var → /tmp/var`, `/mnt → /tmp/mnt`도 같은 패턴임을 새로 확인했고,
  `/sbin/checkbootparam`, `/sbin/flash`, `/sbin/nvshow`, `/sbin/phy`,
  `/sbin/rtl`이 모두 `/sbin/freebox`를 가리키는 busybox류 multi-call
  패턴도 확인했습니다 — 전부 dump·official 동일하며 의심할 이유가
  없는 정상적인 구성입니다.

**결론** — sasquatch 기반 재추출은 "RootFS는 사실상 완전히 동일하다"는
기존 결론을 **강화**했습니다. 유일한 차이(symlink 재작성 여부)는 도구의
안전장치 차이일 뿐, firmware 내용의 차이가 아닙니다.

---

### ③ vbindiff / cmp / xxd

**목적** — `vbindiff`는 ncurses 기반 대화형 전용 도구라 완전 자동화가
불가능합니다. `tmux`로 실제 키 입력을 보내 화면을 캡처하는 방식으로
실제 실행 결과를 확보하고, `cmp -l`/`xxd`/`hexdump -C`로 교차 검증하여
최초 차이 offset·차이 구간·차이 패턴을 사람이 읽을 수 있는 형태로
정리합니다.

**결과**

| 항목 | 값 |
|---|---|
| `cmp` 최초 차이 위치 | byte 131,080 (1-indexed) = `0x020007` |
| `cmp -l` 총 차이 byte 수 (겹치는 구간 내) | 65,689 bytes |
| `cmp -l` 차이 구간 수 | 13개 연속 구간 |
| diffoscope 분석과의 일치 여부 | **정확히 일치** (65,689 bytes, 같은 13개 구간) |
| `vbindiff` 실행 | tmux로 세션 구동, `G` 키로 offset 이동 후 화면 캡처 성공 |

📄 출처: [analysis/vbindiff/README.md](analysis/vbindiff/README.md), [analysis/vbindiff/cmp_l_summary.txt](analysis/vbindiff/cmp_l_summary.txt), [analysis/vbindiff/vbindiff_screen_loader_blob_diff.txt](analysis/vbindiff/vbindiff_screen_loader_blob_diff.txt)

**분석**

- `cmp -l`이 집계한 차이 byte 수(65,689)와 차이 구간이 diffoscope
  분석 결과와 **정확히 일치**하여, 서로 다른 두 도구가 같은 사실에
  도달했음을 재확인했습니다.
- hex를 사람이 직접 보면 세 가지 패턴이 뚜렷이 구분됩니다: **①**
  `H601`+헤더 태그처럼 구조(레코드 포맷)는 동일하고, **②** 그 안의
  특정 필드(선두 MAC 그룹, ASCII 숫자열)만 실제 값이 다르며, **③**
  완전히 빈 여백 구간(`0x030000`–`0x040000`)은 채움 값(`0xFF`/`0x00`)만
  다릅니다. `vbindiff` 화면 캡처에서도 이 세 패턴이 그대로 나타나
  실제 대화형 도구 실행으로도 같은 결론을 육안으로 확인할 수 있었습니다.

**결론** — vbindiff는 완전 자동화가 불가능했지만, tmux 기반 실제 실행 +
cmp/xxd/hexdump 교차 검증으로 목표를 달성했습니다. 여러 도구가 동일한
차이 목록에 도달한 것은 이번 분석 결과가 도구 종류에 좌우되지 않는
재현 가능한 사실임을 뒷받침합니다.

---

### ④ radare2 / rabin2

**목적** — `rizin`이 본 환경에 없어 `radare2`/`rabin2`로 대체해,
`sbin/httpd`, `bin/busybox`, `sbin/init` 세 바이너리를 dump·official
양쪽에서 아키텍처·entry point·import·문자열·section 수준까지
교차 검증하고, `httpd`에서 보안 관점의 관심 함수/문자열을 확인합니다.

**결과**

| 바이너리 | SHA-256 (dump = official) | `rabin2 -I/-e/-l/-i/-z/-S` dump vs official |
|---|---|---|
| `sbin/httpd` | `22fb1f9a…9fae3` | 전부 동일 |
| `bin/busybox` | `48325224…184fb6` | 전부 동일 |
| `sbin/init` | `7762db5d…4bcc797` | 전부 동일 |

| 바이너리 | Entry point (rabin2) | 기존 readelf 결과와 일치 여부 |
|---|---|---|
| `sbin/httpd` | `0x00401c80` | 일치 |
| `bin/busybox` | `0x00403530` | 일치 |
| `sbin/init` | `0x00400c70` | 일치 |

📄 출처: [analysis/radare2/README.md](analysis/radare2/README.md)

**분석**

- 세 바이너리 모두 rabin2의 6가지 출력(`-I`, `-e`, `-l`, `-i`, `-z`,
  `-S`)이 dump·official 간 **완전히 동일**했으며, entry point 값도
  기존 `readelf` 기반 분석과 정확히 일치했습니다 — 서로 다른 두 도구가
  같은 결론에 도달한 세 번째 교차 검증입니다.
- `httpd` compiler 문자열(`Realtek MSDK-4.8.5p1 Build 2536`)은 SoC가
  Realtek 계열임을 시사하며, sasquatch 분석에서 확인한 `/dev/rtl865x`,
  `/sbin/rtl → /sbin/freebox`와도 일관됩니다.
- `httpd`의 `rabin2 -i`(import 심볼)에서 `strcpy`, `strcat`, `sprintf`,
  `memcpy`, `getenv`, `execve`, `execl`이 확인되었고, `-z`(strings)에서
  `application/x-httpd-cgi`, `SERVER_ADMIN`, `CgiLog`, `CGIPath`,
  `"/login/login.cgi"` 등 CGI/인증 관련 문자열이 확인되었습니다
  (dump·official 동일). `system`, `popen`, `vsprintf`는 import 목록에
  없었습니다.

**보안적 의미** — `httpd`가 길이를 검사하지 않는 문자열 함수
(`strcpy`/`strcat`/`sprintf`)와 외부 프로세스 실행 함수
(`execve`/`execl`), CGI 환경변수 조회 함수(`getenv`)를 함께 import하고
있다는 사실은 CGI 요청 처리 경로에 사용자 입력이 흘러들어갈 수 있는
지점이 있음을 **암시**합니다. 다만 이는 **정적으로 import된 심볼이
존재한다는 사실**일 뿐이며, 실제 호출부의 길이 검증 여부나 사용자
입력이 실제로 해당 함수까지 도달하는지(source→sink 흐름)는 이번 정적
비교 범위를 벗어납니다. 따라서 **"취약점 확인"이 아니라 "정적 분석상
추가 검토 대상"**으로 분류합니다. 또한 이 함수들은 dump·official
양쪽에 동일하게 존재하므로, dump에서 새로 추가된 위험이 아니라 이
firmware 릴리스(v15.258) 자체에 공통된 특성입니다.

**결론** — radare2/rabin2 분석은 대표 바이너리 3종에서 새로운 차이를
전혀 발견하지 못해, 기존 "Binary 비교" 장의 결론을 세 번째 독립
도구로 재확인했습니다. `httpd`의 위험 함수 import는 후속 정적 분석
대상으로 기록하되, 확정된 취약점으로 표현하지 않습니다.

---

### ⑤ ent

**목적** — 기존 `binwalk -E` 기반 entropy edge 비교를 독립적인 도구로
재확인하고, 특히 trailing erased flash 영역이 실제로 낮은 entropy /
`0xFF` 반복 패턴인지, 그리고 diffoscope에서 새로 발견한 영역들의
entropy 특성은 어떤지 확인합니다.

**결과**

| 영역 | Dump entropy (bits/byte) | Official entropy (bits/byte) | 비고 |
|---|---|---|---|
| 전체 파일 | 7.886575 | 7.963426 | dump는 trailing erased flash가 섞여 약간 낮음 |
| Header/boot | 5.173703 | 5.173703 | 동일 |
| Loader blob (전체 232,960 bytes) | 2.933242 | 2.878421 | **다름** — 압축 스트림 + 레코드 + 예비 블록이 섞여 있어 재압축·필드값 차이가 반영됨 |
| Kernel | 7.991305 | 7.991305 | 동일 |
| SquashFS rootfs | 7.999937 | 7.999937 | 동일 |
| Post-SquashFS tail (1,628 bytes) | 0.000000 | 0.000000 | 동일 — 전부 `0x00` |
| Trailing erased flash (225,280 bytes, dump 전용) | 0.000000 | — (해당 없음) | 전부 `0xFF` (byte 히스토그램으로 재확인, unique value 1개) |

📄 출처: [analysis/ent/README.md](analysis/ent/README.md), [analysis/ent/ent_full.txt](analysis/ent/ent_full.txt), [analysis/ent/ent_regions.txt](analysis/ent/ent_regions.txt)

**분석**

- Header/boot, kernel, SquashFS rootfs, post-squashfs tail은 dump와
  official에서 entropy 값이 **소수점까지 완전히 동일**합니다 — 이미
  byte 단위 동일성이 확인된 영역에 대해 독립적인 통계 지표로도 같은
  결론에 도달한 것입니다.
- loader blob 전체의 entropy가 dump·official 간에 다르게 나온 것은
  diffoscope 분석에서 밝힌 것처럼 이 영역이 (a) 완전히 동일한 gzip
  스트림, (b) 일부 필드만 다른 레코드, (c) 채움 값이 다른 64KB 블록의
  혼합이기 때문이며, entropy 하나만으로는 이 세 가지를 구분할 수
  없다는 것도 함께 확인했습니다 — 즉 entropy 비교는 "다르다/같다"를
  빠르게 스크리닝하는 데는 유용하지만, **원인 규명에는 diffoscope 같은
  구조 인식 도구가 추가로 필요하다**는 방법론적 시사점을 얻었습니다.
- trailing erased flash는 entropy 0, byte 히스토그램상 고유 값이
  `0xFF` 하나뿐임을 재확인했습니다 — "숨겨진 데이터"가 아니라 완전히
  비어 있는 flash 영역이라는 기존 결론을 다시 뒷받침합니다.

**보안적 의미** — entropy가 0에 가깝고 byte 값이 단일값으로 반복되는
영역(trailing erased flash, post-squashfs tail, 64KB 예비 블록)은
구조적으로 **암호화되었거나 난독화된 추가 payload를 숨기기에 부적합한
형태**입니다 (암호화/압축된 데이터라면 entropy가 7~8 bits/byte에
가깝게 나타나야 함). 따라서 이 영역들에 숨겨진 설정값이나 장치별
비밀 데이터가 있을 가능성은 낮다고 판단합니다. 반대로 loader blob
내부의 `0x020000` 레코드처럼 entropy가 중간값이면서 dump·official
간에 실제로 값이 다른 영역은, 구조화된 실제 콘텐츠(계산된 필드값)를
담고 있을 가능성이 있는 지점으로 볼 수 있습니다 *(추정)*.

**결론** — ent 기반 정밀 entropy 분석은 기존 binwalk entropy 비교
결론을 독립적으로 재확인했고, loader blob 영역이 다르게 나온 이유가
diffoscope 분석과 정합적으로 설명됨을 확인했습니다. trailing erased
flash·post-squashfs tail이 "비어 있음"이라는 기존 결론도 재확인했습니다.

---

### 잔여 한계

> [!WARNING]
> 도구를 모두 설치한 뒤에도 정적 파일 비교라는 방법론 자체의 한계로
> 인해 아래 사항은 여전히 확인하지 못했습니다.

- 🧩 `rizin`은 본 환경에 패키지가 없어 설치하지 못했고, 대신 `radare2`/
  `rabin2`로 동등한 분석(파일 정보, entry point, import, strings,
  section)을 수행했습니다. `rizin` 고유 기능(예: `rz-diff`)으로 재검증한
  것은 아닙니다.
- 🔑 diffoscope 분석으로 새로 발견한 `0x020000` 레코드가 **실제
  장치별/빌드별 calibration·MAC 슬롯인지, 아니면 다른 목적의 값인지는
  확정할 수 없습니다** — 정적 비교만으로는 이 필드가 어떻게 채워지고
  어떻게 사용되는지 알 수 없으며, 이는 "추정"으로 남겨둡니다. 또한
  official 다운로드 이미지에 담긴 값이 "모든 배포본에 공통인 고정
  placeholder"인지, 아니면 특정 빌드/유닛의 값이 우연히 남은 것인지도
  확인하지 못했습니다.
- 🔒 펌웨어 업그레이드 도구/부트로더가 이 레코드나 64KB 예비 블록이
  위치한 섹터를 실제 플래싱 시 보존(skip)하는지 여부는 본 정적 분석만
  으로는 확인할 수 없습니다.
- 🚫 여전히 dynamic/runtime 분석은 수행하지 않았습니다 — `httpd`의
  위험 함수 import가 실제로 어떤 입력에 어떻게 반응하는지, `/tmp/etc`
  런타임 설정의 실제 값, NVRAM의 실제 MAC/calibration 값은 이번 분석
  범위 밖입니다.
- 🗺 Kernel 영역의 정확한 끝 경계 등 일부 flash 영역 경계는 여전히
  다음 signature로부터의 **추정**이며, 별도 partition table로 확정된
  값이 아닙니다.

---

## 🗣 분석자 의견

> [!NOTE]
> 이 절은 지금까지의 근거 기반 비교 결과와 달리, 분석자의 개인적인
> 해석과 판단을 담습니다. 본문의 다른 절과 달리 "추정"보다도 더 주관적인
> 의견이 포함될 수 있습니다.

이번 작업은 단순히 "두 파일이 같다/다르다"를 가리는 것이 아니라, **실장비
dump라는 결과물 자체의 신뢰성을 검증하는 과정**이라는 데 더 큰 의미가
있다고 생각합니다. 하드웨어에서 직접 뽑아낸 dump가 공식 배포 파일과
바이트 단위로 거의 동일하다는 것은 "이 장비가 순정 상태였다"는 결론
못지않게, "이번에 사용한 dump 채취·분석 파이프라인 자체가 신뢰할 만하다"
는 것을 함께 증명합니다 — 둘 중 하나가 잘못됐다면 이렇게 깨끗하게
맞아떨어지기 어렵기 때문입니다.

공식 펌웨어와 실장비 dump가 (loader blob 내부의 몇백 바이트를 제외하면)
사실상 동일하다는 이번 결론은, 앞으로 이 장치의 CVE·취약점 분석을 실장비
없이 **공식 배포 펌웨어만으로 진행해도 실제 장비와의 괴리가 크지 않을
가능성이 높다**는 것을 시사합니다. 이는 실무적으로 꽤 중요한데, 실장비를
매번 분해해서 SPI flash를 덤프하지 않고도 공식 다운로드 파일만으로
대부분의 정적 분석(바이너리, 설정, RootFS 구조)을 신뢰성 있게 수행할 수
있다는 뜻이기 때문입니다.

다만 이번 분석은 어디까지나 **정적 파일 비교**이며, 그 자체로 취약점의
유무를 증명하지는 않습니다. `httpd`에서 확인한 `strcpy`/`sprintf`/
`execve` 같은 함수들이 실제로 안전하게 쓰이는지는 (1) `/tmp/etc`에 실제로
전개되는 런타임 설정값, (2) NVRAM에 저장된 실제 장치별 값, (3) 웹 요청이
CGI로 전달되는 처리 흐름, (4) 그 흐름 속에서 이 위험 함수들이 실제로
호출되는 경로를 함께 봐야 판단할 수 있는 문제입니다. 정적 비교만으로는
이 네 가지 중 어느 것도 확인할 수 없습니다.

개인적인 판단으로는, 다음 단계로는 여러 바이너리를 넓게 훑기보다
**`httpd` 하나를 중심으로 실제 CGI 요청이 들어오는 지점(source)부터
`strcpy`/`sprintf`/`execve` 같은 위험 함수 호출(sink)까지 이어지는 흐름을
추적하는 것이 가장 효율적**이라고 생각합니다. 이번 정적 분석으로 이미
"어떤 함수가 존재하는지"와 "그 함수들이 어느 문자열/오프셋 부근에
몰려 있는지"까지는 확인했으므로, 다음 단계는 폭을 넓히는 것보다 이미
찾은 지점의 깊이를 파는 쪽이 투자 대비 효율이 높다고 봅니다.

---

## ✅ 최종 결론

### 이번 분석으로 확인한 사항
- Header, Kernel, RootFS, 대표 바이너리의 ELF 구조, RootFS 파일/디렉터리
  구성, 대부분의 Configuration 파일이 **모두 동일**함을 파일 단위·영역
  단위·바이너리 단위·통계 단위의 4가지 서로 다른 방법으로 교차
  확인했으며, 이후 `diffoscope`/`sasquatch`/`radare2`/`ent`를 추가
  설치해 각각 독립적인 도구로 **다시 한번 재확인**했습니다
  ([🔬 추가 도구 기반 교차 검증](#-추가-도구-기반-교차-검증) 참고).
- rootfs 내부 버전 문자열(`15.258`)과 빌드 타임스탬프까지 일치하여,
  두 이미지가 **같은 빌드 파이프라인의 산출물**임을 다각도로
  뒷받침했습니다.
- Loader blob 영역은 애초에 "재압축 아티팩트"로만 설명되었으나,
  diffoscope 정밀 재분석으로 (1) gzip 스트림 자체는 완전히 동일,
  (2) `hwparam.bin`과 같은 헤더 포맷을 가지되 일부 필드가 실제로 다른
  레코드(`0x020000`), (3) 채움 값만 다른 64KB 예비 블록(`0x030000`)의
  혼합임이 **새로 확인**되었습니다 — 결론을 뒤집지는 않지만 원인
  설명을 더 정확하게 교정한 **2차 갱신 사항**입니다.

### Hardware Dump와 Official Firmware의 차이
| 구분 | 차이 |
|---|---|
| 크기 | Dump가 225,280 bytes 더 큼 |
| 정체 | 전량 trailing erased flash (`0xFF`), 실제 콘텐츠 아님 |
| Loader blob: gzip 스트림 (35,904 bytes) | 압축 byte·압축 해제 결과 모두 완전히 동일 |
| Loader blob: `0x020000` 레코드 *(신규)* | 헤더 포맷은 동일, MAC-like 그룹·숫자열 등 일부 필드 값이 다름 *(추정: 장치별/빌드별 슬롯)* |
| Loader blob: `0x030000` 64KB 블록 *(신규)* | dump=`0xFF`, official=`0x00` — 내용 없는 예비 섹터 |
| 그 외 모든 항목 (Header, Kernel, RootFS, 대표 바이너리, 대부분의 Configuration) | 차이 없음 |

### RootFS 비교 결과
파일 수(415), 디렉터리 수(105), symlink 수(279), 총 크기, SquashFS
superblock 메타데이터, 개별 파일 SHA-256이 **전부 동일**하여, RootFS는
사실상 완전히 동일한 것으로 결론지었습니다.

### Flash Layout 비교 결과
Header → CRC32 table → Bootloader(gzip) → 미압축 영역(레코드 + 예비
블록 포함) → Kernel → RootFS → post-squashfs tail 순서의 동일한 구조를
공유하며, 구조적 차이는 dump에만 존재하는 trailing erased flash와
Bootloader 뒤 미압축 영역 안의 소규모 레코드·예비 블록뿐입니다. Dump는
8 MiB 전체 SPI flash 캡처, Official은 실제 크기에 맞춘 update 이미지로
판단됩니다.

### Firmware 구조 비교 결과
Binwalk signature와 독립적인 entropy 통계 분석이라는 두 가지 방법이
동일한 구조적 결론에 도달했으며, ELF Header/Program Header/Dynamic
Section 비교를 통해 바이너리 수준에서도 이를 재확인했습니다.

### 분석의 의의
- 이 분석은 단일 diff 결과에 의존하지 않고, **파일 → 구조(binwalk/entropy)
  → flash layout → rootfs → binary(ELF) → configuration/calibration**의
  6단계 계층을 모두 통과하며 서로 다른 도구로 교차 검증한, 실제
  리버스 엔지니어링 프로젝트에 준하는 체계적인 firmware 비교
  워크플로우를 보여줍니다.
- 하드웨어에서 직접 추출한 dump가 공식 배포 firmware와 실질적으로
  동일하다는 결론은, 해당 장치가 dump 채취 시점에 **수정되지 않은
  순정 firmware**로 동작하고 있었음을 강하게 뒷받침합니다.
- Configuration/Calibration 데이터에 대해서는 "동일하다"는 결과를
  액면 그대로 받아들이지 않고, 그것이 `default/` 템플릿이기 때문에
  동일한 것이라는 **원인까지 규명**함으로써, 결과를 넘어 의미를
  설명하는 분석을 수행했습니다.

### 향후 추가 분석 방향

> [!NOTE]
> 이전 버전에서 이 목록에 있던 "`radare2`/`rizin` 설치 후 심층 바이너리
> 분석"과 "`diffoscope` 설치 후 완전한 Deep Diff"는 이번에 **완료**되어
> [🔬 추가 도구 기반 교차 검증](#-추가-도구-기반-교차-검증)으로
> 반영되었습니다. 아래는 그 결과로 새로 생긴 후속 과제입니다.

1. **Runtime 검증** — 실제 장치 접근이 가능하다면, `/tmp/etc`에
   전개되는 실제 런타임 설정과 별도 NVRAM 영역의 실제 MAC/calibration
   값을 캡처하여 이번에 분석한 `default/` 템플릿, 그리고 loader blob
   내부 `0x020000` 레코드와 비교.
2. **`0x020000` 레코드 성격 규명** — 이 레코드가 실제 장치별/빌드별
   calibration·MAC 슬롯인지, 아니면 다른 목적의 고정값인지, 그리고
   펌웨어 업그레이드 시 이 섹터가 보존(skip)되는지 여부를 부트로더
   소스나 실제 업그레이드 절차 분석으로 확인.
3. **`httpd` source→sink 흐름 추적** — 이번 정적 분석으로 확인한
   `strcpy`/`strcat`/`sprintf`/`execve`/`execl`/`getenv` import와
   CGI 관련 문자열을 바탕으로, 실제 CGI 요청 처리 경로에서 사용자
   입력이 이 함수들에 어떻게 도달하는지 동적/디스어셈블리 분석으로
   추적 (§🗣 분석자 의견 참고).
4. **Bootloader partition table 확인** — 가능하다면 부트로더
   소스/데이터시트를 확보하여, 본 분석에서 "추정"으로 표기한 flash
   영역 경계(특히 Kernel 영역의 끝, `0x020000`/`0x030000` 블록의 정확한
   용도)를 공식적으로 확정.

---

<div align="center">

🇰🇷 한국어 보고서 — 📄 [English version available here](REPORT.md)

</div>
