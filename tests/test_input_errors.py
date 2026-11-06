"""User-facing input error messages and per-line name detection (UI audit H3).

Every message must name the fix, blame the right field, and number rows the way
the web table does (from 1). All fast: nothing here loads pydentate.
"""

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from mecobi import inputs, perception
from mecobi.geometry import DenticityMismatchError, geometries_for_cn
from mecobi.inputs import InputError
from mecobi.model import Complex, Ligand, Metal
from mecobi.web import app
from mecobi.web.app import JOB_NOT_FOUND, _describe

client = TestClient(app)


def _headerless(*lines):
    """A headerless positional DataFrame, padded like the web's _read_csv does."""
    rows = [[c.strip() for c in line.split(",")] for line in lines]
    width = max(len(r) for r in rows)
    return pd.DataFrame([r + [""] * (width - len(r)) for r in rows],
                        columns=[f"col{i}" for i in range(width)])


# --------------------------------------------------------------------------- #
# Messages
# --------------------------------------------------------------------------- #

def test_missing_oxidation_state_names_the_fix():
    with pytest.raises(InputError) as exc:
        inputs.parse_row(["Ir", "", "c1ccncc1"])
    msg = str(exc.value)
    assert msg.startswith("Oxidation state missing. Put it after the metal")
    assert "VISION" not in msg


def test_invalid_oxidation_state_names_the_fix():
    with pytest.raises(InputError, match=r"Oxidation state 'two' isn't a whole number"):
        inputs.parse_row(["Pt", "two", "N"])


def test_fractional_oxidation_state_is_not_truncated():
    # 2.5 used to be silently truncated to 2 (a wrong d-count -> wrong geometry).
    with pytest.raises(InputError, match="isn't a whole number"):
        inputs.parse_row(["Pt", "2.5", "N"])
    assert inputs.parse_row(["Pt", "+2", "N"]).metal.oxidation_state == 2
    assert inputs.parse_row(["Pt", "2.0", "N"]).metal.oxidation_state == 2


def test_unknown_metal_names_the_fix():
    with pytest.raises(InputError, match=r"'Xx' is not an element symbol\. Start the line"):
        inputs._resolve_symbol("Xx")


def test_atomic_number_metal_is_rejected():
    for value in ("78", 78, 78.0):
        with pytest.raises(InputError, match=r"is not an element symbol\. Use the symbol"):
            inputs._resolve_symbol(value)
    with pytest.raises(InputError, match="Use the symbol"):
        inputs.parse_row(["78", "2", "N", "N"])


def test_unreadable_smiles_message():
    cx = Complex(metal=Metal("Pt", 2), ligands=[Ligand(smiles="C1CC")], name="bad")
    with pytest.raises(perception.SmilesParseError, match=r"^Can't read SMILES 'C1CC'\.$"):
        perception.perceive_complex(cx)
    # The web table shows it without the "perception failed:" prefix ...
    out = _describe(Complex(metal=Metal("Pt", 2), ligands=[Ligand(smiles="C1CC")], name="b"))
    assert out.supported is False and out.error == "Can't read SMILES 'C1CC'."
    # ... and it is still a PerceptionError for existing callers.
    assert issubclass(perception.SmilesParseError, perception.PerceptionError)


def test_unsupported_cn_message():
    with pytest.raises(DenticityMismatchError) as exc:
        geometries_for_cn(10)
    assert str(exc.value) == "No supported geometry for coordination number 10 (supported: 2 to 9)."


def test_expired_job_message():
    with TestClient(app) as c:  # run lifespan, so the job store exists
        r = c.get("/api/jobs/0123456789abcdef")
    assert r.status_code == 404
    assert r.json()["detail"] == JOB_NOT_FOUND
    assert "24 hours" in JOB_NOT_FOUND and "Build the complexes again" in JOB_NOT_FOUND


# --------------------------------------------------------------------------- #
# Row numbering (from 1, matching the web table's "row N")
# --------------------------------------------------------------------------- #

def test_strict_errors_number_rows_from_one():
    df = pd.DataFrame({"Metal": ["Pt", "Pt"], "Charge": [2, None],
                       "L1": ["N", "N"], "L2": ["N", "N"]})
    with pytest.raises(InputError, match=r"^Row 2: Oxidation state missing"):
        inputs.parse_dataframe(df)


def test_strict_no_ligand_error_numbers_from_one():
    df = pd.DataFrame({"Metal": ["Pt"], "Charge": [2], "L1": [""], "L2": [""]})
    with pytest.raises(InputError, match=r"^Row 1: No coordinating ligand SMILES found\.$"):
        inputs.parse_dataframe(df)


def test_strict_row_number_ignores_dataframe_index_labels():
    # Numbering is positional, not the DataFrame's index labels.
    df = pd.DataFrame({"Metal": ["Pt", "Xx"], "Charge": [2, 2], "L1": ["N", "N"]},
                      index=[10, 20])
    with pytest.raises(InputError, match=r"^Row 2: 'Xx'"):
        inputs.parse_dataframe(df)


def test_lenient_message_has_no_row_prefix_and_table_label_is_one_based():
    # The web table already shows the row, so the message itself carries no prefix.
    items = inputs.parse_dataframe(_headerless("Pt, 2, N, N", "Pt, , N, N"), lenient=True)
    err = items[1]
    assert isinstance(err, inputs.RowParseError) and err.position == 1
    assert err.message.startswith("Oxidation state missing")
    r = client.post("/api/parse", json={"csv": "Pt, , [Cl-], [Cl-]"})
    assert r.status_code == 200
    row = r.json()[0]
    assert row["name"] == "row 1" and not row["error"].startswith("Row")


