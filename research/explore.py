import csv, math, statistics

rows = list(csv.DictReader(open("bars.csv")))
C = [float(r["close"]) for r in rows]
O = [float(r["open"]) for r in rows]
H = [float(r["high"]) for r in rows]
L = [float(r["low"]) for r in rows]
V = [float(r["volume"]) for r in rows]
N = len(C)
FEE = 0.0005   # taker 5 bp per side
SLIP = 0.0002  # 2 bp per side

def run(pos, fee=FEE, slip=SLIP):
    """pos[i] = target position (-1,0,1) held over bar i (close->close)."""
    pnl = 0.0
    eq = [0.0]
    prev = 0
    trades = 0
    peak = 0.0
    mdd = 0.0
    for i in range(1, N):
        r = C[i] / C[i - 1] - 1
        pnl += pos[i - 1] * r
        if pos[i] != pos[i - 1]:
            pnl -= (fee + slip) * abs(pos[i] - pos[i - 1])
            trades += 1
        eq.append(pnl)
        peak = max(peak, pnl)
        mdd = max(mdd, peak - pnl)
    return pnl, trades, mdd, eq

def zs(series, k, i):
    w = series[i - k:i]
    if len(w) < k: return 0.0
    m = sum(w) / len(w)
    sd = statistics.pstdev(w)
    return 0.0 if sd == 0 else (series[i] - m) / sd

rets = [0.0] + [C[i] / C[i - 1] - 1 for i in range(1, N)]

def strat_mr(k, z, hold=1):
    pos = [0] * N
    i = 0
    cur = 0
    left = 0
    while i < N - 1:
        if left > 0:
            left -= 1
            pos[i] = cur
            i += 1
            continue
        zz = zs(rets, k, i)
        if zz < -z:
            cur, left = 1, hold
        elif zz > z:
            cur, left = -1, hold
        else:
            cur = 0
        pos[i] = cur
        i += 1
    pos[N - 1] = pos[N - 2]
    return pos

def strat_mom(k, thr=0.0):
    pos = [0] * N
    for i in range(k, N):
        m = C[i] / C[i - k] - 1
        pos[i] = 1 if m > thr else (-1 if m < -thr else 0)
    return pos

def strat_ema(fast, slow):
    pos = [0] * N
    ef = es = C[0]
    af, as_ = 2 / (fast + 1), 2 / (slow + 1)
    for i in range(N):
        ef += af * (C[i] - ef)
        es += as_ * (C[i] - es)
        pos[i] = 1 if ef > es else -1
    return pos

print("baseline buy&hold", (C[-1] / C[0] - 1) * 100, "%")
print("\n-- mean reversion (k, z, hold) --")
for k in (5, 10, 15, 20, 30):
    for z in (1.5, 2.0, 2.5, 3.0):
        for hold in (1, 3, 5, 10):
            p, t, mdd, _ = run(strat_mr(k, z, hold))
            if t > 0:
                print(f"k={k:3d} z={z:4.1f} h={hold:2d}  pnl={p*100:7.2f}%  trades={t:4d}  mdd={mdd*100:6.2f}%")

print("\n-- momentum --")
for k in (5, 10, 20, 30, 60):
    for thr in (0.0, 0.001, 0.002):
        p, t, mdd, _ = run(strat_mom(k, thr))
        print(f"k={k:3d} thr={thr:.3f}  pnl={p*100:7.2f}%  trades={t:4d}  mdd={mdd*100:6.2f}%")

print("\n-- ema cross --")
for f in (3, 5, 10, 20):
    for s in (20, 50, 100):
        p, t, mdd, _ = run(strat_ema(f, s))
        print(f"f={f:3d} s={s:3d}  pnl={p*100:7.2f}%  trades={t:4d}  mdd={mdd*100:6.2f}%")
