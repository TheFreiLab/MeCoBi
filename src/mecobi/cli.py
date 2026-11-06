"""Command-line interface for the core library.

    mecobi build INPUT.csv --output-dir ./out [--all-isomers]

Local-only, no web deps. Thin wrapper over :mod:`mecobi.pipeline`.

``build`` writes one line per structure (its path) to stdout and everything else
(progress, warnings, failures, the closing summary) to stderr, and keeps going
past a complex that fails. Exit status: 0 when every complex built, 1 when one or
more failed (partial results are still written), 2 for a usage or input error
(bad ``--format``, unreadable CSV) before anything was built.
"""

from __future__ import annotations

import argparse
import sys

EXIT_OK = 0
EXIT_BUILD_FAILED = 1  # one or more complexes failed; the rest were still built
EXIT_USAGE = 2         # bad arguments or unreadable input; nothing was built


def _progress_reporter(index: int, total: int, label: str):
    """A ``build_complex`` progress callback that draws a one-line bar on stderr.

    On a TTY it redraws in place (carriage return); when stderr is redirected it
    stays silent so piped ``stdout`` (the .xyz paths) is not polluted. Returns
    ``(callback, clear)`` — call ``clear()`` before printing the result lines.
    """
    is_tty = sys.stderr.isatty()
    width = 20

    def draw(message: str) -> None:
        if not is_tty:
            return
        filled = int(width * index / total)
        bar = "#" * filled + "-" * (width - filled)
        line = f"\r[{index}/{total}] {bar} {label}: {message}"
        sys.stderr.write(line[:110].ljust(80))
        sys.stderr.flush()

    def clear() -> None:
        if is_tty:
            sys.stderr.write("\r" + " " * 80 + "\r")
            sys.stderr.flush()

    return draw, clear


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mecobi", description="Build metal-complex 3D structures.")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser(
        "build", help="Build complexes from a CSV.",
        epilog="Structure paths go to stdout; progress, warnings and failures to stderr. "
               "Exit status: 0 all complexes built, 1 one or more failed (the others are "
               "still written), 2 usage or input error.")
    build.add_argument("input", help="Path to the complexes CSV.")
    build.add_argument("--output-dir", default="./output", help="Where to write .xyz files.")
    build.add_argument("--all-isomers", action="store_true", help="Enumerate every isomer.")
    build.add_argument("--no-relax", dest="relax", action="store_false",
                       help="Skip the xtb relaxation (assembly + MCHammer only).")
    build.add_argument("--format", default="xyz",
                       help="Comma-separated output formats (default: xyz). Also supports "
                            "mol and pdb, e.g. --format xyz,mol,pdb. Connectivity for mol/pdb "
                            "comes from the assembled graph, coordinates from the built .xyz.")
    build.add_argument("--xtb-bin", default="xtb", help="xtb executable (default: on PATH).")
    build.set_defaults(relax=True)

    rev = sub.add_parser("reverse", help="Recover metal + ligand SMILES from an .xyz.")
    rev.add_argument("input", help="Path to a mononuclear metal-complex .xyz.")
    rev.add_argument("--notation", action="store_true",
                     help="Also print the donor-index isomer notation.")
    rev.add_argument("--backend", default="builtin",
                     choices=["builtin", "xyz2mol_tm"],
                     help="xyz->SMILES perception engine (default: builtin). "
                          "'xyz2mol_tm' (optional extra) also emits a whole-complex SMILES.")
    rev.add_argument("--charge", type=int, default=None,
                     help="Overall complex charge (required by --backend xyz2mol_tm, --trex "
                          "and --msmiles).")
    rev.add_argument("--trex", action="store_true",
                     help="Also print the T-REX notation (needs the optional trex package).")
    rev.add_argument("--msmiles", action="store_true",
                     help="Also print the MetalloGen m-SMILES (geometry + site-labelled donors).")

    args = parser.parse_args(argv)

    if args.command == "build":
        from . import export, inputs, pipeline

        try:
            formats = export.normalize_formats(args.format.split(","))
        except ValueError as exc:
            print(f"# {exc}", file=sys.stderr)
            return EXIT_USAGE
        try:
            complexes = inputs.parse_csv(args.input)
        except Exception as exc:
            print(f"# could not read {args.input}: {exc}", file=sys.stderr)
            return EXIT_USAGE
        total = len(complexes)
        failed: list[str] = []
        for idx, cx in enumerate(complexes, start=1):
            label = cx.name or cx.metal.symbol
            draw, clear = _progress_reporter(idx, total, label)
            try:
                results = pipeline.build_complex(
                    cx, args.output_dir,
                    all_isomers=args.all_isomers, relax=args.relax, xtb_bin=args.xtb_bin,
                    formats=formats, progress=draw,
                )
            except Exception as exc:  # keep going through the batch
                clear()
                failed.append(label)
                print(f"# FAILED {label}: {exc}", file=sys.stderr)
                continue
            clear()
            for r in results:
                suffix = ""
                if r.relative_energy_kcal is not None:
                    tag = "  *lowest*" if r.is_lowest_energy else ""
                    suffix = f"  (+{r.relative_energy_kcal:.2f} kcal/mol{tag})"
                elif not r.connectivity_ok:
                    suffix = "  (connectivity changed in relaxation; not ranked)"
                print(f"{r.xyz_path}{suffix}")
                for w in r.warnings:
                    print(f"  # {w}", file=sys.stderr)
        if failed:
            print(f"# {len(failed)} of {total} complexes failed: {', '.join(failed)}",
                  file=sys.stderr)
            return EXIT_BUILD_FAILED
        return EXIT_OK

    if args.command == "reverse":
        from . import reverse

        try:
            rc = reverse.reverse_xyz(args.input, backend=args.backend, overall_charge=args.charge)
        except Exception as exc:
            print(f"# FAILED: {exc}", file=sys.stderr)
            return 1
        print(f"metal: {rc.metal}  (CN {rc.coordination_number})")
        for lig in rc.ligands:
            print(f"  {lig.smiles}\tdonors={lig.donor_atoms}\tcharge={lig.charge}")
        if rc.complex_smiles:
            print(f"complex SMILES: {rc.complex_smiles}")
        if args.notation:
            print(f"notation: {rc.to_isomer_notation()}")
        if args.trex:
            try:
                print(f"T-REX: {reverse.to_trex(args.input, args.charge)}")
            except Exception as exc:
                print(f"# T-REX failed: {exc}", file=sys.stderr)
        if args.msmiles:
            try:
                print(f"m-SMILES: {reverse.to_msmiles(args.input, args.charge)}")
            except Exception as exc:
                print(f"# m-SMILES failed: {exc}", file=sys.stderr)
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
