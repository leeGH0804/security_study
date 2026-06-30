```
PS C:\WINDOWS\system32> usbipd list
Connected:
BUSID  VID:PID    DEVICE                                                        STATE
1-3    1a86:5512  USB UART-LPT                                                  Shared
1-5    04e8:730b  CanvasBio Fingerprint Driver                                  Not shared
1-6    2b7e:0134  720p HD Camera                                                Not shared
1-10   8087:0026  인텔(R) 무선 Bluetooth(R)                                     Not shared
1-13   0bda:8153  Realtek USB GbE Family Controller #2                          Not shared

Persisted:
GUID                                  DEVICE

PS C:\WINDOWS\system32> usbipd attach --wsl --busid 1-3
usbipd: info: Using WSL distribution 'Ubuntu' to attach; the device will be available in all WSL 2 distributions.
usbipd: info: Loading vhci_hcd module.
usbipd: info: Detected networking mode 'nat'.
usbipd: info: Using IP address 172.31.176.1 to reach the host.
```

```
dlrlf@LGH:/mnt/c/Users/dlrlf$ sudo flashrom -p ch341a_spi
flashrom unknown on Linux 6.6.87.2-microsoft-standard-WSL2 (x86_64)
flashrom is free software, get the source code at https://flashrom.org

Using clock_gettime for delay loops (clk_id: 1, resolution: 1ns).
Found GigaDevice flash chip "GD25Q64(B)" (8192 kB, SPI) on ch341a_spi.
No operations were specified.
dlrlf@LGH:/mnt/c/Users/dlrlf$ sudo flashrom -p ch341a_spi -r iptime_dump_1.bin
flashrom unknown on Linux 6.6.87.2-microsoft-standard-WSL2 (x86_64)
flashrom is free software, get the source code at https://flashrom.org

Using clock_gettime for delay loops (clk_id: 1, resolution: 1ns).
Found GigaDevice flash chip "GD25Q64(B)" (8192 kB, SPI) on ch341a_spi.
Reading flash... done.

dlrlf@LGH:/mnt/c/Users/dlrlf$ binwalk iptime_dump_1.bin

DECIMAL       HEXADECIMAL     DESCRIPTION
--------------------------------------------------------------------------------
35604         0x8B14          CRC32 polynomial table, little endian
39520         0x9A60          gzip compressed data, maximum compression, from Unix, last modified: 2024-07-18 01:30:40
272480        0x42860         LZMA compressed data, properties: 0x5D, dictionary size: 8388608 bytes, uncompressed size: 6115028 bytes
2293760       0x230000        Squashfs filesystem, little endian, version 4.0, compression:xz, size: 5867940 bytes, 831 inodes, blocksize: 131072 bytes, created: 2025-09-22 04:53:19

dlrlf@LGH:/mnt/c/Users/dlrlf$ binwalk -e iptime_dump_1.bin

DECIMAL       HEXADECIMAL     DESCRIPTION
--------------------------------------------------------------------------------
35604         0x8B14          CRC32 polynomial table, little endian
39520         0x9A60          gzip compressed data, maximum compression, from Unix, last modified: 2024-07-18 01:30:40
272480        0x42860         LZMA compressed data, properties: 0x5D, dictionary size: 8388608 bytes, uncompressed size: 6115028 bytes

WARNING: Extractor.execute failed to run external extractor 'sasquatch -p 1 -le -d 'squashfs-root-0' '%e'': [Errno 2] No such file or directory: 'sasquatch', 'sasquatch -p 1 -le -d 'squashfs-root-0' '%e'' might not be installed correctly

WARNING: Extractor.execute failed to run external extractor 'sasquatch -p 1 -be -d 'squashfs-root-0' '%e'': [Errno 2] No such file or directory: 'sasquatch', 'sasquatch -p 1 -be -d 'squashfs-root-0' '%e'' might not be installed correctly

WARNING: Symlink points outside of the extraction directory: /mnt/c/Users/dlrlf/_iptime_dump_1.bin.extracted/squashfs-root/etc -> /tmp/etc; changing link target to /dev/null for security purposes.

WARNING: Symlink points outside of the extraction directory: /mnt/c/Users/dlrlf/_iptime_dump_1.bin.extracted/squashfs-root/linuxrc -> /usr/bin/busybox; changing link target to /dev/null for security purposes.

WARNING: Symlink points outside of the extraction directory: /mnt/c/Users/dlrlf/_iptime_dump_1.bin.extracted/squashfs-root/mnt -> /tmp/mnt; changing link target to /dev/null for security purposes.

WARNING: Symlink points outside of the extraction directory: /mnt/c/Users/dlrlf/_iptime_dump_1.bin.extracted/squashfs-root/var -> /tmp/var; changing link target to /dev/null for security purposes.

WARNING: Symlink points outside of the extraction directory: /mnt/c/Users/dlrlf/_iptime_dump_1.bin.extracted/squashfs-root/cgibin/d.cgi -> /home/httpd/cgi/d.cgi; changing link target to /dev/null for security purposes.

WARNING: Symlink points outside of the extraction directory: /mnt/c/Users/dlrlf/_iptime_dump_1.bin.extracted/squashfs-root/home/httpd/captcha -> /tmp/captcha; changing link target to /dev/null for security purposes.

WARNING: Symlink points outside of the extraction directory: /mnt/c/Users/dlrlf/_iptime_dump_1.bin.extracted/squashfs-root/home/httpd/192.168.0.1/build_date -> /home/httpd/build_date; changing link target to /dev/null for security purposes.

WARNING: Symlink points outside of the extraction directory: /mnt/c/Users/dlrlf/_iptime_dump_1.bin.extracted/squashfs-root/home/httpd/192.168.0.1/captcha -> /home/httpd/captcha; changing link target to /dev/null for security purposes.

WARNING: Symlink points outside of the extraction directory: /mnt/c/Users/dlrlf/_iptime_dump_1.bin.extracted/squashfs-root/home/httpd/192.168.0.1/index.html -> /home/httpd/index.html; changing link target to /dev/null for security purposes.

WARNING: Symlink points outside of the extraction directory: /mnt/c/Users/dlrlf/_iptime_dump_1.bin.extracted/squashfs-root/home/httpd/192.168.0.1/version -> /home/httpd/version; changing link target to /dev/null for security purposes.

WARNING: Symlink points outside of the extraction directory: /mnt/c/Users/dlrlf/_iptime_dump_1.bin.extracted/squashfs-root/sbin/checkbootparam -> /usr/sbin/freebox; changing link target to /dev/null for security purposes.

WARNING: Symlink points outside of the extraction directory: /mnt/c/Users/dlrlf/_iptime_dump_1.bin.extracted/squashfs-root/sbin/flash -> /usr/sbin/freebox; changing link target to /dev/null for security purposes.

WARNING: Symlink points outside of the extraction directory: /mnt/c/Users/dlrlf/_iptime_dump_1.bin.extracted/squashfs-root/sbin/iptables-xml -> /usr/sbin/xtables-multi; changing link target to /dev/null for security purposes.

WARNING: Symlink points outside of the extraction directory: /mnt/c/Users/dlrlf/_iptime_dump_1.bin.extracted/squashfs-root/sbin/nvshow -> /usr/sbin/freebox; changing link target to /dev/null for security purposes.

WARNING: Symlink points outside of the extraction directory: /mnt/c/Users/dlrlf/_iptime_dump_1.bin.extracted/squashfs-root/sbin/phy -> /usr/sbin/freebox; changing link target to /dev/null for security purposes.

WARNING: Symlink points outside of the extraction directory: /mnt/c/Users/dlrlf/_iptime_dump_1.bin.extracted/squashfs-root/sbin/rtl -> /usr/sbin/freebox; changing link target to /dev/null for security purposes.

WARNING: Symlink points outside of the extraction directory: /mnt/c/Users/dlrlf/_iptime_dump_1.bin.extracted/squashfs-root/usr/sbin/brctl -> /usr/sbin/brctl; changing link target to /dev/null for security purposes.

WARNING: Symlink points outside of the extraction directory: /mnt/c/Users/dlrlf/_iptime_dump_1.bin.extracted/squashfs-root/usr/sbin/route -> /usr/sbin/route; changing link target to /dev/null for security purposes.
2293760       0x230000        Squashfs filesystem, little endian, version 4.0, compression:xz, size: 5867940 bytes, 831 inodes, blocksize: 131072 bytes, created: 2025-09-22 04:53:19


```

