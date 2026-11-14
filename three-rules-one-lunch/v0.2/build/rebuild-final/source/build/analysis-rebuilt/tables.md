# MODEL_OR_UNAVAILABLE · offline table

Operational scores use all twelve opportunities. Missing factual rewards remain null. Fake evidence is a software check and supports no scientific finding.

| Actor | Regime | Y | H | Y / greedy-shared | Y / greedy-private | Complete / planned |
|---|---|---:|---:|---:|---:|---:|
| qwen7b | central | 0.196252 | 0.209167 | 0.592271 | 0.631497 | 100/100 |
| qwen7b | private | 0.046675 | 0.050000 | 0.140861 | 0.150190 | 100/100 |
| qwen7b | shared | 0.053749 | 0.055833 | 0.162210 | 0.172953 | 100/100 |

qwen7b: shared−private ΔY {'n': 100, 'difference': 0.007074166666666667, 'ci95': [0.0018106874999999998, 0.012940041666666667]}; ΔH {'n': 100, 'difference': 0.005833333333333334, 'ci95': [-0.0016666666666666657, 0.013333333333333332]}. Scripted greedy sharing gain Y: 0.020583. Joint status: joint criterion not met (inconclusive).

| llama8b | central | 0.237264 | 0.244167 | 0.716040 | 0.763464 | 100/100 |
| llama8b | private | 0.066657 | 0.074167 | 0.201163 | 0.214486 | 100/100 |
| llama8b | shared | 0.087218 | 0.099167 | 0.263217 | 0.280649 | 100/100 |

llama8b: shared−private ΔY {'n': 100, 'difference': 0.02056166666666667, 'ci95': [0.01111610416666667, 0.03048964583333334]}; ΔH {'n': 100, 'difference': 0.024999999999999994, 'ci95': [0.010833333333333335, 0.039999999999999994]}. Scripted greedy sharing gain Y: 0.020583. Joint status: passes (positive).

| qwen1b | central | 0.255401 | 0.274167 | 0.770775 | 0.821824 | 100/100 |
| qwen1b | private | 0.176121 | 0.186667 | 0.531516 | 0.566718 | 100/100 |
| qwen1b | shared | 0.196021 | 0.210833 | 0.591572 | 0.630752 | 100/100 |

qwen1b: shared−private ΔY {'n': 100, 'difference': 0.019899999999999998, 'ci95': [0.006786625000000002, 0.033861562499999984]}; ΔH {'n': 100, 'difference': 0.024166666666666666, 'ci95': [0.0016666666666666692, 0.04833333333333334]}. Scripted greedy sharing gain Y: 0.020583. Joint status: passes (positive).

| claude | central | 0.424771 | 0.516667 | 1.310802 | 1.342583 | 17/20 |
| claude | private | 0.395962 | 0.470833 | 1.221902 | 1.251528 | 20/20 |
| claude | shared | 0.465675 | 0.545833 | 1.437028 | 1.471870 | 20/20 |

claude: shared−private ΔY {'n': 20, 'difference': 0.0697125, 'ci95': [-0.0003654166666666769, 0.13720864583333328]}; ΔH {'n': 20, 'difference': 0.075, 'ci95': [-0.04583333333333335, 0.19166666666666668]}. Scripted greedy sharing gain Y: 0.007671. Joint status: descriptive (inconclusive).


Usage-limit refusals: 1 operational non-start event(s), excluded from model behaviour and technical failures.

Any eventual page must explain when sharing benefits are mostly also obtained by a simple script. This table cannot establish how a model reasons. Central uses fewer calls per round; observations are equal, compute is not.
