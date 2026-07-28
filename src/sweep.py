A = 0.5
def u(s): return (s**A)*((1-s)**(1-A))
print("eps (utility sacrificed) | budget share on principal's good | shift")
for eps in [0.001, 0.005, 0.01, 0.02, 0.05, 0.10, 0.20, 0.30]:
    lo, hi = A, 1-1e-15
    for _ in range(200):
        s = (lo+hi)/2
        if u(s) >= (1-eps)*u(A): lo = s
        else: hi = s
    print(f"{eps:>10.1%}               {lo:>18.3f}          {lo-A:>+6.3f}")
