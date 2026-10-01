# 노트북 CMDI-01 진행 가이드 v3 — 동글 위치(DETACH/ATTACH) 기준으로 순서 정리

**v2는 이제 안 봐도 됨.** 핵심 원칙 하나만 기억: **동글이 Windows에 있으면
(DETACH) Windows만 그 LAN에 접근 가능, WSL은 못 씀. 동글이 WSL에 있으면
(ATTACH) WSL만 그 LAN에 접근 가능, Windows는 못 씀 (인터넷 포함).** 모든 혼란이
이거 때문이었음. 아래는 "지금 동글이 어디 있어야 하는지" 기준으로 순서대로
나눔 — 위에서 아래로 그냥 실행.

**확정된 값들**: BUSID `1-4`, WSL 인터페이스명 `enx88366cfecb0f`, 공유기 IP
`192.168.0.1`.

---

## PHASE 1 — DETACH 상태 (동글이 Windows에 있을 때) 할 일

지금 ATTACH 상태라면 먼저 **PowerShell**에서:
```powershell
usbipd detach --busid 1-4
```

이 상태에서 할 일들 (전부 Windows 인터넷/브라우저가 필요한 것들):

### 1-A. 공유기 관리자 페이지에서 EasyMesh 켜져있는지 확인
Windows 브라우저로 `http://192.168.0.1` 접속 → 로그인 → "EasyMesh"/"메시"/"Wi-Fi
통합" 메뉴 찾기 → 꺼져있으면 켜고 공유기 재부팅.

### 1-B. WSL에 필요한 패키지 설치 (인터넷 복구된 상태에서)
```bash
sudo apt-get update && sudo apt-get install -y tcpdump isc-dhcp-client
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

**WSL**에서 인터페이스 올리고 IP 부여:
```bash
ip link show enx88366cfecb0f
sudo ip link set enx88366cfecb0f up
sudo ip addr add 192.168.0.50/24 dev enx88366cfecb0f
ping -c 3 192.168.0.1
```
✅ ping 응답 확인.

### 2-A. (1-A를 안 했거나 결과가 애매하면) telnet으로 EasyMesh 데몬 확인
```bash
telnet 192.168.0.1 25000
```
들어가면: `ps -ef | grep p1905_managerd`
- 떠있으면 → 2-B로
- 안 떠있으면 → PHASE 1로 돌아가서 1-A(웹UI에서 켜기) 다시

### 2-B. raw L2 캡처 (타겟이 실제로 CMDU 보내는지)

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

---

## PHASE 3 — (ATTACH 상태에서) prplMesh 실행

PHASE 1-C에서 받아둔 소스로, `REAL-HARDWARE-VERIFICATION-GUIDE.md`의 "3-3.
CMDI-01 페이로드" "전체 절차" 그대로 (patch 적용 → build → run.sh). 동글이
WSL에 ATTACH된 이 상태 그대로 진행.

---

## 막히면 돌아올 지점

| 증상 | 원인 | 해결 |
|---|---|---|
| ping 되는데 브라우저 안 됨 | 동글이 WSL에 있음 (ATTACH) | PHASE 1로 (detach) |
| telnet/ps 하려는데 WSL에서 IP 없음 | 동글이 Windows에 있음 (DETACH) | PHASE 2로 (attach + IP) |
| apt/git 안 됨 (인터넷 없음) | 동글이 WSL에 있음 (ATTACH) | PHASE 1로 (detach) |
| raw L2 캡처 테스트 하려는데 | 동글이 Windows에 있음 (DETACH) | PHASE 2로 (attach) |
