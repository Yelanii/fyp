"""Compare two FreshQA snapshots matched by QUESTION TEXT (ids are reassigned between versions).
Output: how many answers a stale snapshot gets wrong today (natural, silent degradation)."""
import csv, re, sys, json, collections
def load(f):
    rows = list(csv.reader(open(f, encoding='utf-8')))
    h = rows[2]; out = []
    for r in rows[3:]:
        if r and r[0].strip():
            out.append(dict(zip(h, r)))
    return out
norm = lambda t: re.sub(r'[^a-z0-9]+', ' ', t.lower()).strip()
answers = lambda d: [d[f'answer_{k}'] for k in range(10) if d[f'answer_{k}'].strip()]
old, new = load(sys.argv[1]), load(sys.argv[2])
oldq = {norm(d['question']): d for d in old}
res, unmatched = [], []
for n in new:
    o = oldq.get(norm(n['question']))
    if o is None:
        unmatched.append(n['question']); continue
    oa, na = [norm(a) for a in answers(o)], [norm(a) for a in answers(n)]
    res.append(dict(fact=n['fact_type'], split=n['split'], fp=n['false_premise'],
                    changed=set(oa) != set(na),
                    stale_wrong=not (oa and oa[0] in na),          # stale tool's main answer no longer accepted
                    q=n['question'], old0=answers(o)[0] if oa else '', new0=answers(n)[0] if na else ''))
json.dump(dict(rows=res, unmatched=unmatched), open(sys.argv[3], 'w'), indent=1)
N = len(res)
print(f'new questions: {len(new)}; matched by text: {N}; reworded or new (unmatched): {len(unmatched)}')
for key in ('fact', 'fp'):
    c = collections.defaultdict(lambda: [0, 0])
    for r in res: c[r[key]][0] += 1; c[r[key]][1] += r['stale_wrong']
    print(f'by {key}:')
    for g, (n_, sw) in sorted(c.items()):
        print(f'  {g:15s} n={n_:3d}  stale main answer no longer accepted: {sw:3d} ({sw/n_:.1%})')
sw = sum(r['stale_wrong'] for r in res); ch = sum(r['changed'] for r in res)
print(f'ALL matched: answer set changed {ch}/{N} ({ch/N:.1%}); stale main answer no longer accepted {sw}/{N} ({sw/N:.1%})')
