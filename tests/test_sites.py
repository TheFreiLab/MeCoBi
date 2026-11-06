"""Coordination-site model: assignment validation + dynamic topology build."""

import numpy as np
import pytest

from mecobi.assembly import sites
from mecobi.assembly.sites import SiteAssignmentError
from mecobi.model import Geometry

O, SP, L = Geometry.OCTAHEDRAL, Geometry.SQUARE_PLANAR, Geometry.LINEAR
TET = Geometry.TETRAHEDRAL
SAP, DD = Geometry.SQUARE_ANTIPRISM, Geometry.DODECAHEDRAL


@pytest.mark.parametrize("geom", [SAP, DD])
def test_cn8_has_a_site_model(geom):
    # CN8 (square-antiprism, dodecahedral) has no fixed topology class; both must
    # be buildable via the site model from their SITE_VECTORS.
    assert geom in sites.SITE_VECTORS
    assert len(sites.site_positions(geom)) == 8
    # four bidentate ligands fill all eight sites.
    asg = sites.default_assignment(geom, [2, 2, 2, 2])
    assert sorted(s for ss in asg.values() for s in ss) == list(range(8))
    cls = sites.topology_from_sites(geom, [2, 2, 2, 2], asg)
    assert len(cls._edge_prototypes) == 8


def test_tetrahedral_has_a_site_model():
    # tetrahedral is offered for CN4 but has no fixed topology class; it must be
    # buildable via the site model (regression: selecting it used to KeyError).
    assert TET in sites.SITE_VECTORS
    pos = sites.site_positions(TET)
    assert len(pos) == 4
    asg = sites.default_assignment(TET, [1, 1, 1, 1])
    assert sorted(s for ss in asg.values() for s in ss) == [0, 1, 2, 3]
    # every tetrahedral pair is ~109.47 deg -> all pairs count as adjacent (cis).
    assert len(sites.cis_pairs(TET)) == 6
    cls = sites.topology_from_sites(TET, [1, 1, 1, 1], asg)
    assert len(cls._edge_prototypes) == 4


# --------------------------------------------------------------------------- #
# fast: site geometry + validation
# --------------------------------------------------------------------------- #

def test_site_positions_and_cis_pairs():
    assert len(sites.site_positions(O)) == 6
    # trans pairs (0,1),(2,3),(4,5) are NOT cis; 90-degree pairs are.
    cis = set(sites.cis_pairs(O))
    assert (0, 1) not in cis and (2, 3) not in cis and (4, 5) not in cis
    assert (0, 2) in cis


def test_default_assignment_fills_all_sites_cis():
    asg = sites.default_assignment(O, [2, 2, 1, 1])
    used = [s for ss in asg.values() for s in ss]
    assert sorted(used) == [0, 1, 2, 3, 4, 5]
    cis = set(sites.cis_pairs(O))
    for lig, ss in asg.items():
        if len(ss) == 2:
            assert tuple(sorted(ss)) in cis  # bidentates land on a cis pair


def test_default_assignment_tris_bidentate_backtracks():
    # Greedy pair-picking dead-ends here ((0,2),(1,3) strands trans 4/5).
    asg = sites.default_assignment(O, [2, 2, 2])
    used = sorted(s for ss in asg.values() for s in ss)
    assert used == [0, 1, 2, 3, 4, 5]
    cis = set(sites.cis_pairs(O))
    assert all(tuple(sorted(ss)) in cis for ss in asg.values())


def test_arene_default_assignment_is_a_facial_triad():
    cis = {tuple(sorted(p)) for p in sites.cis_pairs(O)}
    plain = sites.default_assignment(O, [3, 2, 1])
    arene = sites.default_assignment(O, [3, 2, 1], arene_ligands={0})

    def facial(triple):
        return all(tuple(sorted((a, b))) in cis for i, a in enumerate(triple) for b in triple[i + 1:])

    assert not facial(plain[0])          # generic tridentate default may be meridional
    assert facial(arene[0])              # an eta-arene cap must be facial


