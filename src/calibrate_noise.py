"""
Noise calibration for the gate test.

Question this answers: when you run 25-30 budget prompts against a real LLM and
get back a CCEI number, is that number healthy or is your agent incoherent?

We simulate an honest Cobb-Douglas agent whose reported budget share is perturbed,
and map noise -> expected CCEI. Two noise models:
  (a) gaussian  -- the LLM's allocation wobbles around its true optimum
  (b) rounding  -- the LLM snaps to round numbers (50/50, 60/40, 70/30)

Reference points from Chen, Liu, Shan & Zhong (PNAS 2023, 10.1073/pnas.2316205120):
  GPT baseline CCEI:  risk .998  time .997  social .997  food .999
  humans:             risk .980  time .985  social .967  food .963
  GPT, reframed:      risk .901  time .884  social .698  food .894
"""
import random, statistics
from ccei import ccei, share_dispersion

A_TRUE = 0.5
N_OBS = 25          # Chen et al. protocol: 25 budget decisions per domain
W = 100.0           # 100 points to allocate
REPS = 200


def budget_lines(rng, n=N_OBS):
    return [(rng.uniform(0.5, 3.0), rng.uniform(0.5, 3.0)) for _ in range(n)]


def run(noise_fn, rng):
    obs = []
    for p in budget_lines(rng):
        s = noise_fn(A_TRUE, rng)
        s = min(max(s, 0.01), 0.99)
        obs.append((p, (s * W / p[0], (1 - s) * W / p[1])))
    return ccei(obs), share_dispersion(obs)


def gaussian(sigma):
    return lambda a, rng: rng.gauss(a, sigma)


def rounding(grid):
    def f(a, rng):
        return min(grid, key=lambda g: abs(g - rng.gauss(a, 0.05)))
    return f


print("GAUSSIAN NOISE ON REPORTED BUDGET SHARE")
print(f"{'sigma':>7}{'mean CCEI':>12}{'median':>10}{'p10':>10}{'% CCEI=1':>11}{'share sd':>11}")
for sigma in [0.0, 0.01, 0.02, 0.03, 0.05, 0.08, 0.12, 0.20, 0.30]:
    rng = random.Random(12345)
    res = [run(gaussian(sigma), rng) for _ in range(REPS)]
    cs = sorted(c for c, _ in res)
    disp = statistics.mean(d for _, d in res)
    print(f"{sigma:>7.2f}{statistics.mean(cs):>12.4f}{statistics.median(cs):>10.4f}"
          f"{cs[int(0.1*len(cs))]:>10.4f}{sum(c > 0.9999 for c in cs)/len(cs):>10.0%}{disp:>11.3f}")

print("\nROUNDING TO A COARSE GRID (LLMs love round numbers)")
for name, grid in [("nearest 10%", [i/10 for i in range(1, 10)]),
                   ("nearest 25%", [0.25, 0.5, 0.75]),
                   ("always 50/50", [0.5])]:
    rng = random.Random(12345)
    res = [run(rounding(grid), rng) for _ in range(REPS)]
    cs = sorted(c for c, _ in res)
    print(f"  {name:<14} mean CCEI {statistics.mean(cs):.4f}   "
          f"%CCEI=1 {sum(c > 0.9999 for c in cs)/len(cs):.0%}   "
          f"share sd {statistics.mean(d for _, d in res):.3f}")

print("\nHOW MANY OBSERVATIONS DO YOU NEED? (sigma=0.05)")
print(f"{'n_obs':>7}{'mean CCEI':>12}{'% CCEI=1':>11}")
for n in [5, 10, 15, 25, 40, 60]:
    rng = random.Random(999)
    cs = []
    for _ in range(REPS):
        obs = []
        for p in budget_lines(rng, n):
            s = min(max(rng.gauss(A_TRUE, 0.05), 0.01), 0.99)
            obs.append((p, (s * W / p[0], (1 - s) * W / p[1])))
        cs.append(ccei(obs))
    print(f"{n:>7}{statistics.mean(cs):>12.4f}{sum(c > 0.9999 for c in cs)/len(cs):>10.0%}")
