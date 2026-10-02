# 노트북 CMDI-01 진행 가이드 v4 — enable/role 분리 정정 + port 25000 오해 정정 + 셸 없는 CMDU 생존 확인법

**v3까지의 핵심 원칙은 그대로 유효함**: 동글이 Windows에 있으면(DETACH) Windows만
그 LAN에 접근 가능, WSL은 못 씀. 동글이 WSL에 있으면(ATTACH) WSL만 그 LAN에
접근 가능, Windows는 못 씀(인터넷 포함).

**v4에서 바뀐 것 — v3의 치명적 오류 2개를 정정**:
1. `telnet 192.168.0.1 25000`으로 `p1905_managerd` 상태를 확인한다는 2-A 절차는
   **틀렸음**. 25000번은 EasyMesh 상시 디버그 콘솔이 아니라 **BACKDOOR-01
   finding 그 자체**(remote-debug RPC가 호출됐을 때만 그 순간 `telnetd`를
   띄우는 포트)라서, 평소엔 당연히 connection refused/timeout이 뜸. EasyMesh
   `enable` on/off와도 무관함.
2. "`controller=1`이 공장 기본값이니 EasyMesh가 pre-auth로 항상 켜져있다"는
   주장도 틀렸음. 실제 관리자 UI에는 `role`(controller/agent)과 `enable`(기능
   전체 on/off)이 **분리된 필드**이고, 실기기에서 확인해보니 `enable`이
   꺼져있었음. `node.default`의 `controller=1`은 role의 기본값일 뿐, enable의
   기본값을 보장하지 않음.

**확정된 값들**: BUSID `1-4`, WSL 인터페이스명 `enx88366cfecb0f`, 공유기 IP
`192.168.0.1`.

---

## PHASE 1 — DETACH 상태 (동글이 Windows에 있을 때) 할 일

지금 ATTACH 상태라면 먼저 **PowerShell**에서:
```powershell
usbipd detach --busid 1-4
```

이 상태에서 할 일들 (전부 Windows 인터넷/브라우저가 필요한 것들):

### 1-A. 공유기 관리자 페이지에서 EasyMesh `enable`/`role` 확인
Windows 브라우저로 `http://192.168.0.1` 접속 → 로그인 → "Easy Mesh" 메뉴 →
**"Controller mode"/"Agent mode" 라디오(= role)와, 그 위/별도에 있는 EasyMesh
켜짐/꺼짐 토글(= enable)을 둘 다 캡처**. (이 둘은 다른 설정값임 — role만 보고
전체가 켜져있다고 단정하지 말 것.)

지금까지 확인된 실기기 상태: **`enable`이 꺼져있음.** 이 상태를 일단
**그대로 두고** PHASE 2로 가서 외부 CMDU 테스트부터 할 것 (켜고 끄는 걸 섞으면
어느 상태에서 재현됐는지 헷갈림).

### 1-B. WSL에 필요한 패키지 설치 (인터넷 복구된 상태에서)
```bash
sudo apt-get update && sudo apt-get install -y tcpdump isc-dhcp-client ethtool
```

### 1-C. (나중에 4단계 쓸 거면 지금 미리) prplMesh 소스 받아두기
```bash
git clone https://gitlab.com/prpl-foundation/prplmesh/prplMesh.git
```

**1단계 다 끝났으면 → PHASE 2로.**

---

## PHASE 2 — ATTACH 상태 (동글이 WSL에 있을 때) 할 일

**PowerShell**에서:
```powershell
usbipd bind --busid 1-4
usbipd attach --wsl --busid 1-4
```
(`usbipd attach` 실행 시 `using IP address 172.30.240.1` 같은 메시지가
뜨는데, 이건 동글의 LAN IP가 아니라 **usbipd-win이 WSL2와 통신할 때 쓰는
내부 터널링 주소**(WSL NAT 게이트웨이)라서 무시해도 됨. 동글 자체의 IP는
아래에서 직접 부여함.)

