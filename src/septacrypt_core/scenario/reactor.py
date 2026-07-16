"""The Entangled Reactor — a real umwelt CumulantCluster, not a GameHost/spec
integration. CumulantCluster is self-contained (constructor takes zone_name,
qubit_roles, gamma, dt, connectivity — no host dependency; see its own
docstring: "Drop-in on the READ interface the field/readout use"). Routing
this through GameHost.register_world() would require a real DomainSpec whose
node/binding declarations translate into ZZ couplings via the engine's own
construction pipeline — a materially bigger undertaking than this scenario
needs. We use the cluster directly.
"""
from umwelt.substrate.cumulant_cluster import CumulantCluster

ROLES = ["valve_17", "coolant_pump", "temp_sensor"]

# Convention (matches geometry/atlas.py's axis order): valve=father (structure),
# pump=son (energy), sensor=spirit (information).


def build_entangled_reactor() -> CumulantCluster:
    """
    Builds a 3-qubit CumulantCluster representing the Repair Station.
    connectivity=None (the constructor default) means dense all-pairs ZZ terms
    are allocated, so both couplings below land on real, pre-existing keys.
    """
    cluster = CumulantCluster(
        zone_name="Repair_Station",
        qubit_roles=ROLES,
        gamma=0.02,
        dt=0.1,
    )

    # ZZ couplings, keyed by qubit index (0=valve_17, 1=coolant_pump, 2=temp_sensor).
    zz_couplings = {
        (0, 1): 0.8,  # Valve <-> Pump coupling
        (1, 2): 0.5,  # Pump <-> Sensor coupling
    }

    # Transverse (x) fields drive natural drift into superposition between LOOKs.
    h_fields = [
        [0.2, 0.0, 0.0],  # Valve
        [0.2, 0.0, 0.0],  # Pump
        [0.1, 0.0, 0.0],  # Sensor
    ]

    cluster.set_couplings(h_fields=h_fields, zz=zz_couplings)
    return cluster
