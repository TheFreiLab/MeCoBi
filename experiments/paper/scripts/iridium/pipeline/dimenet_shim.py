"""Pure-torch replacements for torch_cluster.radius_graph and torch_sparse-based
triplets, so PyG's DimeNetPlusPlus runs without compiled companion packages.
Import this module BEFORE using DimeNetPlusPlus; it patches the dimenet module.
"""
import torch
import torch_geometric.nn.models.dimenet as _dm


def radius_graph(pos, r, batch=None, loop=False, max_num_neighbors=32,
                 flow="source_to_target", num_workers=None, **kw):
    d = torch.cdist(pos, pos)
    N = pos.size(0)
    mask = d <= r
    if not loop:
        mask.fill_diagonal_(False)
    if batch is not None:
        mask &= (batch.view(-1, 1) == batch.view(1, -1))
    if max_num_neighbors and max_num_neighbors < N:
        dd = d.masked_fill(~mask, float("inf"))
        k = min(max_num_neighbors, N)
        idx = dd.topk(k, dim=1, largest=False).indices
        keep = torch.zeros_like(mask)
        keep.scatter_(1, idx, True)
        mask &= keep
    src, dst = mask.nonzero(as_tuple=True)  # dst is a neighbor of src
    if flow == "source_to_target":
        return torch.stack([dst, src], dim=0)
    return torch.stack([src, dst], dim=0)


def triplets(edge_index, num_nodes):
    """Reproduce torch_geometric.nn.models.dimenet.triplets without SparseTensor.
    edge_index rows are (j -> i). Returns i, j, idx_i, idx_j, idx_k, idx_kj, idx_ji
    for angle triplets k -> j -> i with k != i."""
    row, col = edge_index  # row = j (source), col = i (target)
    E = row.size(0)
    counts = torch.bincount(col, minlength=num_nodes)          # incoming edges per node
    ptr = torch.cat([col.new_zeros(1), counts.cumsum(0)])
    order = torch.argsort(col, stable=True)                     # edge ids sorted by target
    num_triplets = counts[row]                                  # per edge e, |incoming(j)|
    idx_i = torch.repeat_interleave(col, num_triplets)
    idx_j = torch.repeat_interleave(row, num_triplets)
    total = int(num_triplets.sum())
    if total == 0:
        z = row.new_zeros(0)
        return col, row, z, z, z, z, z
    e_ids = torch.repeat_interleave(torch.arange(E, device=row.device), num_triplets)
    base = torch.cumsum(num_triplets, 0) - num_triplets
    within = torch.arange(total, device=row.device) - torch.repeat_interleave(base, num_triplets)
    pos_in_order = ptr[row][e_ids] + within
    idx_kj = order[pos_in_order]        # edge f = k -> j
    idx_k = row[idx_kj]                 # node k
    idx_ji = e_ids                      # edge e = j -> i
    mask = idx_i != idx_k
    return col, row, idx_i[mask], idx_j[mask], idx_k[mask], idx_kj[mask], idx_ji[mask]


def patch():
    _dm.radius_graph = radius_graph
    _dm.triplets = triplets
