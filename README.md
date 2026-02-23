# animus-ai
Curiosity-driven AI agent that develops behavioral criteria through pure environmental experience — no supervised learning, no token prediction.
Runs on a laptop CPU.

## What it does
ANIMUS explores complex environments and builds episodic memory from direct experience.
Tested in Pokémon Blue: starting from a single room, the agent autonomously discovered
6 maps including Viridian City — with no objective except the pull of novelty.

## Results after ~800,000 steps
- 6 maps discovered autonomously
- 4,386 emergent behavioral criteria
- Base-camp exploration pattern emerged without programming
- Novelty saturation cycles consistent with biological curiosity

## Requirements
- Python 3.10+
- PyBoy
- Your own copy of Pokémon Blue ROM

## Install
pip install pyboy pygame

## Run
python conscious_agent_v16.py pokemon_azul.gb 200000

## ANIMUS Web — Update v2.0

The same principle, now exploring the open web.

Starting from a random Wikipedia page about an Iranian village,
the agent developed spontaneous attraction to neuroscience and 
scientific research after 800 pages — without any instruction.

**Results after 800 pages:**
- 2,524 emergent conceptual criteria
- Top domains: ScienceDaily, BBC, ArXiv, Nature
- Top concepts: scientists, brain, researchers, arxiv
- Concept evolution: geography → neuroscience → stable science identity

```
Page   50:  wikipedia | categoria | district    ← geographic, random
Page  100:  brain | researchers | your          ← first science attraction  
Page  200:  brain | scientists | news           ← consolidation
Page  500:  scientists | arxiv | brain          ← stable identity
Page  800:  scientists | arxiv | your           ← maturity
```

Nobody told it science was important. It got there through novelty alone.

**Top domains after 800 pages:**
| Domain | Value | Pages Visited |
|--------|-------|---------------|
| ScienceDaily | 2,664 | 198 |
| BBC | 1,860 | 120 |
| Wikipedia (EN) | 1,411 | 114 |
| ArXiv | 593 | 48 |
| Nature | 337 | 30 |

Run:
```
pip install requests beautifulsoup4
python animus_web.py 500


## Architecture

ANIMUS is built on three components:

**Memory** — emergent criteria weighted by novelty. Hard ceiling of 100 prevents pathological loops (analogous to biological memory regulation).

**Will** — probabilistic action selection weighted by novelty estimates. Anti-obsession mechanisms prevent territory capture.

**Interviewer** — periodic snapshots of the agent's current identity: what it values most, what concepts it has reinforced, how it has evolved.

---

## Core Philosophy

Current AI learns through prediction — next token, future reward. An external designer defines success.

ANIMUS asks a different question: what if the only drive was the intrinsic pull of the unknown?

The result in Pokémon: a spatial explorer that developed a preference for northward movement.  
The result on the web: a science reader that gravitates toward research and discovery.

Neither preference was designed. Both emerged from experience alone.

> *An agent that wants nothing except to see something new will, given enough time, develop a character.*

---

## Cross-Domain Comparison

| Aspect | Pokémon | Web |
|--------|---------|-----|
| Position | (map, x, y) | (domain, keyword_cluster) |
| Novelty | Unvisited coordinate | New concept keywords |
| Actions | 8 discrete buttons | N hyperlinks |
| Environment | Closed, deterministic | Open, infinite |
| Identity emerged | Spatial explorer | Science reader |
| Hardware | Laptop CPU | Laptop CPU + internet |

---

## Limitations

- No generalization across environments
- Linear memory growth
- No temporal planning or goal hierarchy
- Web: keyword extraction is shallow (TF-IDF, no semantic understanding)

These are documented honestly because they matter.

---

## Files

| File | Description |
|------|-------------|
| `conscious_agent_v16.py` | ANIMUS Pokémon agent |
| `animus_web.py` | ANIMUS Web agent |
| `jugar_manual.py` | Manual play with position logging |
| `ROM_NOTICE.txt` | Copyright notice |

---

## Author

**Ernesto Antonio Arias Díaz**  
Independent Researcher | Santo Domingo, Dominican Republic  
Linux System Administrator | Algorithmic Trader | Chess Player (FIDE 2000)



## Support

If this project was useful to you, USDT donations are welcome:

BEP20: 0x682d792095ec89176af6d6d736388d61ea54f5d5 TRC20: TBBpUCkhSc9EuverYayokZzWP2xLfCTx2R

ERC20: 0x682d792095ec89176af6d6d736388d61ea54f5d5

TRC20: TBBpUCkhSc9EuverYayokZzWP2xLfCTx2R

*ANIMUS — because curiosity alone is enough to develop a character.*

