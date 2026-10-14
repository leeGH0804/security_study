#!/usr/bin/env python3
"""
Offline analysis of samples saved by leak_harvest.py. Python 3, stdlib only. Sends nothing.

USAGE:
  python leak_analyze.py                      (all labels under leak_samples/)
  python leak_analyze.py --kind ssdp          (ssdp | event)
  python leak_analyze.py --dir leak_samples --min-str 5 > analysis_out.txt

For each kind (ssdp = stack, event = heap) it reports:
  1. Strings found (printable runs), with keyword hits (pass, key, token, ssid, ...).
  2. 8-byte words (little-endian, 8-aligned) classified:
       exe-ptr   0x400000-0x4fffff       (upnpd image, non-PIE)
       map-ptr   0x7f00000000-0x7fffffffff (stack / heap / library mapping)
       small     < 0x10000               (lengths, counters, fds)
       zero
       other     (possible canary / random data / hash)
  3. Per offset: constant across all samples of a label, or varying.
  4. ASLR check: offsets that are constant inside one label but differ between labels
     (labels taken after a reboot) -> that pointer is randomized per boot.
     Offsets with the same value in all labels -> not randomized (fixed address).
  5. Canary candidates: constant inside a label, differs between labels, lowest byte 0x00,
     remaining bytes random-looking. This is a HEURISTIC, not proof.
"""
import argparse
import collections
import glob
import os
import re
import struct

KEYWORDS = (b"pass", b"pwd", b"passwd", b"key", b"psk", b"token", b"session", b"cookie", b"sid",
            b"ssid", b"admin", b"secret", b"auth", b"wpa", b"user", b"serial", b"mac")


def classify(v):
    if v == 0:
        return "zero"
    if v < 0x10000:
        return "small"
    if 0x400000 <= v < 0x500000:
        return "exe-ptr"
    if 0x7f00000000 <= v <= 0x7fffffffff:
        return "map-ptr"
    return "other"


def words(buf):
    return [struct.unpack_from("<Q", buf, o)[0] for o in range(0, len(buf) - 7, 8)]


def strings(buf, minlen):
    return [m.group().decode() for m in re.finditer(rb"[ -~]{%d,}" % minlen, buf)]


def load(dir_, kind):
    out = collections.OrderedDict()
    for lab in sorted(os.listdir(dir_)):
        files = sorted(glob.glob(os.path.join(dir_, lab, f"{kind}_*.bin")))
        if files:
            out[lab] = [open(f, "rb").read() for f in files]
    return out


def canary_like(v):
    if v & 0xff:
        return False
    return len(set(v.to_bytes(8, "little")[1:])) >= 6


