data = "aa550600ed452c197d"

data = bytes.fromhex(data)

tmp = 0
for b in data[:-1]:
    tmp ^= b
    print(f"{tmp:08b}")

print(f"{tmp:02X}")