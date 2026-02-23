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

Run:
```
pip install requests beautifulsoup4
python animus_web.py 500



## Support

If this project was useful to you, USDT donations are welcome:

BEP20: 0x682d792095ec89176af6d6d736388d61ea54f5d5 TRC20: TBBpUCkhSc9EuverYayokZzWP2xLfCTx2R

ERC20: 0x682d792095ec89176af6d6d736388d61ea54f5d5

TRC20: TBBpUCkhSc9EuverYayokZzWP2xLfCTx2R
