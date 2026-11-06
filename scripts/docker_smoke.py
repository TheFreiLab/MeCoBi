"""Fail CI unless the served application returns a real xTB-optimized structure."""

import json
import math
import os
import urllib.request


def main():
    base = os.environ.get("MECOBI_TEST_URL", "http://127.0.0.1:8000")
    spec = {
        "name": "cisplatin", "metal": "Pt", "oxidation_state": 2,
        "ligands": [{"smiles": s} for s in ("N", "N", "[Cl-]", "[Cl-]")],
        "geometry": "square_planar", "relax": True, "xtb_timeout_s": 300,
    }
    request = urllib.request.Request(
        base + "/api/build", data=json.dumps(spec).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=600) as response:
        result = json.load(response)
    assert result["results"], result
    structure = result["results"][0]
    energy = structure.get("total_energy")
    assert energy is not None and math.isfinite(energy), structure
    # Recovery diagnostics are not necessarily failures. Preserve them in CI logs;
    # finite GFN2 energy proves relaxation, while the chemistry suite checks topology.
    warnings = structure.get("warnings", [])
    with urllib.request.urlopen(base + "/api/file/" + structure["token"], timeout=10) as response:
        xyz = response.read().decode().splitlines()
    assert int(xyz[0]) == 11, xyz  # Pt + 2 N + 6 H + 2 Cl
    assert len(xyz[2:]) >= 11, xyz
    print("Optimized cisplatin downloaded; finite xTB energy:", energy)
    for warning in warnings:
        print("Build diagnostic:", warning)

    # Every reverse representation must be served: the optional reverse-tm packages are
    # easy to drop from the image without anything else failing (it happened once).
    expected = {"complex_smiles": "Pt", "trex": "Pt{+2}", "msmiles": "[Pt+2]|"}
    for key, marker in expected.items():
        request = urllib.request.Request(
            base + "/api/reverse/represent",
            data=json.dumps({"xyz": "\n".join(xyz) + "\n", "key": key,
                             "overall_charge": 0}).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=60) as response:
            value = json.load(response)["value"]
        assert marker in value, (key, value)
        print(f"Reverse {key}: {value}")

    # Static-bundle checks that ONLY fail in the built/installed image (a non-editable
    # install serves from site-packages, copying just what package-data globs list) —
    # so they belong here, not in pytest against a source checkout:
    #  - the self-hosted 3Dmol viewer must actually be shipped (else no 3D renders);
    #  - depict_svg thumbnails must be CSP-safe (no inline styles a proxy CSP strips).
    with urllib.request.urlopen(base + "/vendor/3Dmol-min.js", timeout=10) as response:
        assert response.status == 200, response.status
        assert len(response.read()) > 100_000  # the real ~525 KB viewer, not a 404 page
    with urllib.request.urlopen(base + "/api/depict_svg?smiles=CCO", timeout=10) as response:
        svg = json.load(response)["svg"]
    assert svg.startswith("<svg") and "style=" not in svg, svg[:200]
    print("Static bundle OK: 3Dmol viewer served; depict_svg CSP-safe.")


if __name__ == "__main__":
    main()
