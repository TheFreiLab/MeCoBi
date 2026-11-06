"""Guards against silently mixing runs of the trainers.

Two accidents this prevents (both happened):

1. A trainer was run on a different dataset / feature file (e.g. the multimetal one) without
   ``--tag-suffix``. Output names are keyed only by scheme + tag, so it overwrote
   ``mlp_doi_oof.csv`` / ``mlp_doi_metrics.json`` of the ruthenium benchmark, which then silently
   disagreed (different folds) with the LightGBM and DimeNet++ files of the same name family.
2. A DimeNet++/SchNet run resumed from checkpoints that were produced with other structures or
   another split, because the checkpoint folder is keyed by tag only.

``guard_run``       refuses a non-default input without ``--tag-suffix`` and refuses to overwrite
                    existing result files without ``--overwrite``.
``check_signature`` stamps a checkpoint folder with what produced it and refuses to resume into it
                    when that differs (``--fresh`` re-stamps).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _same(a, b) -> bool:
    return Path(a).resolve() == Path(b).resolve()


def guard_run(args, *, default_dataset, outputs=(), default_struct_map=None,
              default_manifest=None) -> None:
    """Abort (SystemExit) on a non-default input without --tag-suffix, or on overwriting results."""
    changed = []
    if not _same(args.dataset, default_dataset):
        changed.append(f"--dataset {args.dataset}")
    for name in ("features", "report"):
        if getattr(args, name, None) is not None:
            changed.append(f"--{name} {getattr(args, name)}")
    sm = getattr(args, "struct_map", None)
    if default_struct_map is not None and sm is not None and not _same(sm, default_struct_map):
        changed.append(f"--struct-map {sm}")
    if default_manifest is not None and getattr(args, "manifest", None) is not None \
            and not _same(args.manifest, default_manifest):
        changed.append(f"--manifest {args.manifest}")
    if getattr(args, "context", None) is not None:
        changed.append("--context " + " ".join(args.context))
    if changed and not args.tag_suffix:
        raise SystemExit(
            "Refusing to run: non-default input without --tag-suffix; outputs would overwrite the "
            "default benchmark files.\n  " + "\n  ".join(changed)
            + "\nAdd e.g. --tag-suffix multimetal (or xtb671).")
    existing = [Path(p) for p in outputs if Path(p).exists()]
    if existing and not getattr(args, "overwrite", False):
        raise SystemExit(
            "Refusing to overwrite existing results (pass --overwrite, or change --tag-suffix):\n  "
            + "\n  ".join(str(p) for p in existing))


def _sha1(path) -> str | None:
    p = Path(path) if path else None
    if p is None or not p.exists():
        return None
    return hashlib.sha1(p.read_bytes()).hexdigest()[:16]


def signature(args, manifest) -> dict:
    """What a checkpoint folder was produced from. n_seeds/folds are left out on purpose:
    resuming with more seeds or more folds is the normal use."""
    keys = ["scheme", "mode", "cell_line", "isomers_dir", "max_isomers", "aug_mode", "emb_dim",
            "head_hidden", "dropout", "lr", "weight_decay", "comp_batch", "epochs", "patience",
            "inner_val_frac", "seed", "with_ecfp", "context"]
    sig = {k: (str(getattr(args, k)) if getattr(args, k, None) is not None else None) for k in keys}
    enc = getattr(args, "dime", None) or getattr(args, "schnet", None) or {}
    sig["encoder"] = {k: str(v) for k, v in enc.items()}
    sig["struct_map"] = {"name": Path(args.struct_map).name, "sha1": _sha1(args.struct_map)}
    sig["manifest"] = {"name": Path(manifest).name, "sha1": _sha1(manifest)}
    sig["dataset"] = Path(args.dataset).name
    sig["features"] = {"name": Path(args.features).name if args.features else "default",
                       "sha1": _sha1(args.features) if args.features else None}
    return sig


def check_signature(ckdir, sig: dict, fresh: bool = False) -> None:
    f = Path(ckdir) / "run_signature.json"
    if f.exists() and not fresh:
        old = json.loads(f.read_text(encoding="utf-8"))
        diff = [k for k in sorted(set(old) | set(sig)) if old.get(k) != sig.get(k)]
        if diff:
            raise SystemExit(
                f"Checkpoint folder {ckdir} was produced with different settings; resuming would "
                "mix runs.\n  differs in: " + ", ".join(diff)
                + "\nUse another --tag-suffix, or --fresh to discard the old checkpoints.")
        return
    if not f.exists() and any(Path(ckdir).glob("fold*_seed*.npz")) and not fresh:
        print(f"  [guard] {ckdir} has checkpoints but no run_signature.json (older run): "
              "cannot verify, stamping with the current settings.", flush=True)
    f.write_text(json.dumps(sig, indent=2), encoding="utf-8")
