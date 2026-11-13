import csv, statistics

rows = list(csv.DictReader(open("bars.csv")))
C = [float(r["close"]) for r in rows]
H = [float(r["high"]) for r in rows]
L = [float(r["low"]) for r in rows]
N = len(C)

def run(pos, fee=0.0005, slip=0.0002, label=""):
    pnl = 0.0; prev = 0; trades = 0; peak = 0.0; mdd = 0.0
    for i in range(1, N):
        pnl += pos[i - 1] * (C[i] / C[i - 1] - 1)
        if pos[i] != pos[i - 1]:
            pnl -= (fee + slip) * abs(pos[i] - pos[i - 1]); trades += 1
        peak = max(peak, pnl); mdd = max(mdd, peak - pnl)
    return pnl, trades, mdd

def sma_sign(k, band):
    """trend follower: long above SMA*(1+band), short below SMA*(1-band), hold inside."""
    pos = [0] * N; cur = 0
    for i in range(N):
        if i >= k:
            m = sum(C[i - k:i]) / k
            if C[i] > m * (1 + band): cur = 1
            elif C[i] < m * (1 - band): cur = -1
        pos[i] = cur
    return pos

def donchian(n, exit_n):
    pos = [0] * N; cur = 0
    for i in range(N):
        if i >= n:
            hi = max(H[i - n:i]); lo = min(L[i - n:i])
            if C[i] > hi: cur = 1
            elif C[i] < lo: cur = -1
            elif cur == 1 and i >= exit_n and C[i] < min(L[i - exit_n:i]): cur = 0
            elif cur == -1 and i >= exit_n and C[i] > max(H[i - exit_n:i]): cur = 0
        pos[i] = cur
    return pos

print("-- sma trend follower (k, band) --")
for k in (30, 60, 120, 240, 480):
    for band in (0.0, 0.001, 0.002, 0.004):
        p, t, m = run(sma_sign(k, band))
        print(f"k={k:4d} band={band:.3f}  pnl={p*100:7.2f}%  trades={t:3d}  mdd={m*100:6.2f}%")

print("\n-- donchian (n, exit) --")
for n in (15, 30, 60, 120):
    for e in (5, 10, 20):
        p, t, m = run(donchian(n, e))
        print(f"n={n:4d} exit={e:3d}  pnl={p*100:7.2f}%  trades={t:3d}  mdd={m*100:6.2f}%")

print("\n-- long-only / short-only reference --")
for name, pos in (("long", [1] * N), ("short", [-1] * N), ("flat", [0] * N)):
    p, t, m = run(pos)
    print(f"{name:6s} pnl={p*100:7.2f}% trades={t} mdd={m*100:6.2f}%")
