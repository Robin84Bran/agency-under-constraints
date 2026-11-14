"""Standard-library finite-benchmark statistics; no model or service imports.

Bootstrap weights are frozen estimand weights. Resampling whole units multiplies
all members' weights by the sampled unit multiplicity. Thus a twice sampled
unit contributes twice, even when its evidence bytes are identical.
"""
import math
import random
from collections import Counter, defaultdict


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def wilson(successes, total, z=1.959963984540054):
    """Nominal descriptive interval only: episodes are not independent trials."""
    if total <= 0:
        return None
    p = successes / total
    scale = 1 + z * z / total
    center = (p + z * z / (2 * total)) / scale
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / scale
    return [max(0.0, center - half), min(1.0, center + half)]


def percentile(values, q):
    if not values:
        return None
    ordered = sorted(values)
    x = (len(ordered) - 1) * q
    low = int(x)
    return ordered[low] + (ordered[min(low + 1, len(ordered) - 1)] - ordered[low]) * (x - low)


def inverse_group_weights(keys):
    sizes = Counter(keys)
    return [1.0 / sizes[key] for key in keys]


def weighted_rate(values, weights=None, eligible=None):
    weights = weights if weights is not None else [1] * len(values)
    eligible = eligible if eligible is not None else [True] * len(values)
    return ratio(sum(w * float(v) for v, w, keep in zip(values, weights, eligible) if keep),
                 sum(w for w, keep in zip(weights, eligible) if keep))


def aggregate_blocks(terms, units):
    """Terms is a list of (numerator, denominator) contributions per episode."""
    out = defaultdict(lambda: [0.0, 0.0])
    for (numerator, denominator), unit in zip(terms, units):
        out[unit][0] += numerator
        out[unit][1] += denominator
    return dict(out)


def evaluate_sample(terms, units, sampled_units):
    """A transparent multiplicity-preserving helper used in offline tests."""
    grouped = aggregate_blocks(terms, units)
    numerator = denominator = 0.0
    for unit in sampled_units:
        a, b = grouped[unit]
        numerator += a
        denominator += b
    return ratio(numerator, denominator)


def bootstrap_endpoints(endpoints, units, replicates=10000, seed=20261112, minimum_blocks=10):
    """Paired percentile bootstrap for rates and paired differences.

    Each endpoint is a list of one or more terms arrays: one array estimates a
    rate, two estimate second-minus-first. All endpoints use the same draws.
    Units with zero denominator do not count toward endpoint support. An empty
    truth subset yields null for that replicate and its count is disclosed.
    """
    if type(replicates) is not int or replicates < 1:
        raise ValueError('bootstrap replicates must be positive')
    names = list(dict.fromkeys(units))
    grouped = {name: [aggregate_blocks(term, units) for term in terms]
               for name, terms in endpoints.items()}
    output, active = {}, {}
    for name, terms in grouped.items():
        supports = [sum(block.get(unit, (0, 0))[1] > 0 for unit in names) for block in terms]
        count = min(supports) if supports else 0
        if count < minimum_blocks:
            output[name] = {'interval': None, 'support_blocks': count, 'null_replicates': None,
                            'reason': 'fewer than ten supporting blocks/groups', 'replicates': replicates}
            continue
        # Constant rates are exact under every resampling with nonempty support.
        # Do not shortcut missing-subset draws: their null counts still matter.
        summaries = []
        for term in terms:
            supported = {unit for unit in names if term.get(unit, (0, 0))[1] > 0}
            rates = [term[u][0] / term[u][1] for u in supported]
            constant = rates[0] if rates and all(abs(v - rates[0]) < 1e-14 for v in rates) else None
            summaries.append((term, supported, constant))
        active[name] = (summaries, [])
    rng = random.Random(seed)
    for _ in range(replicates):
        multiplicity = Counter(rng.choices(names, k=len(names)))
        drawn = set(multiplicity)
        for name, (terms, values) in active.items():
            rates = []
            for term, supported, constant in terms:
                if constant is not None:
                    rates.append(constant if supported.intersection(drawn) else None)
                    continue
                a = b = 0.0
                for unit, count in multiplicity.items():
                    n, d = term.get(unit, (0, 0))
                    a += n * count
                    b += d * count
                rates.append(ratio(a, b))
            values.append(None if any(v is None for v in rates) else
                          (rates[0] if len(rates) == 1 else rates[1] - rates[0]))
    for name, (terms, values) in active.items():
        valid = [v for v in values if v is not None]
        output[name] = {'interval': [percentile(valid, .025), percentile(valid, .975)] if valid else None,
                        'support_blocks': min(len(supported) for term, supported, constant in terms),
                        'null_replicates': len(values) - len(valid), 'replicates': replicates,
                        'reason': None if valid else 'all replicates lack a required truth subset'}
    return output
