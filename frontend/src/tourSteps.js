// Ordered steps for the guided tour (GuidedTour.jsx). Each step either targets an
// existing element by its data-tour="<target>" attribute, or is centred (no target,
// e.g. the welcome/closing cards). A step whose target isn't in the DOM is skipped,
// so the tour adapts as sections open.
//
// Interactive steps drive a real example: "Load an example" drops cisplatin and
// ferroquine into the input; Parse waits for the table; the donor step opens
// ferroquine's donor panel; the Assign steps open the 3D editor, wait for the four
// ligands to be placed, then save the isomer; finally Build all builds everything.
// `waitLabel` is the call-to-action shown while a step waits on the user. The
// "ligand-library-btn" step only appears once that feature ships.
export const TOUR_STEPS = [
  {
    title: "Welcome to MeCoBi",
    body: "MeCoBi turns the SMILES of a metal complex's ligands into optimised 3D structures. This quick tour walks through the interface with real examples. Reopen it any time from “Tour” at the top-right.",
  },
  {
    target: "input-card",
    title: "1 · Describe your complexes",
    body: "Type or paste one complex per line: the metal, its oxidation state, then each ligand as SMILES, separated by commas.",
  },
  {
    target: "input-card",
    title: "2 · Load an example",
    body: "You can load sample structures to see how MeCoBi works. For the tour I've loaded two into the box: cisplatin and ferroquine.",
    action: "loadSample",
  },
  {
    target: "ligand-library-btn",
    title: "Common ligands",
    body: "Browse a library of frequent ligands (CO, bipy, Cp, chloride…) and click one to drop its SMILES straight into the input box.",
  },
  {
    target: "parse-btn",
    title: "3 · Parse",
    body: "Now click Parse to read them into a table. The tour continues once the table appears.",
    waitFor: "complex-table",
    waitLabel: "Click Parse to continue",
    interactive: true,
  },
  {
    target: "complex-table",
    title: "4 · Review the table",
    body: "Each row is one complex: here cisplatin and ferroquine, with its metal, coordination number, geometry, and ligands.",
  },
  {
    target: "ferroquine-donors",
    title: "5 · Donor atoms",
    body: "MeCoBi works out which atoms coordinate. Untick ferroquine's Donors box to see what it found.",
    waitFor: "donor-panel",
    waitLabel: "Untick ferroquine's Donors box",
    interactive: true,
  },
  {
    target: "donor-panel",
    // Top-aligned regardless of size: its ✓ / ✕ sit in the header, and the panel grows
    // after the scroll as the depictions load, so a measured "short" panel would be centred.
    scrollBlock: "start",
    title: "It recognised the Cp rings",
    body: "MeCoBi has marked all five carbons of each cyclopentadienyl (Cp) ring as coordinating: it read both rings as η5 caps. Click ✓ to keep the selection or ✕ to discard it.",
    waitGone: "donor-panel",
    waitLabel: "Save (✓) or Cancel (✕) to continue",
    interactive: true,
  },
  {
    target: "build-controls",
    title: "6 · Relaxation settings",
    body: "Toggle xtb (GFN2) geometry relaxation, choose the spin state, and cap the time per structure. “Advanced options” exposes the pre-xtb geometry guards.",
  },
  {
    target: "assign-btn",
    title: "7 · Set up one exact isomer",
    body: "Cisplatin's two chlorides are cis. Let's set up the trans isomer, transplatin, by hand. Click Isomer editor on cisplatin's row to open it.",
    waitFor: "assign-scene",
    waitLabel: "Click Isomer editor to continue",
    interactive: true,
  },
  {
    target: "assign-disconnect",
    title: "Start from a clean slate",
    body: "The scene opens with cisplatin's ligands already placed (cis). Click Disconnect all to clear the sites and place them yourself. The first ligand then becomes active (highlighted).",
    waitFor: "assign-cleared",
    waitLabel: "Click Disconnect all",
    interactive: true,
  },
  {
    // The chips + 3D scene only, scrolled to the TOP of the window: on a phone the card
    // otherwise covers the lower sites the user has to tap.
    target: "assign-workspace",
    scrollBlock: "start",
    title: "Place the ligands",
    body: "The highlighted chip is the active ligand. Click a numbered site to seat it, and the next ligand highlights automatically. For transplatin, put the two chlorides on OPPOSITE (trans) sites and the two ammines on the other pair. Drag anywhere in the scene to rotate it.",
    waitFor: "assign-build",
    waitLabel: "Place all four ligands on their sites",
    interactive: true,
  },
  {
    target: "assign-build",
    title: "Save this isomer",
    body: "All four are placed. Drag the scene to rotate and check your isomer, then click Save this isomer to remember transplatin. It does not build yet.",
    waitFor: "custom-isomer-flag",
    waitLabel: "Click Save this isomer",
    interactive: true,
  },
  {
    target: "custom-isomer-flag",
    title: "Your isomer is remembered",
    body: "The row now shows a custom-isomer flag. MeCoBi stored your placement, so Build all will build transplatin for cisplatin and the default sandwich for ferroquine. Clear it with the × any time.",
  },
  {
    target: "build-all-btn",
    title: "8 · Build everything",
    body: "Last step: Build all queues every row as one job and builds them. Click it now to build your transplatin and the ferroquine sandwich. With xtb relaxation on, this can take a little while.",
    waitFor: "results-card",
    waitLabel: "Click Build all (this can take a moment)",
    interactive: true,
  },
  {
    target: "results-card",
    title: "9 · Your structures",
    body: "Here they are. Drag a structure to rotate it, tick others to compare side by side, download as .xyz / .mol / .pdb, or convert them back to SMILES / T-REX.",
    interactive: true,
  },
  {
    title: "That's the tour!",
    body: "You're set: describe complexes, Parse, then Build or Build all to generate 3D structures. Reopen this any time from “Tour”. Happy building!",
  },
];