def test_nonarene_tridentate_default_is_meridional_not_piano_stool():
    # A non-arene tridentate (ONO Schiff base) shares the octahedral (3,2,1)
    # partition with the arene piano-stool cap. It must bind MERIDIONALLY, not
    # fold onto the cap's facial triad: default_isomer routes it to the site model
    # with the central backbone donor on the site cis to both ends.
    from mecobi import assembly, perception
    from mecobi.inputs import parse_row

    cx = parse_row([
        "V", "5",
        "[O-]C1=CC=CC=C1/C=N/N=C([O-])/C2=CC=CC=C2",  # ONO azine tridentate
        "O=C(N[O-])C1=CC=CC=C1",                        # O,O bidentate
        "[O-2]",                                        # oxo
    ])
    perception.perceive_complex(cx)
    spec = assembly.default_isomer(cx, O)
    assert spec.site_based                              # NOT the facial piano-stool
    tri = spec.assignment[0]
    assert len(tri) == 3
    adj = sites._adjacency(O)
    centre, ends = tri[1], (tri[0], tri[2])             # centre donor is coord idx 1
    assert all(e in adj[centre] for e in ends)          # centre cis to both ends
    assert ends[1] not in adj[ends[0]]                  # the two ends are trans


def test_default_assignment_rejects_overfilled_geometry():
    with pytest.raises(SiteAssignmentError):
        sites.default_assignment(SP, [2, 2, 1])  # 5 donors, 4 sites


def test_validate_rejects_trans_bidentate_and_double_booking():
    with pytest.raises(SiteAssignmentError):
        sites.validate_assignment(O, [2], {0: (0, 1)})  # trans
    with pytest.raises(SiteAssignmentError):
        sites.validate_assignment(SP, [1, 1, 1, 1], {0: (0,), 1: (0,), 2: (1,), 3: (2,)})  # site 0 twice


def test_topology_from_sites_builds_class():
    cls = sites.topology_from_sites(O, [2, 2, 1, 1], {0: (0, 2), 1: (3, 5), 2: (1,), 3: (4,)})
    assert len(cls._ligand_vertex_prototypes) == 4
    assert len(cls._edge_prototypes) == 6


# --------------------------------------------------------------------------- #
# slow: construct + relax, cis vs trans differ
# --------------------------------------------------------------------------- #

@pytest.mark.slow
def test_polyatomic_monodentate_points_outward(tmp_path):
    # A polyatomic monodentate (pyridine) built via the site model must be oriented
    # with its body radially outward; before the fix it kept RDKit's arbitrary
    # orientation and folded onto the metal (~8-10 body atoms closer than the donor).
    from mecobi import pipeline
    from mecobi.model import Complex, Ligand, Metal

    py = "c1ccccn1"  # pyridine; N donor is atom index 5 (donor_override avoids torch)
    cx = Complex(
        metal=Metal("Ru", 2), geometry=O,
        ligands=[Ligand(py, donor_override=[5])]
        + [Ligand("[Cl-]") for _ in range(4)]
        + [Ligand(py, donor_override=[5])],
    )
    res = pipeline.build_complex(cx, tmp_path, all_isomers=True, relax=False)  # site model
    r = res[0]
    from pathlib import Path

    txt = Path(r.xyz_path).read_text().splitlines()
    ncount = int(txt[0])
    syms, X = [], []
    for ln in txt[2:2 + ncount]:
        q = ln.split(); syms.append(q[0]); X.append([float(x) for x in q[1:4]])
    X = np.array(X); metal = X[r.metal_index]
    for di in r.donor_indices:
        if syms[di] == "Cl":
            continue
        d_donor = np.linalg.norm(X[di] - metal)
        assert d_donor < 2.6  # a real M-N bond, not a folded ligand pushing it out
        folded = sum(
            1 for i in range(ncount)
            if syms[i] not in ("H", "Cl", "Ru") and i != di
            and np.linalg.norm(X[i] - metal) < d_donor
        )
        assert folded <= 1  # body points outward (was 8-10 before the fix)


