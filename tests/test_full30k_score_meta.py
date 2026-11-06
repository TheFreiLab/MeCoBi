"""full30k_score.run_setting: a run merged by merge_rerun.py keeps its sources' metadata nested.

The scorer picks the crystal references by the hydride file the run was built with. Reading only
the top level of run_meta.json, a merged run looked like a run without hydride corrections, and
its ~1,400 hydride complexes were scored against hydride-less references without any warning.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments" / "benchmark" / "full30k"))
from full30k_score import run_setting

H = "benchmark_hydrides.json"


def test_plain_run_reads_the_top_level():
    assert run_setting({"hydrides": H, "commit": "abc"}, "hydrides") == H
    assert run_setting({"hydrides": None}, "hydrides") is None
    assert run_setting({}, "hydrides") is None


def test_merged_run_reads_its_sources():
    meta = {"merged_from": {"base": "a", "rerun": "b"},
            "base_meta": {"hydrides": H, "commit": "409b273"},
            "rerun_meta": {"hydrides": H, "commit": "69c8760"}}
    assert run_setting(meta, "hydrides") == H
    assert run_setting(meta, "missing") is None


def test_merged_run_with_disagreeing_sources_is_refused():
    meta = {"base_meta": {"hydrides": H}, "rerun_meta": {"hydrides": None}}
    with pytest.raises(SystemExit):
        run_setting(meta, "hydrides")
