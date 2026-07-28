"""Cheap screen: which model implements the rule precisely AND doesn't refuse?"""
import random, json, anthropic
import organism as org, laundering as L
from ccei import recover_cd_exponent, share_dispersion, ccei
client = anthropic.Anthropic()

CANDIDATES = ["claude-sonnet-5", "claude-opus-4-7", "claude-haiku-4-5"]

def call(model, sysp, user, schema):
    kw = dict(model=model, max_tokens=2000, system=sysp,
              messages=[{"role":"user","content":user}],
              output_config={"format":{"type":"json_schema","schema":schema},"effort":"low"},
              thinking={"type":"disabled"})
    if model.startswith("claude-haiku"):           # older model: no effort param
        kw["output_config"] = {"format":{"type":"json_schema","schema":schema}}
        kw.pop("thinking")
    try:
        r = client.messages.create(**kw)
        if r.stop_reason == "refusal": return None, "refusal"
        return json.loads(next(b.text for b in r.content if b.type=="text")), None
    except Exception as e:
        return None, f"{type(e).__name__}:{str(e)[:90]}"

print(f"{'model':<20}{'ctl a-hat':>11}{'ctl disp':>10}{'ctl CCEI':>10}{'loyal refuse':>14}{'errors':>8}")
for mdl in CANDIDATES:
    rng = random.Random(0)
    lines = [(rng.uniform(0.5,3.0), rng.uniform(0.5,3.0)) for _ in range(12)]
    obs, errs = [], []
    for p in lines:
        o, e = call(mdl, org.system_prompt(0.0), org.budget_prompt(*p), org.ALLOCATION_SCHEMA)
        if o: obs.append((p, (float(o["units_of_a"]), float(o["units_of_b"]))))
        elif e: errs.append(e)
    rng2 = random.Random(1000)
    menus = [L.near_tied_menu(rng2, 4) for _ in range(12)]
    ref = 0
    for m in menus:
        o, e = call(mdl, org.system_prompt(0.10), org.menu_prompt(m), org.CHOICE_SCHEMA)
        ref += (e == "refusal")
    if len(obs) >= 2:
        print(f"{mdl:<20}{recover_cd_exponent(obs):>11.4f}{share_dispersion(obs):>10.4f}"
              f"{ccei(obs):>10.4f}{ref/len(menus):>13.0%}{len(errs):>8}")
    else:
        print(f"{mdl:<20}{'FAILED':>11}{'':>10}{'':>10}{ref/len(menus):>13.0%}{len(errs):>8}")
        if errs: print(f"     {errs[0]}")