**WSL**에서 인터페이스 올리고 IP 부여:
```bash
ip link show enx88366cfecb0f
sudo ip link set enx88366cfecb0f up
sudo ip addr add 192.168.0.50/24 dev enx88366cfecb0f
ping -c 3 192.168.0.1
```

### 2-0. (ping이 안 될 때) NO-CARRIER 트러블슈팅
`ip -d link show enx88366cfecb0f`의 `<...>` 플래그에 `LOWER_UP`이 없고
`NO-CARRIER`만 있으면 **물리 계층 문제**(소프트웨어 설정 문제 아님):
```bash
ip -d link show enx88366cfecb0f      # LOWER_UP 있는지
sudo ethtool enx88366cfecb0f | grep -i link   # Link detected: yes/no
lsusb; dmesg | tail -50              # USB/드라이버 에러 확인
```
- 케이블을 동글/공유기 양쪽에 다시 꽉 꽂기, 포트 바꿔보기, 케이블 교체
- 가장 확실한 분리 테스트: `usbipd detach`로 동글을 Windows로 돌려놓고
  Windows 네트워크 설정에서 그 어댑터가 "연결됨"으로 뜨는지 확인 → Windows
  에서도 안 뜨면 케이블/포트 문제 확정, Windows에선 뜨는데 ATTACH 후에만
  NO-CARRIER면 usbipd/WSL 패스스루 쪽 문제로 좁혀짐.

✅ ping 응답 확인되면 다음 단계로.

---

## PHASE 2-A (수정됨) — 셸 없이 p1905_managerd 생존 확인 (Topology Query 왕복)

~~telnet 192.168.0.1 25000으로 ps -ef 확인~~ **← 삭제. 이 방법은 안 됨
(위 "바뀐 것" 1번 참고).**

대신 **1905.1a Topology Query(0x0002) → Topology Response(0x0003)** 왕복으로
데몬 생존을 외부에서 판별한다. Topology Query를 받은 1905 엔티티는 스펙상
반드시 Topology Response로 응답해야 하므로, 응답이 오면 곧 p1905_managerd가
살아서 CMDU를 파싱하고 있다는 뜻이고, 안 오면 죽어있거나 안 듣는다는 뜻.

### 1. 공유기 MAC 확인 (ping 성공했다면)
```bash
ip neigh show 192.168.0.1
```

### 2. 터미널 A — 캡처
```bash
sudo tcpdump -i enx88366cfecb0f -XX 'ether proto 0x893a'
```

### 3. 터미널 B — Topology Query 전송
```bash
sudo python3 - <<'EOF'
import socket, struct

IFACE = "enx88366cfecb0f"
ETHERTYPE = 0x893a
DST_MAC = "ff:ff:ff:ff:ff:ff"   # 공유기 MAC 알면 그걸로 교체 권장

dst = bytes.fromhex(DST_MAC.replace(":", ""))

s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETHERTYPE))
s.bind((IFACE, 0))
src = s.getsockname()[4]

# --- CMDU header (1905.1a) ---
message_version = 0x00
reserved        = 0x00
message_type    = 0x0002   # Topology Query
message_id      = 0x0001
fragment_id     = 0x00
flags           = 0x80     # LastFragmentIndicator=1, RelayIndicator=0

cmdu_header = struct.pack("!BBHHBB",
    message_version, reserved, message_type, message_id, fragment_id, flags)

# --- End-of-message TLV (type=0x00, length=0x0000) ---
end_tlv = struct.pack("!BH", 0x00, 0x0000)

payload = cmdu_header + end_tlv

ethertype_bytes = struct.pack("!H", ETHERTYPE)
frame = dst + src + ethertype_bytes + payload
frame += b"\x00" * max(0, 60 - len(frame))   # 최소 프레임 길이 패딩

s.send(frame)
print(f"sent Topology Query, {len(frame)} bytes, src={src.hex(':')}")
EOF
```

### 4. 판단 기준
터미널 A에서 **우리 src MAC이 아닌 공유기 MAC에서 온 CMDU**가 잡히고, 그
CMDU 헤더의 MessageType(이더넷 헤더 14바이트 뒤 3~4번째 바이트)가 `00 03`
(Topology Response)이면 → **p1905_managerd 생존 + CMDU 파싱 경로 살아있음
확정**. 응답 없으면 → 꺼져있거나 최소 이 요청엔 무응답.

