"""Input parsing — CSV / direct spec -> :class:`~mecobi.model.Complex`.

Row = one whole complex. The vision's canonical form is positional
(``metal, oxidation_state, SMILES_1, SMILES_2, ...``); the prototype CSVs use
named slots (``Metal, Charge, L1..L6, Name, Index``). This module normalises
either shape so the rest of the core never sees CSV quirks. Ligands are listed
individually — repeated ligands appear multiple times; there is no count column.

Oxidation state is required: a row missing it is a hard error, not
a silent default. Per-job caps (max 1000 rows) are enforced by the
caller/web layer, not here.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from rdkit import Chem

from .model import Complex, Ligand, Metal

_L_SLOT = re.compile(r"^L\d+$", re.IGNORECASE)
# Words that mark a CSV's first row as a header (plus L1/L2/... slot names). Shared by the
# CLI reader below and the web reader, so both decide "is there a header?" the same way.
HEADER_TOKENS = frozenset({"metal", "charge", "oxidation_state", "oxidation", "name", "index",
                           "complex_id"})


def is_header_row(cells) -> bool:
    """True if a CSV row is a header (contains a known column name or an L-slot)."""
    return any(str(c).strip().lower() in HEADER_TOKENS or _L_SLOT.match(str(c).strip())
               for c in cells)
_PERIODIC = Chem.GetPeriodicTable()

# Small inorganic ligands users often write as neutral radicals when they mean a
# closed-shell anion (RDKit then gets the charge AND the unpaired-electron count
# wrong, so xtb ejects/distorts the ligand). Keyed by canonical SMILES of the
# problematic input -> chemically correct SMILES.
_SMILES_NORMALIZATIONS = {
    # Carbon monoxide. Plain 'CO' is methanol, so users write '[C]#[O+]' — but
    # RDKit reads that as a +1 *radical cation* (CO+). '[C-]#[O+]' is neutral,
    # closed-shell CO with the same C donor atom (index 0).
    "[C]#[O+]": "[C-]#[O+]",
    # Nitrite. 'O=[N+][O-]' is the neutral NO2 *radical* (charge 0, 1 unpaired e).
    # 'O=N[O-]' is the closed-shell nitrite anion NO2- (charge -1), the intended
    # coordinating ligand; same N donor atom (index 1).
    "O=[N+][O-]": "O=N[O-]",
}

# Unambiguous non-coordinating counterions that pad out a written complex but
# never bind the metal. Dropped at parse time so they don't inflate the ligand
# count / coordination number, and so the total charge reflects only the real
# coordination sphere. Bare halides (Cl-/Br-/I-) are DELIBERATELY EXCLUDED — they
# coordinate as often as they float, so stripping them would silently change the
# chemistry. Keyed by canonical SMILES (see _COUNTERION_CANON below).
_COUNTERION_SMILES = (
    # Alkali counter-cations.
    "[Na+]", "[K+]", "[Li+]", "[Cs+]",
    # Classic weakly-coordinating anions.
    "F[P-](F)(F)(F)(F)F",              # PF6-
    "[B-](F)(F)(F)F",                  # BF4-
    "[O-]Cl(=O)(=O)=O",                # ClO4-
    "[O-]S(=O)(=O)C(F)(F)F",           # triflate / OTf- (CF3SO3-)
    "F[Sb-](F)(F)(F)(F)F",             # SbF6-
    # BArF: tetrakis[3,5-bis(trifluoromethyl)phenyl]borate.
    "[B-](c1cc(cc(c1)C(F)(F)F)C(F)(F)F)(c1cc(cc(c1)C(F)(F)F)C(F)(F)F)"
    "(c1cc(cc(c1)C(F)(F)F)C(F)(F)F)c1cc(cc(c1)C(F)(F)F)C(F)(F)F",
)

# Canonicalised so whitespace / atom-ordering variants of the same ion all match.
_COUNTERION_CANON = frozenset(
    Chem.MolToSmiles(m)
    for s in _COUNTERION_SMILES
    if (m := Chem.MolFromSmiles(s)) is not None
)


def is_counterion(smiles: str) -> bool:
    """True if ``smiles`` is one of the unambiguous non-coordinating counterions.

    Used to strip spectator ions (alkali cations, PF6-/BF4-/ClO4-/OTf-/SbF6-/
    BArF) from the ligand list before building. Bare halides are not treated as
    counterions (they often coordinate); unrecognised input is not a counterion.
    """
    mol = Chem.MolFromSmiles(smiles.strip())
    if mol is None:
        return False
    return Chem.MolToSmiles(mol) in _COUNTERION_CANON


class InputError(ValueError):
    """Raised for malformed complex input (missing metal, oxidation state, etc.)."""


def radical_electrons(smiles: str) -> int:
    """Unpaired electrons in a (normalised) ligand SMILES; 0 if closed-shell.

    Small inorganic ligands are often mistyped as neutral radicals when an anion
    is meant (CO, nitrite, halides): the charge and spin then come out wrong and
    xtb misbehaves. Known cases are auto-normalised; anything still radical after
    normalisation is flagged to the user (see the web parse warning).
    """
    mol = Chem.MolFromSmiles(normalize_smiles(smiles))
    if mol is None:
        return 0
    return sum(a.GetNumRadicalElectrons() for a in mol.GetAtoms())


def radical_warning(smiles: str) -> str | None:
    """A user-facing warning if a ligand parses as a radical, else None."""
    n = radical_electrons(smiles)
    if n:
        return (f"{smiles} parses as a radical ({n} unpaired e) — did you mean an anion? "
                f"Total charge and spin (--uhf) may be wrong.")
    return None


def normalize_smiles(smiles: str) -> str:
    """Correct common mis-written ligand SMILES (e.g. CO as ``[C]#[O+]``).

    Matches on canonical SMILES so whitespace/atom-ordering variants are caught.
    Unrecognised input is returned unchanged.
    """
    s = smiles.strip()
    mol = Chem.MolFromSmiles(s)
    if mol is None:
        return s
    return _SMILES_NORMALIZATIONS.get(Chem.MolToSmiles(mol), s)


def _as_symbol(value) -> str | None:
    """The element symbol ``value`` spells (loose casing: 'fe'/'FE' -> 'Fe'), else None.

    Symbols only: an atomic number ('78') is not accepted as a metal.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if text in _ELEMENT_SYMBOLS:
        return text
    capitalized = text.capitalize()
    return capitalized if capitalized in _ELEMENT_SYMBOLS else None


def _resolve_symbol(value) -> str:
    """Element symbol (``'Ir'``, loose casing tolerated) -> canonical symbol.

    A typo'd metal is flagged at parse (a clear row error) rather than surfacing
    later as a raw "stk has no metal atom class" build failure.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        raise InputError("Missing metal.")
    text = str(value).strip()
    if not text:
        raise InputError("Missing metal.")
    symbol = _as_symbol(text)
    if symbol is not None:
        return symbol
    try:
        float(text)
    except ValueError:
        raise InputError(
            f"{text!r} is not an element symbol. Start the line with a metal symbol, e.g. Pt."
        ) from None
    raise InputError(f"{text!r} is not an element symbol. Use the symbol instead, e.g. Pt.")


def _whole_number(value) -> int | None:
    """``value`` as an int if it is a whole number ('2', '+3', 2.0), else None."""
    try:
        number = float(str(value).strip())
    except (ValueError, TypeError):
        return None
    return int(number) if number.is_integer() else None


def _oxidation_state(value) -> int:
    if value is None or (isinstance(value, float) and pd.isna(value)) or str(value).strip() == "":
        raise InputError("Oxidation state missing. Put it after the metal, e.g. Pt, 2, …")
    number = _whole_number(value)
    if number is None:
        raise InputError(
            f"Oxidation state {str(value).strip()!r} isn't a whole number. "
            "Put it after the metal, e.g. Pt, 2, …")
    return number


def _assign_unique_names(complexes: list[Complex]) -> None:
    """Ensure every complex has a unique, non-empty name (in place).

    A provided name is kept; a missing one is generated as ``{metal}_{seq}`` from
    its row position. Any resulting collision (including duplicate *provided*
    names) is disambiguated with a numeric suffix, so distinct complexes never
    share a name — otherwise their output ``.xyz`` files would silently overwrite
    each other when a batch is built into one directory.
    """
    used: set[str] = set()
    for i, cx in enumerate(complexes):
        base = cx.name or f"{cx.metal.symbol}_{i + 1:02d}"
        name, n = base, 2
        while name in used:
            name = f"{base}_{n}"
            n += 1
        used.add(name)
        cx.name = name


def _make_ligand(smiles: str) -> Ligand:
    smiles = normalize_smiles(smiles)
    mol = Chem.MolFromSmiles(smiles)
    charge = Chem.GetFormalCharge(mol) if mol is not None else 0
    return Ligand(smiles=smiles, formal_charge=charge)


def _find_col(columns, *candidates) -> str | None:
    lower = {c.lower(): c for c in columns}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    return None


# All element symbols, for cheaply telling a metal ('Au') from a complex name
# ('CN2_Au_PMe3') in the headerless positional form (avoids the noisy RDKit
# exception GetAtomicNumber throws on non-elements).
_ELEMENT_SYMBOLS = frozenset(_PERIODIC.GetElementSymbol(z) for z in range(1, 119))


def is_f_block(symbol: str) -> bool:
    """True if ``symbol`` is a lanthanide (La-Lu) or actinide (Ac-Lr).

    xtb's GFN methods do not reliably parametrise the f-block, so relaxation is
    skipped for these metals (the assembled geometry is returned instead).
    """
    try:
        z = _PERIODIC.GetAtomicNumber(str(symbol).strip())
    except (RuntimeError, ValueError):
        return False
    return 57 <= z <= 71 or 89 <= z <= 103


def _has_leading_name(cells: list[str]) -> bool:
    """Does a headerless line start with a complex name (``name, metal, OS, ...``)?

    Yes when the second cell is an element symbol, unless the first cell is one too
    and the third cell is filled in but not a whole number. That exception keeps
    ``Pt, N, N, N`` (OS forgotten, ammonia first) reading as metal Pt, while
    ``B, Pt, 2, ...`` and ``B, Pt, , ...`` still read as a complex named "B".
    Decided per line, so named and unnamed lines can be mixed.
    """
    if len(cells) < 2 or _as_symbol(cells[1]) is None:
        return False
    third = cells[2] if len(cells) > 2 else ""
    if _as_symbol(cells[0]) is not None and third and _whole_number(third) is None:
        return False
    return True


def _split_positional(cells: list[str]) -> tuple[str | None, list[str]]:
    """Split a headerless line into ``(name or None, [metal, OS, SMILES...])``."""
    if _has_leading_name(cells):
        return cells[0] or None, cells[1:]
    return None, cells


def _positional_complex(name: str | None, cells: list[str]) -> Complex:
    """Build a Complex from ``[metal, OS, SMILES...]`` cells (name may be None)."""
    metal = Metal(_resolve_symbol(cells[0] if cells else None),
                  _oxidation_state(cells[1] if len(cells) > 1 else None))
    ligands = [_make_ligand(s) for s in cells[2:] if s and not is_counterion(s)]
    if not ligands:
        raise InputError("No coordinating ligand SMILES found.")
    return Complex(metal=metal, ligands=ligands, name=name)


@dataclass(frozen=True)
class RowParseError:
    """A single CSV row that could not be parsed into a Complex.

    Returned (instead of raised) in ``parse_dataframe(..., lenient=True)`` so one
    bad row does not abort a whole batch — the web layer renders it as a flagged,
    unbuildable table row alongside the good complexes.
    """

    position: int          # 0-based row position in the data (users see position + 1)
    name: str | None
    metal: str | None
    message: str


def _cell_str(row, col) -> str | None:
    if col is None:
        return None
    val = row[col]
    if pd.isna(val):
        return None
    text = str(val).strip()
    return text or None


def _row_to_complex(row, *, metal_col, ox_col, name_col, index_col, isomer_col,
                    ligand_cols) -> Complex:
    """Build one Complex from a DataFrame row (raises InputError on bad input)."""
    metal = Metal(_resolve_symbol(row[metal_col]), _oxidation_state(row[ox_col]))
    ligands = [
        _make_ligand(str(row[c]).strip())
        for c in ligand_cols
        if pd.notna(row[c]) and str(row[c]).strip()
        and not is_counterion(str(row[c]).strip())
    ]
    if not ligands:
        raise InputError("No coordinating ligand SMILES found.")
    name = str(row[name_col]) if name_col and pd.notna(row[name_col]) else None
    index = None
    if index_col and pd.notna(row[index_col]):
        try:
            index = int(row[index_col])
        except (ValueError, TypeError):
            index = None
    isomer_spec = None
    if isomer_col and pd.notna(row[isomer_col]) and str(row[isomer_col]).strip():
        isomer_spec = str(row[isomer_col]).strip()
    return Complex(metal=metal, ligands=ligands, name=name, index=index,
                   isomer_spec=isomer_spec)


def parse_dataframe(df: pd.DataFrame, *, lenient: bool = False):
    """Normalise a complexes DataFrame (either shape) into Complex objects.

    With ``lenient=True`` a row that fails to parse becomes a :class:`RowParseError`
    entry (in input order) instead of aborting the whole batch; the return list is
    then a mix of ``Complex`` and ``RowParseError``. The default (strict) mode
    keeps the original behaviour: it raises on the first bad row.
    """
    cols = list(df.columns)
    metal_col = _find_col(cols, "metal")
    ox_col = _find_col(cols, "oxidation_state", "charge", "oxidation")
    name_col = _find_col(cols, "name")
    index_col = _find_col(cols, "index", "complex_id")
    isomer_col = _find_col(cols, "isomer", "isomer_spec", "isomer_notation")
    slot_cols = [c for c in cols if _L_SLOT.match(str(c))]

    headerless = metal_col is None
    if headerless:
        # Positional: [name,] metal, oxidation_state, SMILES... The optional leading
        # name is detected per line (_has_leading_name), so one typo'd first line
        # can't shift every row and named/unnamed lines can be mixed.
        ligand_cols = []
    elif slot_cols:
        ligand_cols = sorted(slot_cols, key=lambda c: int(re.search(r"\d+", c).group()))
    else:
        # Positional: every column after metal & oxidation_state is a ligand.
        skip = {metal_col, ox_col, name_col, index_col, isomer_col} - {None}
        ligand_cols = [c for c in cols if c not in skip]

    complexes: list[Complex] = []
    ordered: list = []  # complexes and (lenient only) RowParseErrors, in input order
    for i, (_, row) in enumerate(df.iterrows()):
        if headerless:
            cells = ["" if pd.isna(v) else str(v).strip() for v in row.tolist()]
            row_name, rest = _split_positional(cells)
            row_metal = rest[0] if rest and rest[0] else None
        else:
            row_name, row_metal = _cell_str(row, name_col), _cell_str(row, metal_col)
        try:
            if headerless:
                cx = _positional_complex(row_name, rest)
            else:
                cx = _row_to_complex(
                    row, metal_col=metal_col, ox_col=ox_col, name_col=name_col,
                    index_col=index_col, isomer_col=isomer_col, ligand_cols=ligand_cols,
                )
        except InputError as exc:
            if not lenient:
                # Rows are numbered from 1, matching the web table's "row N" labels.
                raise InputError(f"Row {i + 1}: {exc}") from exc
            ordered.append(RowParseError(
                position=i, name=row_name, metal=row_metal, message=str(exc),
            ))
            continue
        complexes.append(cx)
        ordered.append(cx)
    _assign_unique_names(complexes)
    return ordered if lenient else complexes


def parse_csv(path: str | Path) -> list[Complex]:
    """Parse a complexes CSV into a list of Complex objects.

    The header line is optional: the first row is only taken as column names when it
    looks like one (:func:`is_header_row`). A headerless file used to lose its first
    complex to ``pd.read_csv``'s default ``header=0``. Rows may have different lengths
    (complexes with different ligand counts); short rows are padded.
    """
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = [[c.strip() for c in r] for r in csv.reader(fh) if any(c.strip() for c in r)]
    if not rows:
        raise InputError("The CSV file has no rows.")
    width = max(len(r) for r in rows)
    if is_header_row(rows[0]):
        header, data = list(rows[0]), rows[1:]
        used = [int(re.search(r"\d+", c).group()) for c in header if _L_SLOT.match(c)]
        next_l = (max(used) + 1) if used else 1
        while len(header) < width:          # extra ligand columns past a short header
            header.append(f"L{next_l}")
            next_l += 1
    else:
        header, data = [f"col{i}" for i in range(width)], rows
    data = [r + [""] * (width - len(r)) for r in data]
    return parse_dataframe(pd.DataFrame(data, columns=header))


def parse_row(cells: list[str]) -> Complex:
    """Parse one positional row: ``[name,] metal, oxidation_state, SMILES_1, ...``.

    A leading name is optional and auto-detected per line (see _has_leading_name).
    """
    cells = [str(x).strip() for x in cells]
    name, cells = _split_positional(cells)
    cx = _positional_complex(name, cells)
    _assign_unique_names([cx])  # keep a provided name; auto-name otherwise
    return cx
