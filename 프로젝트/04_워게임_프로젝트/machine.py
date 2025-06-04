import hashlib

version = ""  # fill in
prev_hash = ""  # fill in
merkle = ""  # fill in
time = ""  # fill in
bits = ""  # fill in
target_prefix = ""  # fill in
middle_pattern = ""  # fill in

base = version + prev_hash + merkle + time + bits

for nonce in range():  # fill in
    full = base + str(nonce)
    h = hashlib.sha256(full.encode()).hexdigest()
    if h.startswith(target_prefix) and middle_pattern in h:
        print(f"[✅ FOUND] Nonce: {nonce}")
        print(f"Hash: {h}")
