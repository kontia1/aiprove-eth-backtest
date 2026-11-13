import csv, statistics, math

rows = list(csv.DictReader(open("bars.csv")))
C = [float(r["close"]) for r in rows]
N = len(C)
R = [0.0] + [C[i] / C[i - 1] - 1 for i in range(1, N)]

def run(pos, fee=0.0005, slip=0.0002):
    pnl = 0.0; prev = 0; trades = 0; peak = 0.0; mdd = 0.0
    for i in range(1, N):
        pnl += pos[i - 1] * R[i]
        if pos[i] != pos[i - 1]:
            pnl -= (fee + slip) * abs(pos[i] - pos[i - 1]); trades += 1
        peak = max(peak, pnl); mdd = max(mdd, peak - pnl)
    return pnl, trades, mdd

def vol_trend(k, enter_z, exit_z):
    """z = (close - SMA_k) / (sigma_k * close * sqrt(k)); regime flip with hysteresis."""
    pos = [0] * N; cur = 0
    for i in range(N):
        if i >= k + 1:
            m = sum(C[i - k:i]) / k
            sd = statistics.pstdev(R[i - k:i]) * C[i] * math.sqrt(k)
            z = (C[i] - m) / sd if sd > 0 else 0.0
            if cur <= 0 and z > enter_z: cur = 1
            elif cur >= 0 and z < -enter_z: cur = -1
            elif (cur == 1 and z < exit_z) or (cur == -1 and z > -exit_z): cur = 0
        pos[i] = cur
    return pos

print("-- vol-normalised trend (k, enter_z, exit_z) --")
best = []
for k in (60, 120, 240, 480):
    for ez in (0.5, 1.0, 1.5, 2.0):
        for xz in (-0.5, 0.0, 0.5):
            p, t, m = run(vol_trend(k, ez, xz))
            best.append((p, t, m, k, ez, xz))
            print(f"k={k:4d} ez={ez:4.1f} xz={xz:+.1f}  pnl={p*100:6.2f}%  trades={t:3d}  mdd={m*100:5.2f}%")
best.sort(reverse=True)
print("\ntop 5:", [(f"{p*100:.2f}%", t, k, ez, xz) for p, t, m, k, ez, xz in best[:5]])
