# 로그
Booting...
init_ram
bond:0x00000004
MCM 64/32MB

 dram_init_clk_frequency ,ddr_freq=1066 (Mbps), 533 (MHZ)

DRAM init disable

DRAM init enable

DRAM init is done , jump to DRAM
enable DRAM ODT

SDR init done dev_map=0xb8142000

Detect page_size = 2KB (3)

Detect bank_size = 4 banks(0x00000001)

Detect dram size = 64MB (0x04000000)

DDR init OK
init ddr ok

DRAM Type: DDR2
        DRAM frequency: 533MHz
        DRAM Size: 64MB
JEDEC id C84017, EXT id 0xc840
found gd25q64
flash vendor: GigaDevice
gd25q64, size=8MB, erasesize=4KB, max_speed_hz=41000000Hz
auto_mode=0 addr_width=3 erase_opcode=0x00000020
Write PLL1=80c00042
=>CPU Wake-up interrupt happen! GISR=89000080

---Realtek RTL8197F-VG boot code at 2024.07.18-10:30+0900 v3.4.14b (999MHz)
Delay 1 second.
Check Firmware(00040000) : size: 0x00788fc8 ---->[ OK ]
Firmware CHECKED [OK]
Jump to image start=0x80a00000...
decompressing kernel:
Uncompressing Linux... done, booting the kernel.
done decompressing kernel.
start address: 0x80425a60
Linux version 3.10.90 (ipTIME@3031a10498e5) (gcc version 4.8.5 20150209 (prerelease) (Realtek MSDK-4.8.5p1 Build 2536) ) #1 Sat Jan 4 13:33:37 KST 2025
bootconsole [early0] enabled
CPU revision is: 00019385 (MIPS 24Kc)
Determined physical RAM map:
 memory: 04000000 @ 00000000 (usable)
Zone ranges:
  Normal   [mem 0x00000000-0x03ffffff]
Movable zone start for each node
Early memory node ranges
  node   0: [mem 0x00000000-0x03ffffff]
Primary instruction cache 64kB, VIPT, 4-way, linesize 32 bytes.
Primary data cache 32kB, 4-way, PIPT, no aliases, linesize 32 bytes
Built 1 zonelists in Zone order, mobility grouping off.  Total pages: 4088
Kernel command line: console=ttyS0,38400 root=/dev/mtdblock1
PID hash table entries: 256 (order: -4, 1024 bytes)
Dentry cache hash table entries: 8192 (order: 1, 32768 bytes)
Inode-cache hash table entries: 4096 (order: 0, 16384 bytes)
Writing ErrCtl register=0000a20b
Readback ErrCtl register=0000a20b
Memory: 50272k/65536k available (4285k kernel code, 15264k reserved, 1516k data, 208k init, 0k highmem)
SLUB: HWalign=32, Order=0-3, MinObjects=0, CPUs=1, Nodes=1
NR_IRQS:192
Realtek GPIO IRQ init
Calibrating delay loop... 666.41 BogoMIPS (lpj=3332096)
pid_max: default: 32768 minimum: 301
Mount-cache hash table entries: 2048
NET: Registered protocol family 16
<<<<<Register PCI Controller>>>>>
Do MDIO_RESET
40MHz
PCIE ->  Cannot LinkUP
Realtek GPIO controller driver init
INFO: registering sheipa spi device
bio: create slab <bio-0> at 0
INFO: sheipa spi driver register
INFO: sheipa spi probe
Switching to clocksource MIPS
NET: Registered protocol family 2
TCP established hash table entries: 2048 (order: 0, 16384 bytes)
TCP bind hash table entries: 2048 (order: -1, 8192 bytes)
TCP: Hash tables configured (established 2048 bind 2048)
TCP: reno registered
UDP hash table entries: 1024 (order: 0, 16384 bytes)
UDP-Lite hash table entries: 1024 (order: 0, 16384 bytes)
NET: Registered protocol family 1
squashfs: version 4.0 (2009/01/31) Phillip Lougher
msgmni has been set to 98
Block layer SCSI generic (bsg) driver version 0.4 loaded (major 254)
io scheduler noop registered (default)
Serial: 8250/16550 driver, 1 ports, IRQ sharing disabled
console [ttyS0] enabled, bootconsole disabled7) is a 16550A
console [ttyS0] enabled, bootconsole disabled
Realtek GPIO Driver for Flash Reload Default
loop: module loaded
m25p80 spi0.0: change speed to 15000000Hz, div 7
JEDEC id C84017
m25p80 spi0.0: found gd25q64, expected m25p80
flash vendor: GigaDevice
m25p80 spi0.0: gd25q64 (8192 Kbytes) (41000000 Hz)
2 rtkxxpart partitions found on MTD device m25p80
Creating 2 MTD partitions on "m25p80":
0x000000000000-0x000000800000 : "boot+cfg+linux+rootfs"
0x000000230000-0x000000800000 : "rootfs"
PPP generic driver version 2.4.2
NET: Registered protocol family 24
MPPE/MPPC encryption/compression module registered
Realtek WLAN driver - version 3.8.0(2017-12-26)(SVN:)
Adaptivity function - version 9.7.07
MACHAL_version_init
[MACFM_software_init 297]wifi hal support Mac function = 0x8008


