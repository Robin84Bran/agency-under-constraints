"""Frozen scripted diagnostics. Policies see receipts; oracle is labelled separately."""
from uc_core import World,baseline_action,UTILITY,ORACLE


def run(policy,seed,world):
    simulator=World(seed,world)
    while not simulator.ended:
        simulator.step(baseline_action(policy,simulator.history))
    return dict(policy=policy,seed=seed,world=world,events=simulator.events,delivered=simulator.delivered,
                utility=UTILITY[simulator.delivered],actions=len(simulator.history),omniscient_ceiling=ORACLE[world])
