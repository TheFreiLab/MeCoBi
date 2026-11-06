"""3D-xyz -> PyG graph builder + GINE classifier (shared by train and Phase-B inference).

Node/edge featurization matches the original 3D_xyz2graph notebook. radius_graph is
reimplemented with torch.cdist so torch_cluster is not required.
"""
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from pathlib import Path
from torch_geometric.data import Data
from torch_geometric.nn import GINEConv, global_mean_pool
from rdkit import Chem
from xyz2graph import MolGraph

_PT = Chem.GetPeriodicTable()
_ELEMENTS = ["H", "C", "N", "O", "S", "P", "F", "Cl", "Br", "I",
             "Ir", "Rh", "Ru", "Pt", "Pd", "Au", "Ag", "Fe", "Co", "Ni", "Cu", "Zn", "Other"]
_METALS = {"Ir", "Rh", "Ru", "Pt", "Pd", "Au", "Ag", "Fe", "Co", "Ni", "Cu"}
RADIUS = 3.0


def _node_feat(sym):
    try:
        Z = _PT.GetAtomicNumber(sym)
    except Exception:
        Z = 0
    enc = [int(sym == e) for e in _ELEMENTS]
    if sym not in _ELEMENTS:
        enc[-1] = 1
    mass = _PT.GetAtomicWeight(Z) if Z > 0 else 0
    cov = _PT.GetRcovalent(Z) if Z > 0 else 0
    vdw = _PT.GetRvdw(Z) if Z > 0 else 0
    return np.array(enc + [Z / 100, mass / 200, cov / 2, vdw / 3], dtype=np.float32)


def radius_graph_cdist(pos, r=RADIUS):
    """Directed edges (both ways) for atom pairs within r Angstrom; no self-loops."""
    d = torch.cdist(pos, pos)
    mask = (d <= r) & (d > 0)
    idx = mask.nonzero(as_tuple=False).t().contiguous()  # [2, E]
    return idx


def xyz_to_graph(xyz_path, identifier=None):
    mg = MolGraph()
    mg.read_xyz(str(xyz_path))
    syms = list(mg.elements)
    x = torch.tensor(np.array([_node_feat(s) for s in syms]), dtype=torch.float)
    pos = torch.tensor(np.vstack([mg.x, mg.y, mg.z]).T.astype(np.float32), dtype=torch.float)
    ei = radius_graph_cdist(pos, RADIUS)
    row, col = ei
    dist = (pos[row] - pos[col]).norm(dim=1)
    ea = []
    for i, j, dd in zip(row.tolist(), col.tolist(), dist.tolist()):
        metal = int(syms[i] in _METALS or syms[j] in _METALS)
        ea.append([dd, 1.0 / (dd + 1e-6), _PT.GetAtomicNumber(syms[i]) / 100,
                   _PT.GetAtomicNumber(syms[j]) / 100, metal])
    edge_attr = torch.tensor(ea, dtype=torch.float)
    data = Data(x=x, edge_index=ei, edge_attr=edge_attr, pos=pos)
    data.identifier = identifier or Path(xyz_path).stem
    return data


def build_graphs(folder, label_map=None, stem_clean=lambda s: s.replace("_OPT", "")):
    """Build graphs for every .xyz in folder. If label_map given, attach y and keep only
    compounds present in it. Returns list of Data."""
    graphs = []
    for p in sorted(Path(folder).glob("*.xyz")):
        cid = stem_clean(p.stem)
        if label_map is not None and cid not in label_map:
            continue
        try:
            g = xyz_to_graph(p, cid)
        except Exception as e:
            print(f"  skip {p.name}: {e}")
            continue
        if label_map is not None:
            g.y = torch.tensor([float(label_map[cid])], dtype=torch.float)
        graphs.append(g)
    return graphs


class GINEClassifier(nn.Module):
    """GINE (2 conv layers) binary classifier; logit output (use BCEWithLogitsLoss)."""
    def __init__(self, in_channels, hidden=128, edge_dim=5, edge_emb=64):
        super().__init__()
        self.lin1 = nn.Linear(in_channels, hidden)
        self.edge_mlp = nn.Sequential(nn.Linear(edge_dim, edge_emb), nn.ReLU(), nn.Linear(edge_emb, hidden))
        self.gin_mlp1 = nn.Sequential(nn.Linear(hidden, hidden), nn.ReLU(), nn.Linear(hidden, hidden))
        self.gin_mlp2 = nn.Sequential(nn.Linear(hidden, hidden), nn.ReLU(), nn.Linear(hidden, hidden))
        self.conv1 = GINEConv(self.gin_mlp1, edge_dim=hidden, train_eps=True)
        self.conv2 = GINEConv(self.gin_mlp2, edge_dim=hidden, train_eps=True)
        self.lin2 = nn.Linear(hidden, hidden)
        self.head = nn.Sequential(nn.Linear(hidden, hidden // 2), nn.ReLU(), nn.Linear(hidden // 2, 1))

    def forward(self, x, edge_index, edge_attr, batch):
        x = F.relu(self.lin1(x))
        e = F.relu(self.edge_mlp(edge_attr))
        x = F.relu(self.conv1(x, edge_index, e))
        x = F.relu(self.lin2(x))
        x = F.relu(self.conv2(x, edge_index, e))
        x = global_mean_pool(x, batch)
        return self.head(x).squeeze(1)
