"""MeCoBi web layer — a thin orchestration wrapper over the core.

No chemistry lives here: every endpoint imports and calls :mod:`mecobi` core.
Local and web share the *same* code path (invariant 2). This minimal app exposes
parse/build/file endpoints and serves the static frontend; the async job queue,
sandboxing, auth seam and 24 h cleanup are layered on later.
"""

from .app import app, create_app

__all__ = ["app", "create_app"]