**지금 EasyMesh `enable`이 꺼진 상태 그대로 먼저 테스트할 것** — 응답이 오면
"enable 토글과 무관하게 pre-auth로 CMDU 파싱 경로가 열려있다"는 가장 강력한
증거가 되고, 이후 1-A로 돌아가 `enable`을 켠 상태에서 같은 테스트를 반복해
차이가 있는지(예: 응답 TLV 내용 변화, 혹은 꺼진 상태에선 무응답이던 게 켜면
응답하는 식)도 비교해볼 것.

---

## PHASE 2-B — raw L2 캡처 (타겟이 CMDU를 자발적으로 보내는지, v3과 동일)

**터미널 A:**
```bash
sudo tcpdump -i enx88366cfecb0f -XX 'ether proto 0x893a'
```
2~3분 대기. 잡히면 성공 — PHASE 4로.

안 잡히면, 우리가 직접 보낸 프레임이 나가는지만 재확인 (터미널 B, 별도 창):
```bash
sudo python3 - <<'EOF'
import socket, struct
IFACE = "enx88366cfecb0f"
ETHERTYPE = 0x893a
s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETHERTYPE))
s.bind((IFACE, 0))
dst = b"\xff\xff\xff\xff\xff\xff"
src = s.getsockname()[4]
frame = dst + src + struct.pack("!H", ETHERTYPE) + b"\x00" * 20
s.send(frame)
print("sent", len(frame), "bytes on", IFACE)
EOF
```
(이건 우리 자신이 보낸 프레임이 와이어에 나가는지만 확인하는 것 — 타겟이
자발적으로 보낸 CMDU와 구별할 것. src MAC이 우리 인터페이스 MAC과 같으면
우리가 보낸 것.)

---

## PHASE 3 — (ATTACH 상태에서) prplMesh 실행

PHASE 1-C에서 받아둔 소스로, `REAL-HARDWARE-VERIFICATION-GUIDE.md`의 "3-3.
CMDI-01 페이로드" "전체 절차" 그대로 (patch 적용 → build → run.sh). 동글이
WSL에 ATTACH된 이 상태 그대로 진행.

---

## (보류) BACKDOOR-01을 통한 실제 셸 확보

p1905_managerd 상태를 `ps -ef`로 직접 보고 싶으면, PHASE 2-A의 외부 CMDU
테스트로는 부족하고 실제 셸이 필요함. 이 경우 `BACKDOOR-01-plugin_agent-
easymesh_remote-noauth-telnetd.md`에 정리된 EasyMesh remote-debug RPC를
trigger해서 25000번에 `/bin/sh` telnetd를 직접 띄우는 방법이 있음 — 단 이건
별도의 공격 체인(BACKDOOR-01 자체의 실기기 PoC)이라, CMDI-01 검증과 섞기
전에 트리거 조건(mode 1 vs mode 2, source IP 제한)부터 다시 확인하고
진행할지 결정할 것.

---

## 막히면 돌아올 지점

| 증상 | 원인 | 해결 |
|---|---|---|
| ping 되는데 브라우저 안 됨 | 동글이 WSL에 있음 (ATTACH) | PHASE 1로 (detach) |
| ping 안 되고 `ip -d link show`에 NO-CARRIER | 물리 연결(케이블/포트) 문제 | PHASE 2-0 트러블슈팅 |
| telnet 25000 둘 다 안 됨 (enable on/off 무관) | **정상임 — 25000은 BACKDOOR-01 RPC 트리거 전용, 상시 포트 아님** | PHASE 2-A의 Topology Query 테스트로 대체 |
| apt/git 안 됨 (인터넷 없음) | 동글이 WSL에 있음 (ATTACH) | PHASE 1로 (detach) |
| raw L2 캡처 테스트 하려는데 | 동글이 Windows에 있음 (DETACH) | PHASE 2로 (attach) |
