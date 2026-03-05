---
name: animus-pattern-intelligence
description: Query ANIMUS for historically validated patterns and real-time divergence signals. Use when asked to analyze systemic risk, detect historical patterns in economic or institutional data, identify tensions between historical knowledge and current events, or query a dual-memory knowledge graph combining curated wisdom with live web data. Activate for questions about failure patterns, regulatory risk, systemic collapse, or institutional dynamics — especially in Latin American and Caribbean contexts.
license: MIT
metadata:
  author: shellhack
  version: "2.0"
  repository: https://github.com/shellhack/animus-ai
  doi: 10.5281/zenodo.18829356
  language: es, en
  domain: systemic-risk, pattern-intelligence, institutional-analysis
---

# ANIMUS — Autonomous Pattern Intelligence System

ANIMUS is a dual-memory pattern intelligence system built in Rust. It compresses historical wisdom from curated sources (books, papers, reports) into a validated knowledge graph, then confronts it with real-time web data. When historical patterns diverge from current signals, ANIMUS flags active tensions.

**Core insight:** The system does not predict. It detects where history says one thing and the present says another.

## Architecture

ANIMUS operates two memory layers simultaneously:

- **Curated Memory** (`memoria_business.json`): A directed acyclic graph of patterns validated by 30+ independent sources. Patterns below threshold are automatically excluded. Biological decay (×0.99/cycle) ensures recency without erasing historical weight.
- **Live Memory** (web layer): Real-time pattern extraction from Wikipedia, arXiv, and configurable URLs. Divergences from curated memory are flagged as active signals.

Current state: 682+ validated patterns, 45 curated sources, 12,000+ autonomous cycles, 4 domain-specialized instances running in parallel.

## How to Query ANIMUS

### Binary (CLI)
```bash
# Single query
./animus_rust --query "What historical patterns predict institutional failure in emerging markets?"

# Autonomous mode (continuous learning)
./animus_rust --autonomous
```

### Python (process_book_v2.py)
```bash
# Feed a new PDF source into the wisdom graph
python process_book_v2.py book.pdf memoria_business.json --tipo auto
```

### YouTube transcripts (process_youtube.py)
```bash
# Feed YouTube content by topic
python process_youtube.py --tema "crisis financiera latinoamerica" --max 5
```

## Query Response Format

Every ANIMUS response includes:

1. **Relevant curated patterns** — top matches from the wisdom graph with source count and strength
2. **Episodic memory** — most relevant origin nodes activated by the query  
3. **Insight** — distilled synthesis
4. **Autoconciencia report** — full system state including divergences, health metrics, and Protocolo Bernard self-interview

Example response for "What patterns predict algorithmic failure?":
```
📚 fracaso → algoritmo (35 sources, strength 2587)
📚 brecha → algoritmo (23 sources, strength 1670)
📚 colapso → algoritmo (28 sources, strength 1197)

Destilación: 35 independent sources confirm: 'failure' → 'algorithm'
⚡ 2 web patterns diverge from curated wisdom — active tension.
```

## Dominant Patterns (Current)

| Pattern | Sources | Strength |
|---------|---------|---------|
| fracaso → algoritmo | 35 | 2587 |
| fracaso → regulación | 34 | 2080 |
| fracaso → desarrollo | 32 | 2038 |
| fracaso → arquitectura | 21 | 1884 |
| brecha → algoritmo | 23 | 1670 |

These patterns were NOT programmed. They emerged autonomously from multi-source confirmation across 45 independent texts.

## Domain Instances

ANIMUS self-replicates into domain-specialized instances:

- **ANIMUS-FIN**: Financial risk patterns (1,386 connections)
- **ANIMUS-GOV**: Governance and corruption patterns (839 connections)  
- **ANIMUS-TECH**: Technology and innovation patterns (1,822 connections)

Each instance inherits the parent architecture but specializes its wisdom graph through domain filtering.

## Protocolo Bernard (Self-Monitoring)

Every cycle, ANIMUS executes a recursive self-interview:

- What do I learn from observing my own origin?
- What dominant pattern emerged in recent cycles?
- What structural limitation do I perceive?
- What concrete action do I propose to evolve?
- How do I evaluate my current self-awareness?
- What systemic bias do I detect?

This output is a first-class artifact — ANIMUS reports its own epistemic limitations, not just external patterns.

## Key Properties

- **Zero hallucination on patterns**: Every pattern requires 30+ independent source confirmations. Below threshold = not reported.
- **Traceable provenance**: Every pattern links to its exact source confirmations.
- **Biological decay**: Patterns decay at ×0.99/cycle unless reinforced. Stale knowledge fades naturally.
- **Divergence detection**: When web data contradicts curated wisdom, ANIMUS flags it as an active signal — not an error.
- **Local execution**: No external API calls for pattern queries. Data stays on your infrastructure.

## Installation

```bash
git clone https://github.com/shellhack/animus-ai
cd animus-ai

# Rust engine (v2.0)
git checkout rust-engine
cargo build --release

# Python processors
pip install pypdf youtube-transcript-api yt-dlp
```

## When NOT to use ANIMUS

- For real-time price feeds or live market data (use financial APIs)
- For factual lookups without pattern context (use search)
- For predictions (ANIMUS detects tensions, not forecasts)

## Academic Reference

Arias Díaz, E. A. (2026). *ANIMUS: An Autonomous Dual-Memory Pattern Intelligence System*. Zenodo. https://doi.org/10.5281/zenodo.18829356