@pytest.mark.slow
def test_cis_vs_trans_dichlorido(tmp_path):
    from mecobi import pipeline
    from mecobi.model import Complex, Ligand, Metal

    def cl_angle(site_assignment):
        cx = Complex(
            metal=Metal("Ir", 3), geometry=O,
            ligands=[Ligand("c1ccc(-c2ccccn2)nc1"), Ligand("c1ccc(-c2ccccn2)nc1"),
                     Ligand("[Cl-]"), Ligand("[Cl-]")],
        )
        res = pipeline.build_complex(cx, tmp_path, site_assignment=site_assignment, relax=True)
        from pathlib import Path

        lines = Path(res[0].xyz_path).read_text().splitlines()
        n = int(lines[0])
        syms, X = [], []
        for ln in lines[2:2 + n]:
            q = ln.split(); syms.append(q[0]); X.append([float(x) for x in q[1:4]])
        X = np.array(X); mi = syms.index("Ir")
        d = np.linalg.norm(X - X[mi], axis=1)
        cl = [i for i in np.argsort(d) if syms[i] == "Cl"][:2]
        va, vb = X[cl[0]] - X[mi], X[cl[1]] - X[mi]
        return np.degrees(np.arccos(np.clip(va @ vb / (np.linalg.norm(va) * np.linalg.norm(vb)), -1, 1)))

    cis = cl_angle({0: (0, 2), 1: (3, 5), 2: (1,), 3: (4,)})
    trans = cl_angle({0: (0, 2), 1: (1, 3), 2: (4,), 3: (5,)})
    assert cis < 110  # ~90
    assert trans > 150  # ~180


def test_bis_tridentate_routes_to_site_model():
    """Bis-terpy routes through the meridional site model, not the fixed octa_2tri
    that overlapped the two planar tridentates (issue #38)."""
    from mecobi import perception
    from mecobi.assembly import default_isomer
    from mecobi.model import Complex, Ligand, Metal

    terpy = "C1(C2=CC=CC=N2)=NC(C3=NC=CC=C3)=CC=C1"
    cx = Complex(metal=Metal("Fe", 2), ligands=[Ligand(terpy), Ligand(terpy)])
    perception.perceive_complex(cx)
    spec = default_isomer(cx, Geometry.OCTAHEDRAL)
    assert spec.site_based                                  # not the fixed octa_2tri
    # each terpy spans a meridian (a trans pair), on perpendicular planes
    for lig in (0, 1):
        pos = [sites.site_positions(Geometry.OCTAHEDRAL)[s] for s in spec.assignment[lig]]
        assert sites._is_meridional_triple(pos)


@pytest.mark.slow
def test_bis_naphthyl_terpy_no_interpenetration():
    """The bulky naphthyl-terpy case from issue #38: the fixed topology fused the two
    ligands into one clashed blob; the site model keeps them separate."""
    import tempfile

    from mecobi import perception, pipeline
    from mecobi.model import Complex, Ligand, Metal

    L2 = "C1(C2=CC=C(C=CC=C3)C3=C2)=CC(C4=CC=CC=N4)=NC(C5=NC=CC=C5)=C1"
    cx = Complex(metal=Metal("Cr", 3), ligands=[Ligand(L2), Ligand(L2)])
    perception.perceive_complex(cx)
    with tempfile.TemporaryDirectory() as d:
        r = pipeline.build_complex(cx, d, relax=False)[0]   # raw placement is enough
        lines = open(r.xyz_path).read().splitlines()
    n = int(lines[0])
    syms = [ln.split()[0] for ln in lines[2:2 + n]]
    P = np.array([[float(x) for x in ln.split()[1:4]] for ln in lines[2:2 + n]])
    # two ligand bodies must stay separate — no fused connected component
    idx = [i for i in range(n) if syms[i] != "Cr"]
    adj = {i: [] for i in idx}
    for a, i in enumerate(idx):
        for j in idx[a + 1:]:
            if np.linalg.norm(P[i] - P[j]) < 1.75:
                adj[i].append(j); adj[j].append(i)
    seen, comps = set(), []
    for i in idx:
        if i in seen:
            continue
        stack, c = [i], []
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x); c.append(x); stack += [y for y in adj[x] if y not in seen]
        comps.append(c)
    big = [c for c in comps if len(c) > 5]
    assert len(big) == 2                                    # two distinct ligands, not fused
    inter = min(np.linalg.norm(P[a] - P[b]) for a in big[0] for b in big[1])
    assert inter > 2.2                                      # no interpenetration
