// Curated common ligands for the library reel (LigandLibrary.jsx). Seeded from the
// repo's Common_Names_Ligands.csv plus a few staples (CO, Cp, terpy, MeCN, DMSO,
// SCN, NO2). SMILES use the normalised forms MeCoBi expects (see inputs.py
// _SMILES_NORMALIZATIONS: CO as [C-]#[O+], nitrite as O=N[O-]). `label` is the short
// chip shown in the box; `name` is the full name (tooltip). Keep the count EVEN so
// the two-column reel duplicates onto a clean row boundary and loops seamlessly.
export const LIGAND_LIBRARY = [
  { label: "NH₃", name: "Ammonia", smiles: "N" },
  { label: "H₂O", name: "Water", smiles: "O" },
  { label: "CO", name: "Carbon monoxide", smiles: "[C-]#[O+]" },
  { label: "Cl⁻", name: "Chloride", smiles: "[Cl-]" },
  { label: "Br⁻", name: "Bromide", smiles: "[Br-]" },
  { label: "I⁻", name: "Iodide", smiles: "[I-]" },
  { label: "CN⁻", name: "Cyanide", smiles: "[C-]#N" },
  { label: "OH⁻", name: "Hydroxide", smiles: "[OH-]" },
  { label: "py", name: "Pyridine", smiles: "c1ccncc1" },
  { label: "bipy", name: "2,2′-Bipyridine", smiles: "c1ccc(-c2ccccn2)nc1" },
  { label: "phen", name: "1,10-Phenanthroline", smiles: "C1(C(N=CC=C2)=C2C=C3)=C3C=CC=N1" },
  { label: "terpy", name: "2,2′:6′,2″-Terpyridine", smiles: "c1ccnc(-c2cccc(-c3ccccn3)n2)c1" },
  { label: "en", name: "Ethylenediamine", smiles: "NCCN" },
  { label: "PPh₃", name: "Triphenylphosphine", smiles: "P(c1ccccc1)(c1ccccc1)c1ccccc1" },
  { label: "acac", name: "Acetylacetonate", smiles: "CC(CC(C)[O-])[O-]" },
  { label: "OAc⁻", name: "Acetate", smiles: "CC(=O)[O-]" },
  { label: "ox²⁻", name: "Oxalate", smiles: "C(=O)(C(=O)[O-])[O-]" },
  { label: "Cp⁻", name: "Cyclopentadienyl", smiles: "[cH-]1cccc1" },
  { label: "MeCN", name: "Acetonitrile", smiles: "CC#N" },
  { label: "DMSO", name: "Dimethyl sulfoxide", smiles: "CS(=O)C" },
  { label: "SCN⁻", name: "Thiocyanate", smiles: "[S-]C#N" },
  { label: "NO₂⁻", name: "Nitrite", smiles: "O=N[O-]" },
];
