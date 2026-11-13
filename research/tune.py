import csv, statistics, math, importlib, sys
import strategy as S
import backtest as B

C = B.load_bars("bars.csv")
N = len(C)

def score(**kw):
    for k, v in kw.items():
        setattr(S, k, v)
    pos = S.signals(C)
    r = B.replay(C, pos)
    h = N // 2
    a = B.replay(C, pos, start=0, end=h)
    b = B.replay(C, pos, start=h, end=N)
    return r, a, b, pos

rows = []
for K in (60, 120, 240, 360):
    for ez in (0.5, 0.75, 1.0, 1.25):
        for xz in (0.0, 0.3, 0.6):
            for vk in (3.0, 4.0, 99.0):
                r, a, b, pos = score(K=K, ENTER_Z=ez, EXIT_Z=xz, VOL_KILL=vk)
                rows.append((r["net_pct"], r["max_dd_pct"], int(r["trades"]), K, ez, xz, vk,
                             a["net_pct"], b["net_pct"]))

rows.sort(reverse=True)
print(f"{'net':>7} {'dd':>5} {'tr':>3} {'K':>4} {'ez':>5} {'xz':>4} {'vk':>5} {'h1':>7} {'h2':>7}")
for r in rows[:20]:
    net, dd, tr, K, ez, xz, vk, h1, h2 = r
    print(f"{net:7.2f} {dd:5.2f} {tr:3d} {K:4d} {ez:5.2f} {xz:4.1f} {vk:5.1f} {h1:7.2f} {h2:7.2f}")

print("\nbaseline config:")
r, a, b, _ = score(K=240, ENTER_Z=1.0, EXIT_Z=0.3, VOL_KILL=4.0)
print(f"net={r['net_pct']:.2f} dd={r['max_dd_pct']:.2f} trades={r['trades']:.0f} h1={a['net_pct']:.2f} h2={b['net_pct']:.2f}")