# --------------------------------------------------------------------------- #
# Failed rows: no made-up oxidation state
# --------------------------------------------------------------------------- #

def test_failed_row_oxidation_state_is_none_not_zero():
    r = client.post("/api/parse", json={"csv": "pt, , [Cl-], [Cl-]\nXx, 2, [Cl-], [Cl-]"})
    assert r.status_code == 200
    a, b = r.json()
    assert a["supported"] is False and a["oxidation_state"] is None
    assert a["metal"] == "Pt"                       # canonical symbol, so the table shows Pt(?)
    assert b["metal"] == "Xx" and b["oxidation_state"] is None


# --------------------------------------------------------------------------- #
# Per-line name detection (headerless input)
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("cells, name, metal", [
    (["Pt", "2", "N", "N"], None, "Pt"),                 # canonical, no name
    (["cisplatin", "Pt", "2", "N", "N"], "cisplatin", "Pt"),
    (["cisplatin", "pt", "2", "N", "N"], "cisplatin", "Pt"),  # loose casing
    (["B", "Pt", "2", "N", "N"], "B", "Pt"),             # one-letter element as a name
])
def test_leading_name_detection(cells, name, metal):
    cx = inputs.parse_row(cells)
    assert cx.metal.symbol == metal
    if name is None:
        assert cx.name and cx.name != cells[0]           # auto-named
    else:
        assert cx.name == name


@pytest.mark.parametrize("cells, message", [
    (["Xx", "2", "N", "N"], "'Xx' is not an element symbol"),          # was "Invalid OS 'N'"
    (["cisplatin", "Pt", "", "N"], "Oxidation state missing"),
    (["B", "Pt", "", "N"], "Oxidation state missing"),                  # B is the name
    (["Pt", "N", "N", "N"], "Oxidation state 'N' isn't a whole number"),  # OS forgotten
    (["Pt", "", "N", "N"], "Oxidation state missing"),
])
def test_leading_name_detection_blames_the_right_field(cells, message):
    with pytest.raises(InputError, match=message):
        inputs.parse_row(cells)


def test_headerless_name_detection_is_per_line():
    # Mixed named/unnamed lines both parse, and a typo'd first line no longer
    # shifts every other row (detection used to be decided once from line 1).
    items = inputs.parse_dataframe(
        _headerless("Xx, 2, N, N", "Pt, 2, N, N", "cisplatin, Pt, 2, N, N"), lenient=True)
    bad, plain, named = items
    assert isinstance(bad, inputs.RowParseError)
    assert bad.metal == "Xx" and bad.name is None and "not an element symbol" in bad.message
    assert plain.metal.symbol == "Pt" and plain.metal.oxidation_state == 2
    assert named.name == "cisplatin" and named.metal.symbol == "Pt"
    assert len(named.ligands) == 2


def test_headerless_auto_names_unchanged():
    # Auto-naming still runs once over the batch (Pt_01, Pt_02), not per line.
    cxs = inputs.parse_dataframe(_headerless("Pt, 2, N, N", "Pt, 2, [Cl-], [Cl-]"))
    assert [c.name for c in cxs] == ["Pt_01", "Pt_02"]


# --------------------------------------------------------------------------- #
# CLI CSV reader: header line optional (found during the UI audit, H3)
# --------------------------------------------------------------------------- #

def test_parse_csv_headerless_keeps_first_complex(tmp_path):
    # pd.read_csv's default header=0 used to swallow the first line as column names.
    p = tmp_path / "nohdr.csv"
    p.write_text("Pt, 2, N, N\nPd, 2, [Cl-], [Cl-], [Cl-], [Cl-]\n", encoding="utf-8")
    cxs = inputs.parse_csv(p)
    assert [c.metal.symbol for c in cxs] == ["Pt", "Pd"]       # ragged rows padded
    assert len(cxs[1].ligands) == 4


def test_parse_csv_headerless_named_lines(tmp_path):
    p = tmp_path / "named.csv"
    p.write_text("cisplatin, Pt, 2, N, N, [Cl-], [Cl-]\nPd, 2, N, N\n", encoding="utf-8")
    cxs = inputs.parse_csv(p)
    assert cxs[0].name == "cisplatin" and cxs[1].metal.symbol == "Pd"


def test_parse_csv_with_header_and_bom(tmp_path):
    p = tmp_path / "hdr.csv"
    p.write_text("﻿Name,Metal,Charge,L1,L2\nA,Pt,2,N,N,[Cl-],[Cl-]\n", encoding="utf-8")
    (cx,) = inputs.parse_csv(p)
    assert cx.name == "A" and cx.metal.symbol == "Pt"
    assert len(cx.ligands) == 4                                # columns past a short header


def test_is_header_row():
    assert inputs.is_header_row(["Name", "Metal", "Charge", "L1"])
    assert inputs.is_header_row(["metal", "oxidation_state", "l1"])
    assert not inputs.is_header_row(["Pt", "2", "N", "N"])
    assert not inputs.is_header_row(["cisplatin", "Pt", "2", "N"])
