// Stage the 3Dmol viewer into public/ so the page loads it from our own origin.
//
// index.html used to pull https://3Dmol.org/build/3Dmol-min.js at runtime: an
// unversioned third-party script, with no integrity attribute, that every visitor's
// browser executed and that took the 3D viewer down with it whenever that host was
// unreachable. The dependency is now pinned in package.json (exact version, with a
// lockfile integrity hash) and copied here at build time, so the served bundle is
// self-contained and what ships is exactly what npm audited.
//
// The copy is generated, not committed: it lives in the gitignored public/vendor/
// and is reproduced by `npm run build` (and `npm run dev`) from node_modules. The
// built OUTPUT under src/mecobi/web/static/vendor/ is committed, like the rest of
// the bundle.
import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const from = join(here, "..", "node_modules", "3dmol", "build");
const to = join(here, "..", "public", "vendor");

mkdirSync(to, { recursive: true });
// The .LICENSE.txt rides along: 3Dmol is BSD-3-Clause and the attribution has to
// ship with the code we serve.
for (const file of ["3Dmol-min.js", "3Dmol-min.js.LICENSE.txt"]) {
  copyFileSync(join(from, file), join(to, file));
}
console.log(`vendored 3Dmol into ${to}`);
