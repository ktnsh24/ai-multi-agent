# Hands-on Labs — Config Tuning (Tier 1–5)

> **Why these labs exist:** This is the AI-engineering interview answer. When asked "how would you tune this system?" the answer is a guided tour of these sweeps + their trade-offs.
>
> **How to run:** Each lab changes ONE config in `.env`, runs the same 3 questions, records the metrics, and explains the trade-off.
>
> **🫏 Donkey lens:** Each lab ends with a donkey takeaway summarising the trade-off in plain language.

## Table of Contents
- [Setup — Common to all labs](#setup--common-to-all-labs)
- [Lab 1: Chunk Size Sweep](#lab-1-chunk-size-sweep)
- [Lab 2: Chunk Overlap Sweep](#lab-2-chunk-overlap-sweep)
- [Lab 3: top_k Sweep](#lab-3-top_k-sweep)
- [Lab 4: Temperature Sweep](#lab-4-temperature-sweep)
- [Lab 5: System Prompt Sweep](#lab-5-system-prompt-sweep)
- [Lab 6: Embedding Model Sweep](#lab-6-embedding-model-sweep)
- [Lab 7: Reranker On/Off](#lab-7-reranker-onoff)
- [Lab 8: Hybrid Search On/Off](#lab-8-hybrid-search-onoff)
- [Lab 9: Query Rewriting On/Off](#lab-9-query-rewriting-onoff)
- [Lab 10: Metadata Filtering](#lab-10-metadata-filtering)
- [Lab 11: Eval Thresholds](#lab-11-eval-thresholds)
- [Lab 12: Agent Count Sweep](#lab-12-agent-count-sweep)
- [Lab 13: Max Iterations Sweep](#lab-13-max-iterations-sweep)

---

## Setup — Common to all labs

1. Make sure the API + WebSocket are running: `poetry run uvicorn src.main:app --port 8401 --reload`
2. Make sure Redis is up: `docker compose up -d redis`
3. Have the 3 fixed test questions ready (mix of RAG + agent coordination):
   - **Q1:** "Research the trade-offs between RAG and fine-tuning and produce a 5-bullet summary."
   - **Q2:** "Find the latest version of CrewAI on PyPI and cite the release notes."
   - **Q3:** "From our ingested portfolio docs, list every repo that uses Bedrock."
4. Each lab takes ~5–10 min: change config → restart/re-ingest → run questions → record table

---

## Lab 1: Chunk Size Sweep — "How big should each backpack pocket be?"

**Config:** `RAG_CHUNK_SIZE` (default: `500`)
**What it controls:** Number of characters per chunk during ingestion.
**Hypothesis:** Small chunks = precise but miss cross-section context; large chunks = more context but lower retrieval precision.

### Setup
1. Set `RAG_CHUNK_SIZE=200` in `.env`
2. Re-ingest: `poetry run python -m src.ingestion.run`
3. Run the same 3 questions (Q1–Q3)
4. Repeat for each value below

### Results table (fill in as you run)
| Value | Retrieval | Faithfulness | Latency (ms) | Cost (€) | Notes |
|---|---|---|---|---|---|
| 200 | ___ | ___ | ___ | ___ | ___ |
| 500 | ___ | ___ | ___ | ___ | ___ |
| 1000 | ___ | ___ | ___ | ___ | ___ |

### What we learned
Multi-agent systems amplify chunk-size effects: each agent retrieves independently, so the wrong size compounds. Tune chunk size against the agent that does the heaviest retrieval (usually the researcher).

### 🫏 Donkey takeaway
Tiny pockets per donkey mean each one carries a clean fact, but the herd loses the storyline; giant pockets bury every donkey under irrelevant cargo.

---

## Lab 2: Chunk Overlap Sweep — "Should pockets share content at the edges?"

**Config:** `RAG_CHUNK_OVERLAP` (default: `100`)
**What it controls:** Characters duplicated between adjacent chunks.
**Hypothesis:** Higher overlap = better answers spanning section boundaries, more storage cost.

### Setup
1. Set `RAG_CHUNK_OVERLAP=0` in `.env`
2. Re-ingest: `poetry run python -m src.ingestion.run`
3. Run the same 3 questions (Q1–Q3)
4. Repeat for each value below

### Results table (fill in as you run)
| Value | Retrieval | Faithfulness | Latency (ms) | Cost (€) | Notes |
|---|---|---|---|---|---|
| 0 | ___ | ___ | ___ | ___ | ___ |
| 100 | ___ | ___ | ___ | ___ | ___ |
| 200 | ___ | ___ | ___ | ___ | ___ |

### What we learned
10–20% overlap is the safe default; agents passing summaries between each other already provide some redundancy, so don't double-pay with huge overlap.

### 🫏 Donkey takeaway
Letting two backpack pockets share their last few sentences keeps a sentence cut in half intact — the donkey just carries those words twice.

---

## Lab 3: top_k Sweep — "How many pockets should each agent carry?"

**Config:** `RAG_TOP_K` (default: `5`)
**What it controls:** Number of chunks pulled from the vector store per retrieval call.
**Hypothesis:** Low = focused & cheap; high = noisy, dilutes retrieval average — and multiplied across agents.

### Setup
1. Set `RAG_TOP_K=1` in `.env`
2. Run the same 3 questions (Q1–Q3) — no re-ingest needed
3. Repeat for each value below

### Results table (fill in as you run)
| Value | Retrieval | Faithfulness | Latency (ms) | Cost (€) | Notes |
|---|---|---|---|---|---|
| 1 | ___ | ___ | ___ | ___ | ___ |
| 3 | ___ | ___ | ___ | ___ | ___ |
| 5 | ___ | ___ | ___ | ___ | ___ |
| 10 | ___ | ___ | ___ | ___ | ___ |

### What we learned
top_k×agent_count is the real cost driver — 4 agents × top_k=10 = 40 chunks of context per question. Right-size top_k before scaling agents.

### 🫏 Donkey takeaway
One pocket is fast but risky; ten pockets per donkey × four donkeys = a stable full of cargo nobody reads.

---

## Lab 4: Temperature Sweep — "How creative should each agent be?"

**Config:** `LLM_TEMPERATURE` (default: `0.3`)
**What it controls:** Sampling randomness for the LLM.
**Hypothesis:** Low temperature for executor agents; higher temperature only for the planner/brainstormer.

### Setup
1. Set `LLM_TEMPERATURE=0.0` in `.env`
2. Run the same 3 questions (Q1–Q3)
3. Repeat for each value below

### Results table (fill in as you run)
| Value | Retrieval | Faithfulness | Latency (ms) | Cost (€) | Notes |
|---|---|---|---|---|---|
| 0.0 | ___ | ___ | ___ | ___ | ___ |
| 0.3 | ___ | ___ | ___ | ___ | ___ |
| 0.7 | ___ | ___ | ___ | ___ | ___ |

### What we learned
In multi-agent loops, high temperature compounds: a creative planner spawns creative subtasks that creative workers freelance even further. Reserve heat for the planner only.

### 🫏 Donkey takeaway
Cold donkeys execute the route exactly; warm donkeys start improvising — fine for one but chaos for a herd.

---

## Lab 5: System Prompt Sweep — "Strict vs lax delivery note"

**Config:** `SYSTEM_PROMPT` per agent (default: balanced)
**What it controls:** Persona and rules each agent gets at every turn.
**Hypothesis:** Strict role boundaries ("you are ONLY the researcher, do not write the summary") prevent agents from stepping on each other.

### Setup
1. Set strict variants in `.env` / agent configs
2. Run the same 3 questions (Q1–Q3)
3. Repeat with lax variants

### Results table (fill in as you run)
| Value | Retrieval | Faithfulness | Latency (ms) | Cost (€) | Notes |
|---|---|---|---|---|---|
| strict | ___ | ___ | ___ | ___ | ___ |
| balanced | ___ | ___ | ___ | ___ | ___ |
| lax | ___ | ___ | ___ | ___ | ___ |

### What we learned
The single biggest quality lever — sharper role boundaries dramatically cut redundant work and crosstalk between agents.

### 🫏 Donkey takeaway
A delivery note saying "you carry mail, not parcels" stops the donkey from hauling everything; vague notes turn every donkey into a generalist.

---

## Lab 6: Embedding Model Sweep — "Smaller vs bigger GPS coordinates"

**Config:** `EMBEDDING_MODEL` (default: `nomic-embed-text` 768d)
**What it controls:** The model that maps text → vector.
**Hypothesis:** Bigger = higher retrieval quality + cost; **requires re-ingest + new index**.

### Setup
1. Set `EMBEDDING_MODEL=all-MiniLM-L6-v2` (384d) in `.env`
2. Drop and re-ingest: `poetry run python -m src.ingestion.run --reset`
3. Run the same 3 questions (Q1–Q3)
4. Repeat for each value below

### Results table (fill in as you run)
| Value | Retrieval | Faithfulness | Latency (ms) | Cost (€) | Notes |
|---|---|---|---|---|---|
| MiniLM (384d) | ___ | ___ | ___ | ___ | ___ |
| nomic-embed (768d) | ___ | ___ | ___ | ___ | ___ |
| Titan v2 (1024d) | ___ | ___ | ___ | ___ | ___ |

### What we learned
Deploy-day decision; rebuild the index when changing. Always re-evaluate on the same golden set so the comparison is fair.

### 🫏 Donkey takeaway
High-resolution GPS pins each parcel exactly; low-resolution GPS lumps similar parcels at the same junction and the donkey grabs the wrong one.

---

## Lab 7: Reranker On/Off — "Second-pass quality check"

**Config:** `RERANKER_ENABLED` + `RERANKER_MODEL` (default: `false`)
**What it controls:** Whether top_k×3 retrieved chunks are re-scored by a cross-encoder before stuffing.
**Hypothesis:** +10–20% retrieval quality, +200–500ms latency.

### Setup
1. Set `RERANKER_ENABLED=false` in `.env`
2. Run the same 3 questions (Q1–Q3)
3. Set `RERANKER_ENABLED=true` and `RERANKER_MODEL=BAAI/bge-reranker-base`, repeat

### Results table (fill in as you run)
| Value | Retrieval | Faithfulness | Latency (ms) | Cost (€) | Notes |
|---|---|---|---|---|---|
| off | ___ | ___ | ___ | ___ | ___ |
| bge-reranker-base | ___ | ___ | ___ | ___ | ___ |
| cohere-rerank-v3 | ___ | ___ | ___ | ___ | ___ |

### What we learned
Reranker pays off most for the researcher agent, where the cost of a bad chunk cascades into bad summaries downstream.

### 🫏 Donkey takeaway
Before the herd leaves the warehouse, an inspector keeps only the pockets the donkeys actually need.

---

## Lab 8: Hybrid Search On/Off — "GPS plus keyword radio"

**Config:** `HYBRID_SEARCH_ENABLED` + `HYBRID_ALPHA` (default: `false`, alpha `0.5`)
**What it controls:** Combine vector similarity with keyword (BM25) matching.
**Hypothesis:** Wins for queries with rare terms (names, IDs, error codes).

### Setup
1. Set `HYBRID_SEARCH_ENABLED=false` in `.env`
2. Run the same 3 questions (Q1–Q3)
3. Enable hybrid and sweep alpha

### Results table (fill in as you run)
| Value | Retrieval | Faithfulness | Latency (ms) | Cost (€) | Notes |
|---|---|---|---|---|---|
| off | ___ | ___ | ___ | ___ | ___ |
| alpha=0.3 | ___ | ___ | ___ | ___ | ___ |
| alpha=0.5 | ___ | ___ | ___ | ___ | ___ |
| alpha=0.7 | ___ | ___ | ___ | ___ | ___ |

### What we learned
Hybrid wins when agents reference exact symbols (CrewAI, Bedrock model IDs). Pure vector blurs them; pure keyword loses paraphrases.

### 🫏 Donkey takeaway
The herd uses GPS to find the neighbourhood and a keyword radio to find the exact street name.

---

## Lab 9: Query Rewriting On/Off — "Rewrite vague delivery notes"

**Config:** `QUERY_REWRITING_ENABLED` (default: `false`)
**What it controls:** Whether an LLM call rewrites the user query before vector search.
**Hypothesis:** Helps vague conversational queries; LLM adds context before search.

### Setup
1. Set `QUERY_REWRITING_ENABLED=false` in `.env`
2. Run Q1–Q3 plus a vague follow-up like "and what about its cost?"
3. Enable and repeat

### Results table (fill in as you run)
| Value | Retrieval | Faithfulness | Latency (ms) | Cost (€) | Notes |
|---|---|---|---|---|---|
| off | ___ | ___ | ___ | ___ | ___ |
| on | ___ | ___ | ___ | ___ | ___ |

### What we learned
Especially valuable in multi-agent: agents pass abbreviated handoffs to each other; rewriting them re-injects context the next agent lacks.

### 🫏 Donkey takeaway
Before the next donkey takes over, the smudged delivery note is rewritten in clear handwriting so the warehouse can find the parcel.

---

## Lab 10: Metadata Filtering — "Pre-sort the warehouse aisle"

**Config:** `METADATA_FILTERS` (default: none)
**What it controls:** Pre-filter chunks by metadata before vector search.
**Hypothesis:** Massive precision boost when applicable; pre-filters before vector search.

### Setup
1. Set `METADATA_FILTERS=` (none) in `.env`
2. Run the same 3 questions (Q1–Q3)
3. Try `METADATA_FILTERS=source=ai-gateway` for Q3
4. Try `METADATA_FILTERS=date>2025-01-01`

### Results table (fill in as you run)
| Value | Retrieval | Faithfulness | Latency (ms) | Cost (€) | Notes |
|---|---|---|---|---|---|
| none | ___ | ___ | ___ | ___ | ___ |
| source=ai-gateway | ___ | ___ | ___ | ___ | ___ |
| date>2025-01-01 | ___ | ___ | ___ | ___ | ___ |

### What we learned
Per-agent metadata filters are powerful: give the researcher web sources only, the summariser internal docs only, etc.

### 🫏 Donkey takeaway
Each donkey skips the whole warehouse and walks to its own aisle because the delivery note says "books, not groceries".

---

## Lab 11: Eval Thresholds — "How strict is the report card?"

**Config:** `EVAL_FAITHFULNESS_THRESHOLD` + `EVAL_KEYWORD_OVERLAP_PCT` (default: `0.5` / `0.5`)
**What it controls:** Pass/fail thresholds in the evaluator. Same answers, different verdicts.
**Hypothesis:** Strict thresholds expose multi-agent regressions that lax ones hide.

### Setup
1. Set strict values, run Q1–Q3, capture report card
2. Repeat for default + lax presets

### Results table (fill in as you run)
| Value | Retrieval | Faithfulness | Latency (ms) | Cost (€) | Notes |
|---|---|---|---|---|---|
| strict (0.8/0.7) | ___ | ___ | ___ | ___ | ___ |
| default (0.5/0.5) | ___ | ___ | ___ | ___ | ___ |
| lax (0.3/0.3) | ___ | ___ | ___ | ___ | ___ |

### What we learned
Calibrate before trusting. In multi-agent, lax thresholds let one bad agent's bad chunk poison every downstream score without firing alerts.

### 🫏 Donkey takeaway
The report card itself can be lenient or strict — the herd did the same trip, but a strict teacher fails the delivery for the smallest miss.

---

## Lab 12: Agent Count Sweep — "How many donkeys in the herd?"

**Config:** `AGENT_COUNT` (default: `2`)
**What it controls:** Number of specialist agents spawned per task (e.g., researcher, writer, critic, …).
**Hypothesis:** More agents = more specialisation + more orchestration overhead; quality plateaus then drops past a sweet spot.

### Setup
1. Set `AGENT_COUNT=1` in `.env` (single generalist agent)
2. Run the same 3 questions (Q1–Q3) and capture wall-clock + token totals
3. Repeat for each value below

### Results table (fill in as you run)
| Value | Retrieval | Faithfulness | Latency (ms) | Cost (€) | Notes |
|---|---|---|---|---|---|
| 1 (solo) | ___ | ___ | ___ | ___ | ___ |
| 2 (researcher + writer) | ___ | ___ | ___ | ___ | ___ |
| 4 (researcher + writer + critic + planner) | ___ | ___ | ___ | ___ | ___ |

### What we learned
Two agents almost always beat one (planner + executor), four often beats two on quality but costs ~3× tokens. Past four, returns diminish quickly. Pick the smallest team that hits your quality bar.

### 🫏 Donkey takeaway
One donkey delivers everything; four donkeys split the route and finish faster — but they spend half the day talking to each other instead of walking.

---

## Lab 13: Max Iterations Sweep — "How long can the agent loop?"

**Config:** `AGENT_MAX_ITERATIONS` (default: `10`)
**What it controls:** Hard cap on the agent's tool-use / think loop before it must answer.
**Hypothesis:** Too low = unfinished tasks; too high = pointless circling and runaway cost.

### Setup
1. Set `AGENT_MAX_ITERATIONS=3` in `.env`
2. Run the same 3 questions (Q1–Q3) and note any "max iterations exceeded" outcomes
3. Repeat for each value below

### Results table (fill in as you run)
| Value | Retrieval | Faithfulness | Latency (ms) | Cost (€) | Notes |
|---|---|---|---|---|---|
| 3 | ___ | ___ | ___ | ___ | ___ |
| 10 | ___ | ___ | ___ | ___ | ___ |
| 25 | ___ | ___ | ___ | ___ | ___ |

### What we learned
Cap iterations to the 95th-percentile of "successful" runs in your traces — high enough to finish real tasks, low enough that a stuck agent gets killed before burning tokens.

### 🫏 Donkey takeaway
A short leash makes the donkey give up before reaching the door; a long leash lets it wander the same corridor twenty times getting nowhere.
