"""fac or mer for every Re(CO)3 structure in a directory of .xyz files (a CO is a C within 2.3 A of Re
whose only other neighbour is an O within 1.3 A; mer = one C-Re-C angle above 150 deg).

    python check_fac.py ../structures_fix6e0590a_refac/structures [re_mer_names.txt]
"""
import collections
import itertools
import sys
from pathlib import Path

import numpy as np

names = set(Path(sys.argv[2]).read_text().split()) if len(sys.argv) > 2 else None
count, mer = collections.Counter(), []
for f in sorted(Path(sys.argv[1]).glob("*.xyz")):
    if names is not None and f.stem not in names:
        continue
    lines = f.read_text().splitlines()
    rows = [ln.split() for ln in lines[2:2 + int(lines[0])]]
    sym = [r[0] for r in rows]
    if "Re" not in sym:
        continue
    x = np.array([[float(v) for v in r[1:4]] for r in rows])
    m = sym.index("Re")
    d = np.linalg.norm(x[:, None] - x[None], axis=2)
    co = [i for i, s in enumerate(sym) if s == "C" and d[m, i] < 2.3
          and [sym[j] for j in np.nonzero((d[i] < 1.9) & (d[i] > 0))[0] if j != m] == ["O"]]
    if len(co) != 3:
        count[f"{len(co)} CO"] += 1
        continue
    u = [(x[i] - x[m]) / d[m, i] for i in co]
    big = max(np.degrees(np.arccos(np.clip(u[a] @ u[b], -1, 1))) for a, b in itertools.combinations(range(3), 2))
    lab = "mer" if big > 150 else "fac"
    count[lab] += 1
    if lab == "mer":
        mer.append(f.stem)
print(dict(count))
if mer:
    print("mer:", " ".join(mer))
