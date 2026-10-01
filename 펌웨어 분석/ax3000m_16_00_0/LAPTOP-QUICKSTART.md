# 노트북에서 그대로 따라하기 — CMDI-01 raw L2 접근 확보

**목적**: 노트북(Windows 11 Home, 테스트 공유기에 유선 연결됨)에서 1905.1 CMDU
(EtherType `0x893a`) 프레임을 raw로 보낼 수 있는 상태를 만든다. 설명은 최소화,
코드 블록을 순서대로 복붙/입력만 하면 됨. 각 단계 끝의 "✅ 확인"을 통과해야
다음 단계로 간다.

---

## 0단계 — 사전 확인 (PowerShell, 관리자 권한 아니어도 됨)

```powershell
winver
(Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion').EditionID
wsl --version
wsl --update
```

✅ 확인: `wsl --version`의 WSL 버전이 `2.0.0` 이상이면 통과. (낮으면 `wsl
--update` 후 재확인)

---

## 1단계 — WSL2 mirrored networking 켜기

PowerShell에서:

```powershell
notepad $env:USERPROFILE\.wslconfig
```

메모장이 열리면 아래 내용을 **그대로 붙여넣고 저장** (기존 내용 있으면 `[wsl2]`
섹션에 `networkingMode=mirrored` 한 줄만 추가):

```ini
[wsl2]
networkingMode=mirrored
```

저장 후 PowerShell에서:

```powershell
wsl --shutdown
```

5초 기다린 뒤 WSL 터미널을 새로 열고:

```bash
ip addr
```

✅ 확인: 테스트 공유기 쪽 서브넷의 실제 IP(예: `192.168.0.x`, `192.168.25.x`
등)가 WSL 안에서 바로 보이면 통과. `172.x`만 보이면 mirrored가 안 먹은 것 —
`.wslconfig` 경로/문법 다시 확인 후 `wsl --shutdown` 재시도.

---

## 2단계 — raw L2 프레임이 실제로 나가는지 테스트 (WSL bash)

인터페이스 이름 먼저 확인:

```bash
ip link
```

아래에서 `eth0` 부분을 실제 인터페이스 이름으로 바꿔서 실행 (터미널 2개 필요
— 하나는 보내고 하나는 캡처):

**터미널 A (캡처, 먼저 실행해서 대기):**
```bash
sudo tcpdump -i eth0 -XX 'ether proto 0x893a'
```

**터미널 B (전송):**
```bash
sudo python3 - <<'EOF'
import socket, struct
IFACE = "eth0"
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

✅ 확인: 터미널 A에 프레임이 캡처되면 **성공 — 3단계(동글) 건너뛰고 바로
4단계로**. 아무것도 안 잡히면 3단계로.

(여유 있으면 추가 확인: 타겟 공유기가 평소에 브로드캐스트하는 M1도 터미널
A에서 같이 잡히는지 — 몇 초~몇십 초 기다려서 확인)

---

## 3단계 — (2단계 실패시만) USB 이더넷 동글로 우회

준비물: USB-LAN 동글 1개 (아무 브랜드나 OK, 수천원).

```powershell
winget install usbipd
```

동글을 노트북에 꽂고, **동글 쪽 케이블을 테스트 공유기 LAN 포트에 연결**
(노트북 내장 이더넷 대신 이 동글을 공유기에 물리는 것).

```powershell
usbipd list
```

목록에서 방금 꽂은 동글의 BUSID 확인 (예: `2-3`), 아래 `<BUSID>`를 그걸로
교체:

```powershell
usbipd bind --busid <BUSID>
usbipd attach --wsl --busid <BUSID>
```

WSL bash에서:

```bash
ip link
```

✅ 확인: `usb0` 같은 새 인터페이스가 보이면 성공.

```bash
sudo dhclient usb0
ip addr show usb0
```

✅ 확인: 테스트 공유기 서브넷 IP를 받으면 성공. 안 받으면 수동으로:
```bash
sudo ip addr add 192.168.0.50/24 dev usb0   # 서브넷은 실제 환경에 맞게 수정
sudo ip link set usb0 up
```

이제 **2단계를 `IFACE = "usb0"`로 바꿔서 다시 실행** — 여기서 성공해야 함
(이 방식은 WSL이 동글을 독점하므로 거의 확실히 됨).

---

## 4단계 — prplMesh 패치본 실행

raw L2가 확인된 인터페이스 이름(`eth0` 또는 `usb0`)을 기억해두고,
`analysis/REAL-HARDWARE-VERIFICATION-GUIDE.md`의 **"3-3. CMDI-01 페이로드"**
섹션 "전체 절차"를 그대로 따라가면 됨 (clone → patch → build → `run.sh`).
패치 파일은 이미 준비되어 있음: `analysis/emulation/CMDI-01-wapp/prplmesh-wep-injection.patch`

`run.sh`를 띄울 때 컨테이너 네트워크 옵션(`--network host` 등)에서 안 되면,
Docker 없이 **네이티브로** `tools/docker/build.sh`가 만든 결과물을 WSL 안에서
직접 빌드/실행하는 것도 고려 (복잡도는 올라가지만 Docker 자체의 네트워크
스택 한 겹을 없앨 수 있음).

---

## 문제 생기면 돌아올 지점

- 0단계에서 WSL 버전이 낮으면 → `wsl --update` 반복
- 1단계에서 mirrored가 안 먹으면 → `.wslconfig` 파일 위치/오타 확인
  (`$env:USERPROFILE`가 맞는 경로인지 `echo $env:USERPROFILE`로 확인)
- 2단계 실패 → 3단계(동글)로
- 3단계도 실패 → 여기서 멈추고 결과(어디서 뭐가 안 됐는지) 그대로 공유 —
  다음 대안 찾아야 함
