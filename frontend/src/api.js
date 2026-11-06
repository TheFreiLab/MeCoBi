// Thin fetch layer over the FastAPI backend. Same endpoints the vanilla page used.

async function post(url, body) {
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.detail || `${r.status} ${r.statusText}`);
  return data;
}

export const api = {
  parse: (csv) => post("/api/parse", { csv }),
  build: (req, options) => post("/api/build", options ? { ...req, options } : req),
  reverse: (xyz, opts = {}) => post("/api/reverse", { xyz, ...opts }),
  reverseBackends: () => fetch("/api/reverse/backends").then((r) => r.json()),
  represent: (xyz, key, overall_charge) =>
    post("/api/reverse/represent", { xyz, key, overall_charge }),
  reverseExport: (items, columns) => post("/api/reverse/export", { items, columns }),
  isomers: (req) => post("/api/isomers", req),
  perceive: (req) => post("/api/perceive", req),
  submitJob: (complexes, relax, xtbTimeout, options) =>
    post("/api/jobs", { complexes, relax, xtb_timeout_s: xtbTimeout, options }),
  getJob: async (id) => {
    const r = await fetch(`/api/jobs/${id}`);
    return r.json();
  },
  cancelJob: (id) => post(`/api/jobs/${id}/cancel`, {}),
  geometries: () => fetch("/api/geometries").then((r) => r.json()),
  version: () => fetch("/api/version").then((r) => r.json()),
  depict: (smiles) =>
    fetch(`/api/depict?smiles=${encodeURIComponent(smiles)}`).then((r) => r.json()),
  depictSvg: (smiles) =>
    fetch(`/api/depict_svg?smiles=${encodeURIComponent(smiles)}`).then((r) => r.json()),
  vertices: (geometry, denticities) =>
    fetch(`/api/vertices?geometry=${encodeURIComponent(geometry)}&denticities=${denticities.join(",")}`).then(
      (r) => r.json()
    ),
  sites: (geometry, denticities, arene = [], cap = []) =>
    fetch(
      `/api/sites?geometry=${encodeURIComponent(geometry)}&denticities=${denticities.join(",")}` +
        (arene.length ? `&arene=${arene.join(",")}` : "") +
        (cap.length ? `&cap=${cap.join(",")}` : "")
    ).then((r) => r.json()),
  fileUrl: (token) => `/api/file/${token}`,
  // Same result, a different format: swap the token's extension (foo.xyz -> foo.mol/foo.pdb).
  fileUrlAs: (token, ext) => `/api/file/${token.replace(/\.[^./]+$/, "." + ext)}`,
  fileText: (token) => fetch(`/api/file/${token}`).then((r) => r.text()),
  downloadAllUrl: (jobId) => `/api/download/${jobId}`,
};