#######################################################
SKB_BUF_SIZE=3032 MAX_SKB_NUM=768
#######################################################

[wlan0] init sae_peer_table
 [wlan0] init sae_blacklist_table
 [MACFM_software_init 297]wifi hal support Mac function = 0x8008
[MACFM_software_init 297]wifi hal support Mac function = 0x8008
[MACFM_software_init 297]wifi hal support Mac function = 0x8008
[MACFM_software_init 297]wifi hal support Mac function = 0x8008
[MACFM_software_init 297]wifi hal support Mac function = 0x8008
Netfilter messages via NETLINK v0.30.
nf_conntrack version 0.5.0 (785 buckets, 3140 max)
ip_tables: (C) 2000-2006 Netfilter Core Team
TCP: cubic registered
Twin IP Module Init
NET: Registered protocol family 17
NET: Registered protocol family 15
Ebtables v2.0 registered
8021q: 802.1Q VLAN Support v1.8
Realtek FastPath:v1.03

Probing RTL819X NIC-kenel stack size order[0]...
  SoC: 8197FH-VG
rtl8651_setAsicOperationLayer --> layer : 1
EFMD - MAX_PRE_ALLOC_RX_SKB = 2048
EFMD - rtl865x_maxPreAllocRxSkb = 2058
rtl8651_setAsicOperationLayer --> layer : 2
eth0 added. vid=9 Member port 0x11e...
eth1 added. vid=8 Member port 0x1...
rtl8651_setAsicOperationLayer --> layer : 3
[peth0] added, mapping to [eth1]...
m25p80 spi0.0: change speed to 41000000Hz, div 3
�������?���������VFS: Mounted root (squashfs filesystem) readonly on device 31:1.
Freeing unused kernel memory: 208K (805ac000 - 805e0000)
������� ��O�}����������ݟ�Start inittime
---> init fs
����---> init elog
��---> init dump_core
---> init version
�� ���Product ID:n602sr Version:15.258
---> init sys
��^_�����---> init sysctl
��/bin/sh: renice: not found
�?��enable 0 interval
����---> init restore_config
���  --> Restoring Config...
                --> 1st Config - �Default [No data in flash]
                 -- Default account : Do macfmt conversion admin/admin
                 -- mgmt access - credential patched : admin /  admin
                 -- patched (login --> removed)
                 -- patched (password --> removed)
���---> init restore_session
---> init nfrule
����������������������������������������������������������^]�---> init servd
��---> init config
��---> init ftm
ώ�---> init tz
��---> init gpio
  ---> gpio.init end
 ---> init mac
    =================================================================
    press magic key to change default setting ...
    LAN MAC : B0:38:6C:52:FE:C0
    WAN MAC : B0:38:6C:52:FE:C1
---> init bridge
---> init wireless
  ---> wl.preinit
killall: iwcontrol: no process killed
killall: iapp: no process killed
killall: wscd: no process killed
killall: iwcontrol: no process killed
killall: iapp: no process killed
killall: wscd: no process killed
        Scanning best channel for wl_mode:0 --->[ 1 ]
device wlan0-va0 is not a slave of br0
device wlan0-va1 is not a slave of br0
device wlan0-va2 is not a slave of br0
ifconfig: SIOCSIFHWADDR: Success
---> init iptables
  ---> NAT:enabled
---> init lan
---> init wan
---> init dns
---> init resume_lan
---> init iptables_chain
route: SIOCDELRT: No such process
---> init dos
---> init connctrl
  ---> init_connctrl
---> init disable_switch
  ---> wan port down
---> init switch
  ---> IPTV mode: 2
---> init enable_switch
  ---> wan port up
---> init port_config
---> init stacache
---> init portcache
---> init optimization
---> init resume_wan
---> init route
---> init services
killall: gpioctld: no process killed
killall: apcpd: no process killed
  ---> init_connctrl
---> Initialize HostName
---> Start station cache timer
killall: httpd: no process killed
rtcs:initial:3311,interval:21600
rtcs:initial:2755,interval:21600
[Service] Start sysled timer
Terminated
killall: auth: no process killed
killall: iwcontrol: no process killed
killall: iwcontrol: no process killed
killall: iapp: no process killed
killall: wscd: no process killed
Only WPA WPA2 WPA-Mixed support for 802.1x
killall: inotifywait: no process killed
killall: saved: no process killed
---> init easymesh
End inittime
Setting up watches.  Beware: since -r was given, this may take a while!
Watches established.
helper_timer_handler:Start wl_helper
killall: dhcpd.helper: no process killed
