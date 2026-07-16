"""Dynamics identity constants for certificates and stable integration policy."""

# Bump when reactor couplings, cumulant semantics, or event application change.
DYNAMICS_VERSION = "septacrypt.reactor.cumulant.v1+umwelt@aa12f943"

# Topology configs for world snapshots (reactor vs ship manifold).
TOPOLOGY_REACTOR = "topology.reactor.v1"
TOPOLOGY_SHIP = "topology.ship.v1+bridges.soft.v1"

# Empirically verified stable range for reactor/zone gamma/dt parameters.
MAX_STABLE_DT_SCALE = 1.0

# Max abs residual on e1/e2 for a verified replay certificate.
DEFAULT_RESIDUAL_TOLERANCE = 1e-9