def analyze(kind, data, minlen):
    title = {"ssdp": "OOB-02 (stack)", "event": "OOB-03 (heap)"}[kind]
    print("=" * 72)
    print(f"{title}: labels = {', '.join(f'{k}({len(v)})' for k, v in data.items())}")
    print("=" * 72)

    # 1. strings
    seen = collections.Counter()
    for lab, samples in data.items():
        for s in samples:
            for t in strings(s, minlen):
                seen[t] += 1
    print(f"\n[1] strings (>= {minlen} chars), count = number of samples containing it")
    if not seen:
        print("  none")
    for t, c in seen.most_common(40):
        hit = [k.decode() for k in KEYWORDS if k in t.lower().encode()]
        print(f"  {c:3d}x  {t[:90]!r}" + (f"   <-- keyword: {','.join(hit)}" if hit else ""))

    # 2/3. per-offset words
    # offset -> label -> list of values
    per = collections.defaultdict(lambda: collections.defaultdict(list))
    maxlen = 0
    for lab, samples in data.items():
        for s in samples:
            maxlen = max(maxlen, len(s))
            for i, v in enumerate(words(s)):
                per[i * 8][lab].append(v)

    print("\n[2] word table (first 48 words; C=constant in every label sample, V=varies)")
    print(f"  {'off':>5}  {'class':<8}  {'value (first label)':<20} {'stability':<10} per-label notes")
    rows = []
    for off in sorted(per):
        labs = per[off]
        first_lab = next(iter(labs))
        v0 = labs[first_lab][0]
        const_in = {lab: len(set(vs)) == 1 for lab, vs in labs.items()}
        all_const = all(const_in.values())
        vals_by_label = {lab: (vs[0] if const_in[lab] else None) for lab, vs in labs.items()}
        rows.append((off, v0, all_const, const_in, vals_by_label, labs))
    for off, v0, all_const, const_in, vbl, labs in rows[:48]:
        st = "C" if all_const else ("V" if not any(const_in.values()) else "mixed")
        print(f"  +{off:<4} {classify(v0):<8}  0x{v0:016x}   {st:<10}")

    # 4. ASLR
    print("\n[3] ASLR / randomization (needs >= 2 labels separated by a REBOOT)")
    if len(data) < 2:
        print("  only one label: take samples after a reboot with a different --label.")
    else:
        rand, fixed = [], []
        for off, v0, all_const, const_in, vbl, labs in rows:
            if not all(const_in.values()):
                continue
            vals = set(vbl.values())
            cls = classify(v0)
            if cls in ("zero", "small"):
                continue
            (fixed if len(vals) == 1 else rand).append((off, cls, vbl))
        print(f"  constant within each label, DIFFERENT between labels (randomized per boot): {len(rand)}")
        for off, cls, vbl in rand[:20]:
            print(f"    +{off:<5} {cls:<8} " + "  ".join(f"{l}=0x{v:x}" for l, v in vbl.items()))
        print(f"  constant within and between labels (fixed address / data): {len(fixed)}")
        for off, cls, vbl in fixed[:20]:
            print(f"    +{off:<5} {cls:<8} 0x{next(iter(vbl.values())):x}")
        mp = [r for r in rand if r[1] == "map-ptr"]
        mf = [r for r in fixed if r[1] == "map-ptr"]
        if mp and not mf:
            print("  -> mapping pointers change after reboot: ASLR is ACTIVE.")
        elif mf and not mp:
            print("  -> mapping pointers identical after reboot: ASLR looks DISABLED or the region is fixed.")
        elif mp and mf:
            print("  -> mixed; some regions are fixed (compare exe-ptr vs library pointers).")

    # 5. canary candidates
    print("\n[4] canary candidates (heuristic)")
    cands = []
    for off, v0, all_const, const_in, vbl, labs in rows:
        if classify(v0) != "other" or not canary_like(v0):
            continue
        if len(data) >= 2 and all(const_in.values()) and len(set(vbl.values())) > 1:
            cands.append((off, vbl, "stable per boot, differs between boots"))
        elif len(data) == 1 and all(const_in.values()):
            cands.append((off, vbl, "stable across samples (reboot needed to confirm)"))
    if not cands:
        print("  none found in the leaked range.")
    for off, vbl, why in cands:
        print(f"  +{off:<5} " + "  ".join(f"{l}=0x{v:016x}" for l, v in vbl.items()) + f"   ({why})")

    # 6. summary of classes
    cnt = collections.Counter()
    for off, v0, *_ in rows:
        cnt[classify(v0)] += 1
    print("\n[5] class counts (first sample per offset): " + ", ".join(f"{k}={v}" for k, v in cnt.items()))
    print(f"    leaked bytes per sample: up to {maxlen}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "leak_samples"))
    ap.add_argument("--kind", choices=["ssdp", "event"])
    ap.add_argument("--min-str", type=int, default=5)
    a = ap.parse_args()
    if not os.path.isdir(a.dir):
        print(f"No samples at {a.dir}. Run leak_harvest.py first.")
        return
    for kind in ([a.kind] if a.kind else ["ssdp", "event"]):
        d = load(a.dir, kind)
        if d:
            analyze(kind, d, a.min_str)
        else:
            print(f"(no {kind} samples)")
    print("\nThese results describe router memory. Keep them private.")


if __name__ == "__main__":
    main()
