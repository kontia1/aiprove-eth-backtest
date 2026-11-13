"""Trend-regime strategy for the frozen ETH 1-minute dataset.

Signal: vol-normalised distance of price from its slow mean.

    z[i] = (close[i] - SMA_k[i]) / (sigma_k[i] * close[i] * sqrt(k))

where sigma_k is the stdev of 1-minute returns over the same window, so z is
scale-free: +2 means "price sits two standard deviations of the k-bar random
walk above its own mean", regardless of ETH's price level or volatility regime.

Regime (hysteresis, so we do not churn on noise):
    z >  ENTER_Z   -> long   (+1)
    z < -ENTER_Z   -> short  (-1)
    |z| < EXIT_Z   -> flat   (0)
    otherwise      -> hold previous regime

Risk gates:
    * flat while warm-up (first k bars) - no lookahead, no early guesswork
    * flat when the realised vol is above VOL_KILL x its slow median
    * never more than MAX_FLIPS regime flips per hour (cost control)

The position emitted at bar i is the target held over bar i+1's return.
"""

import math
import statistics
import sys

K = 240
ENTER_Z = 0.5
EXIT_Z = 0.0
VOL_WIN = 60
VOL_KILL = 4.0
MAX_FLIPS = 6


def _sma(xs, k, i):
    return sum(xs[i - k:i]) / k


def signals(closes):
    n = len(closes)
    rets = [0.0] + [closes[i] / closes[i - 1] - 1 for i in range(1, n)]
    pos = [0.0] * n
    cur = 0.0
    flips = []
    vol_hist = []

    for i in range(n):
        if i < K + 1:
            pos[i] = 0.0
            continue
        win = rets[i - K:i]
        sd = statistics.pstdev(win)
        mean = _sma(closes, K, i)
        scale = sd * closes[i] * math.sqrt(K)
        z = (closes[i] - mean) / scale if scale > 0 else 0.0

        v = statistics.pstdev(rets[i - VOL_WIN:i]) if i >= VOL_WIN else 0.0
        vol_hist.append(v)
        vmed = statistics.median(vol_hist[-480:]) if vol_hist else 0.0
        risk_off = vmed > 0 and v > VOL_KILL * vmed

        want = cur
        if risk_off:
            want = 0.0
        elif z > ENTER_Z:
            want = 1.0
        elif z < -ENTER_Z:
            want = -1.0
        elif abs(z) < EXIT_Z:
            want = 0.0

        if want != cur:
            flips = [f for f in flips if i - f < 60]
            if len(flips) < MAX_FLIPS or want == 0.0:
                flips.append(i)
                cur = want
        pos[i] = cur

    return pos


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "bars.csv"
    with open(path) as f:
        head = f.readline().strip().split(",")
        ci = head.index("close")
        closes = [float(line.split(",")[ci]) for line in f if line.strip()]
    pos = signals(closes)
    out = sys.stdout
    out.write("minute,position\n")
    for i, p in enumerate(pos):
        out.write(f"{i},{p:g}\n")


if __name__ == "__main__":
    main()
