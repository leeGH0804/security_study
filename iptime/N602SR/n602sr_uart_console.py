#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
n602sr_uart_console.py

ipTIME N602SR UART Bootloader Command Mode 진입/조작 콘솔.

부팅 직후 ESC(0x1B)를 자동으로 연타하여 vendor bootloader의
"Escape booting by user" 경로를 유발, <RealTek> 프롬프트(Command Mode)로
진입시킨 뒤, 프롬프트 감지 즉시 ESC 전송을 멈추고 인터랙티브 터미널로
전환하는 도구.

background:
  이 라우터의 부트로더는 UART로 ESC(0x1B) 1바이트를 받으면 정상 부팅을
  중단하고 인증 없는 vendor 디버그 CLI("<RealTek>" 프롬프트, Command Mode)
  로 진입한다. 이 판단은 실제 부트로더 바이너리를 디스어셈블해 확인한
  것이며, 자세한 근거는 analysis/bootloader/README.md 참고.

필요 패키지:
    pip install pyserial

실행 예:
    python n602sr_uart_console.py
    python n602sr_uart_console.py --port COM4 --baud 38400
    python n602sr_uart_console.py --log bootloader_uart.log
    python n602sr_uart_console.py --allow-dangerous

자세한 사용법은 파일 맨 아래 "사용법" 주석 참고.
"""

import sys
import os
import time
import argparse
import threading
import queue

try:
    import serial
except ImportError:
    print("[!] pyserial이 설치되어 있지 않습니다. 다음 명령으로 설치하세요:")
    print("    pip install pyserial")
    sys.exit(1)


# =====================================================================
# 기본 설정값 (상단에서 바로 수정 가능; 명령행 인자로도 덮어쓸 수 있음)
# =====================================================================
DEFAULT_PORT = "COM3"
DEFAULT_BAUD = 38400          # 확인된 값. 115200에서는 로그가 깨짐.
DEFAULT_BYTESIZE = serial.EIGHTBITS
DEFAULT_PARITY = serial.PARITY_NONE
DEFAULT_STOPBITS = serial.STOPBITS_ONE

DEFAULT_ESC_BURST = 10        # 한 번에 보낼 ESC 바이트 개수
DEFAULT_ESC_INTERVAL = 0.001  # burst 내부, ESC 바이트 사이 간격(초)
DEFAULT_ESC_BURST_GAP = 0.02  # burst와 burst 사이 간격(초)
DEFAULT_TIMEOUT = 30          # <RealTek> 미검출 시 ESC 전송을 포기하는 시간(초)

PROMPT_MARKER = "<RealTek>"

# 위험 명령어 목록 (대소문자 무시, 첫 토큰 기준으로 매칭)
DANGEROUS_COMMANDS = {"ERASECHIP", "ERASESECTOR", "FLW"}

# 시리얼 read 폴링 주기 (짧을수록 <RealTek> 감지가 빨라져 ESC 잔여 바이트가 줄어듦)
SERIAL_READ_TIMEOUT = 0.05
ROLLING_BUFFER_KEEP = 512     # 프롬프트 탐지를 위해 유지하는 최근 수신 버퍼 길이(문자 수)


# =====================================================================
# 전역 상태
# =====================================================================
class SharedState:
    def __init__(self):
        self.stop_all = threading.Event()        # 프로그램 전체 종료 신호 (read thread까지 종료)
        self.stop_esc = threading.Event()        # ESC 전송 스레드만 종료 (read thread는 계속 생존)
        self.prompt_found = threading.Event()    # <RealTek> 감지 여부
        self.log_lock = threading.Lock()
        self.log_file = None


def ts():
    return time.strftime("%H:%M:%S")


# =====================================================================
# UART 읽기 스레드 — 프로그램이 끝날 때까지(stop_all) 절대 종료되지 않음
# =====================================================================
def reader_thread(ser: "serial.Serial", state: SharedState):
    rolling = ""
    print(f"[*] {ts()} [READ] 수신 스레드 시작 (stop_all 신호까지 계속 유지됩니다)")

    while not state.stop_all.is_set():
        try:
            n = ser.in_waiting
            data = ser.read(n if n > 0 else 1)
        except serial.SerialException as e:
            print(f"[!] {ts()} [READ] 시리얼 오류: {e}")
            state.stop_all.set()
            break

        if not data:
            continue

        text = data.decode("utf-8", errors="replace")

        # 화면 출력 (raw 그대로, 부트로그 개행을 그대로 살림)
        sys.stdout.write(text)
        sys.stdout.flush()

        # 로그 파일 기록
        if state.log_file:
            with state.log_lock:
                state.log_file.write(text)
                state.log_file.flush()

        # 프롬프트 탐지를 위한 rolling buffer 갱신
        rolling += text
        if len(rolling) > ROLLING_BUFFER_KEEP:
            rolling = rolling[-ROLLING_BUFFER_KEEP:]

        if not state.prompt_found.is_set() and PROMPT_MARKER in rolling:
            state.prompt_found.set()
            state.stop_esc.set()
            # ESC 전송 스레드가 아직 보내지 못하고 OS 송신 버퍼에 남아있는
            # 잔여 ESC 바이트를 취소한다. (이미 물리적으로 전송된 바이트는
            # 되돌릴 수 없지만, 아직 안 나간 바이트는 여기서 차단된다.)
            try:
                ser.reset_output_buffer()
            except Exception:
                pass
            print(f"\n[*] {ts()} [READ] '{PROMPT_MARKER}' 프롬프트 감지 -> ESC 전송 중단")

    print(f"[*] {ts()} [READ] 수신 스레드 종료")


# =====================================================================
# ESC 전송 스레드 — prompt_found / stop_esc / stop_all / timeout 중
#                  하나라도 걸리면 스스로 종료. read thread에는 영향 없음.
# =====================================================================
def esc_sender_thread(ser: "serial.Serial", state: SharedState,
                       esc_burst: int, esc_interval: float, timeout: float):
    print(f"[*] {ts()} [ESC ] ESC(0x1B) 자동 전송 시작 "
          f"(burst={esc_burst}, interval={esc_interval*1000:.1f}ms, timeout={timeout}s)")

    start = time.time()
    esc_byte = bytes([0x1B])

    while True:
        if state.stop_all.is_set() or state.stop_esc.is_set() or state.prompt_found.is_set():
            break
        if time.time() - start > timeout:
            print(f"\n[*] {ts()} [ESC ] timeout({timeout}s) 도달 — '{PROMPT_MARKER}' 미검출. "
                  f"ESC 전송을 중단하고 로그 수신만 계속합니다.")
            break

        try:
            for _ in range(esc_burst):
                if state.stop_all.is_set() or state.stop_esc.is_set() or state.prompt_found.is_set():
                    break
                ser.write(esc_byte)
                time.sleep(esc_interval)
        except serial.SerialException as e:
            print(f"\n[!] {ts()} [ESC ] 전송 중 시리얼 오류: {e}")
            state.stop_all.set()
            break

        time.sleep(DEFAULT_ESC_BURST_GAP)

    print(f"[*] {ts()} [ESC ] ESC 전송 스레드 종료 (read 스레드는 계속 동작 중)")


# =====================================================================
# 인터랙티브 모드
# =====================================================================
def is_dangerous(command_line: str) -> bool:
    if not command_line.strip():
        return False
    first_token = command_line.strip().split()[0].upper()
    return first_token in DANGEROUS_COMMANDS


def interactive_mode(ser: "serial.Serial", state: SharedState,
                      newline: str, allow_dangerous: bool):
    line_ending = "\r\n" if newline == "crlf" else "\r"

    print()
    print("=" * 70)
    print(" 인터랙티브 모드 시작")
    print(f"   - 줄바꿈 방식: {'CRLF (\\r\\n)' if newline == 'crlf' else 'CR (\\r)'}")
    print("   - 'exit' 입력 시 프로그램 종료")
    print("   - Ctrl+C 로도 안전 종료 가능")
    if not allow_dangerous:
        print(f"   - 위험 명령({', '.join(sorted(DANGEROUS_COMMANDS))})은 기본적으로 차단됩니다.")
        print("     허용하려면 프로그램을 --allow-dangerous 옵션으로 다시 실행하세요.")
    else:
        print(f"   - [경고] --allow-dangerous 활성화됨: 위험 명령 전송이 허용됩니다!")
    print("=" * 70)

    if not state.prompt_found.is_set():
        print(f"[*] 참고: '{PROMPT_MARKER}' 프롬프트를 아직 감지하지 못했습니다.")
        print("    그래도 직접 명령을 입력해 볼 수 있습니다 (부트로더가 이미 Command")
        print("    Mode에 들어가 있을 수도 있습니다).")

    while not state.stop_all.is_set():
        try:
            user_input = input()
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\n[*] Ctrl+C 감지 — 종료합니다.")
            state.stop_all.set()
            break

        if user_input.strip().lower() == "exit":
            print("[*] 'exit' 입력 — 종료합니다.")
            state.stop_all.set()
            break

        if is_dangerous(user_input):
            first_token = user_input.strip().split()[0].upper()
            if not allow_dangerous:
                print(f"[!] '{first_token}'는 위험 명령으로 분류되어 전송이 차단되었습니다.")
                print(f"    (flash를 지우거나 씁니다. 허용하려면 --allow-dangerous 옵션으로 재실행하세요.)")
                continue
            else:
                print(f"[!!!] 위험 명령 '{first_token}'을(를) 전송하려 합니다. flash가 변경/삭제될 수 있습니다.")
                confirm = input(f"      정말 전송하시겠습니까? 'YES'를 정확히 입력하세요: ")
                if confirm.strip() != "YES":
                    print("[*] 확인되지 않아 전송을 취소했습니다.")
                    continue
                print(f"[!!!] 위험 명령 '{first_token}' 전송을 진행합니다.")

        try:
            ser.write(user_input.encode("utf-8", errors="replace") + line_ending.encode())
        except serial.SerialException as e:
            print(f"[!] 전송 중 시리얼 오류: {e}")
            state.stop_all.set()
            break

    state.stop_all.set()


# =====================================================================
# main
# =====================================================================
def parse_args():
    p = argparse.ArgumentParser(
        description="ipTIME N602SR UART Bootloader Command Mode 진입 도구"
    )
    p.add_argument("--port", default=DEFAULT_PORT, help=f"COM 포트 (기본값: {DEFAULT_PORT})")
    p.add_argument("--baud", type=int, default=DEFAULT_BAUD, help=f"baudrate (기본값: {DEFAULT_BAUD})")
    p.add_argument("--esc-burst", type=int, default=DEFAULT_ESC_BURST,
                    help=f"burst당 ESC 바이트 개수 (기본값: {DEFAULT_ESC_BURST})")
    p.add_argument("--esc-interval", type=float, default=DEFAULT_ESC_INTERVAL,
                    help=f"burst 내 ESC 바이트 사이 간격(초) (기본값: {DEFAULT_ESC_INTERVAL})")
    p.add_argument("--newline", choices=["cr", "crlf"], default="cr",
                    help="인터랙티브 모드에서 Enter 전송 방식 (기본값: cr)")
    p.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                    help=f"<RealTek> 미검출 시 ESC 전송을 포기하는 시간(초) (기본값: {DEFAULT_TIMEOUT})")
    p.add_argument("--log", default=None, help="수신 로그를 저장할 파일 경로 (예: bootloader_uart.log)")
    p.add_argument("--allow-dangerous", action="store_true",
                    help="ERASECHIP/ERASESECTOR/FLW 등 위험 명령 전송을 허용")
    return p.parse_args()


def main():
    args = parse_args()
    state = SharedState()

    if args.log:
        try:
            state.log_file = open(args.log, "a", encoding="utf-8", buffering=1)
            state.log_file.write(f"\n\n===== session start {time.strftime('%Y-%m-%d %H:%M:%S')} =====\n")
        except OSError as e:
            print(f"[!] 로그 파일을 열 수 없습니다: {e}")
            sys.exit(1)

    print(f"[*] {ts()} {args.port} 포트를 baud={args.baud}, 8N1로 여는 중...")
    try:
        ser = serial.Serial(
            port=args.port,
            baudrate=args.baud,
            bytesize=DEFAULT_BYTESIZE,
            parity=DEFAULT_PARITY,
            stopbits=DEFAULT_STOPBITS,
            timeout=SERIAL_READ_TIMEOUT,
            write_timeout=2,
        )
    except serial.SerialException as e:
        print(f"[!] 포트를 열 수 없습니다: {e}")
        print("    - 포트 이름이 맞는지 (장치 관리자에서 확인)")
        print("    - 다른 프로그램(PuTTY 등)이 포트를 점유하고 있지 않은지 확인하세요.")
        sys.exit(1)

    print(f"[*] {ts()} 포트 오픈 성공. 이제 공유기 전원을 켜세요 (또는 재부팅하세요).")
    print(f"[*] {ts()} '{PROMPT_MARKER}' 프롬프트를 감지할 때까지 ESC를 자동 전송합니다...")
    print("-" * 70)

    t_reader = threading.Thread(target=reader_thread, args=(ser, state), daemon=True)
    t_reader.start()

    t_esc = threading.Thread(
        target=esc_sender_thread,
        args=(ser, state, args.esc_burst, args.esc_interval, args.timeout),
        daemon=True,
    )
    t_esc.start()

    # ESC 전송 스레드가 끝날 때까지 대기 (prompt 감지 또는 timeout)
    t_esc.join()

    # 프롬프트가 감지된 경우, 잔여 "Unknown command !" 노이즈가 가라앉을
    # 시간을 잠깐 준다 (read thread는 계속 돌면서 화면에 출력한다).
    if state.prompt_found.is_set():
        time.sleep(0.5)

    try:
        interactive_mode(ser, state, args.newline, args.allow_dangerous)
    except KeyboardInterrupt:
        print("\n[*] Ctrl+C 감지 — 종료합니다.")
        state.stop_all.set()

    state.stop_all.set()
    t_reader.join(timeout=2)

    try:
        ser.close()
    except Exception:
        pass

    if state.log_file:
        state.log_file.write(f"===== session end {time.strftime('%Y-%m-%d %H:%M:%S')} =====\n")
        state.log_file.close()

    print(f"[*] {ts()} 포트를 닫고 프로그램을 종료합니다.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[*] Ctrl+C 감지 — 강제 종료합니다.")
        sys.exit(1)


# =====================================================================
# 사용법
# =====================================================================
#
# 0) 설치
#     pip install pyserial
#
# 1) 기본 실행 (COM3, 38400bps)
#     python n602sr_uart_console.py
#
#   실행 순서:
#     ① 스크립트가 먼저 COM 포트를 연다.
#     ② "이제 공유기 전원을 켜세요" 메시지가 뜨면 그때 라우터 전원을 인가한다.
#        (또는 이미 켜져 있다면 라우터를 재부팅한다.)
#     ③ 부팅 로그가 실시간으로 화면에 출력되면서, 동시에 ESC(0x1B)가
#        자동으로 계속 전송된다.
#     ④ "<RealTek>" 프롬프트가 로그에 나타나면 ESC 전송이 즉시 멈추고,
#        인터랙티브 모드로 전환된다 (UART 읽기 스레드는 계속 살아있다).
#     ⑤ 이제 키보드로 "?", "CP0", "DB 80001000 10" 같은 명령을 입력하고
#        Enter를 치면 그대로 UART로 전달된다. 응답은 실시간으로 화면에
#        출력된다.
#     ⑥ "exit"를 입력하거나 Ctrl+C를 누르면 안전하게 포트를 닫고 종료한다.
#
# 2) 포트/속도 변경
#     python n602sr_uart_console.py --port COM4 --baud 38400
#
# 3) ESC burst 세기/간격 조절 (기본값으로 안 될 때)
#     python n602sr_uart_console.py --esc-burst 20 --esc-interval 0.0005
#
# 4) <RealTek> 대기 시간(기본 30초) 조절
#     python n602sr_uart_console.py --timeout 60
#
# 5) 수신 로그를 파일로 저장
#     python n602sr_uart_console.py --log bootloader_uart.log
#
# 6) Enter를 CRLF로 보내고 싶을 때 (기본은 CR)
#     python n602sr_uart_console.py --newline crlf
#
# 7) 위험 명령(ERASECHIP / ERASESECTOR / FLW) 허용
#     python n602sr_uart_console.py --allow-dangerous
#   -> 이 옵션 없이 위험 명령을 입력하면 전송이 차단되고 경고만 출력된다.
#   -> 옵션을 켜도 실제 전송 전에 'YES'를 직접 입력해야 최종 전송된다.
#
# 8) <RealTek>를 못 찾은 경우
#     --timeout 초가 지나면 ESC 전송은 자동으로 멈추고, 로그 수신은 계속
#     된다. 이 상태에서도 인터랙티브 모드로 넘어가므로, 수동으로 Enter나
#     원하는 문자를 보내볼 수 있다.
#
# 주의:
#   - ERASECHIP / ERASESECTOR / FLW 는 실제로 flash를 지우거나 씁니다.
#     장비를 벽돌로 만들 수 있으니 --allow-dangerous 없이는 원천 차단됩니다.
#   - baudrate 38400 확인됨 (115200에서는 로그가 깨짐).
#   - Windows 장치 관리자에서 실제 COM 포트 번호를 먼저 확인하세요.
