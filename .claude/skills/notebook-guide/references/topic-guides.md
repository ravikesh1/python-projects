# Topic Guides for AI Engineering Notebooks

What a good learning notebook covers for each core AI engineering topic:
the right scope for one sitting, the concepts that must land, the pitfall
worth demonstrating live, and good exercises. Suggested notebook series order:
prompting → embeddings → RAG → LangChain → agents → evals.

## Contents

- [Prompt engineering](#prompt-engineering)
- [Embeddings & vector search](#embeddings--vector-search)
- [RAG](#rag)
- [LangChain / LangGraph](#langchain--langgraph)
- [Agents & tool use](#agents--tool-use)
- [Evals](#evals)
- [General guidance](#general-guidance)

---

## Prompt engineering

**One-sitting scope:** system vs user messages, few-shot examples, structured
output (JSON), temperature.

**Must land:** the model only sees the text you send — every behavior change
comes from changing that text or the sampling params. Show the same task with
a weak prompt and a strong prompt side by side.

**Pitfall to demo:** asking for JSON without constraining it — show the chatty
non-JSON reply breaking `json.loads`, then fix with explicit schema
instructions and a retry-on-parse-failure loop.

**Good exercises:** convert a vague prompt into role + task + format + examples;
build a prompt that extracts structured fields from a messy paragraph.

## Embeddings & vector search

**One-sitting scope:** what an embedding is, cosine similarity, nearest-neighbor
search over a small corpus — all doable with numpy before touching a vector DB.

**Must land:** similarity in vector space ≈ similarity in meaning, and it's
just arrays — demystify before introducing any library. Plot a handful of
sentence embeddings in 2D (PCA) so "similar things cluster" is *seen*.

**Pitfall to demo:** comparing embeddings from two different models, or skipping
normalization — show the nonsense similarity scores.

**Good exercises:** build `top_k(query, corpus)` from scratch with numpy;
find the pair of sentences in a list that are most/least similar.

## RAG

**One-sitting scope:** chunk → embed → retrieve → stuff into prompt → generate.
Build it from scratch (lists + numpy) *before* any framework, so the framework
later reads as convenience, not magic.

**Must land:** RAG is two separate problems — retrieval quality and generation
quality — and bad answers are usually a *retrieval* failure. Print the
retrieved chunks before every generation so the reader develops the habit of
inspecting them.

**Pitfall to demo:** chunk size. Embed whole documents as single chunks, watch
retrieval return vaguely-related documents, then re-chunk into paragraphs and
watch the answer improve.

**Good exercises:** add a k parameter and find where more context stops
helping; ask a question the corpus can't answer and make the system say
"I don't know" instead of hallucinating.

## LangChain / LangGraph

**One-sitting scope:** one notebook for LCEL basics (prompt | model | parser,
runnables, streaming), a separate one for LangGraph (state, nodes, edges).

**Must land:** LangChain pieces are thin wrappers around things the reader
already built by hand in earlier notebooks — map each abstraction back
(`PromptTemplate` ≈ f-string, retriever ≈ their numpy `top_k`, chain ≈
function composition). Without that mapping the framework feels like magic
and debugging becomes guesswork.

**Pitfall to demo:** version drift — imports moving between `langchain`,
`langchain_core`, `langchain_community`. Pin versions in the setup cell and
show where to check the real current import path (the API reference, not blog
posts, which age badly here).

**Good exercises:** rebuild the from-scratch RAG notebook in ~15 lines of
LCEL; add streaming to an existing chain.

## Agents & tool use

**One-sitting scope:** the tool-use loop — model proposes a tool call, code
executes it, result goes back to the model, repeat until final answer. Build
the loop manually with 2 toy tools (calculator, mock search) before using any
agent framework.

**Must land:** an "agent" is just an LLM in a while-loop with tool results
fed back in. Print every iteration (tool chosen, args, result) so the loop is
transparent. This audience's SQL background makes a "query the database" tool
a great motivating example — connect to what they know.

**Pitfall to demo:** the infinite/flailing loop — give the model a task its
tools can't accomplish and show it spinning; fix with a max-iterations guard
and a "give up gracefully" instruction.

**Good exercises:** add a third tool and a task requiring two tools chained;
add a max-steps budget that forces a best-effort answer.

## Evals

**One-sitting scope:** why "it looks good" doesn't scale; build a tiny eval set
(10–20 cases), score exact-match/keyword first, then LLM-as-judge.

**Must land:** evals turn prompt tweaking from vibes into engineering — change
the prompt, rerun the eval, see the score move. Store cases as data (list of
dicts / JSONL), not code.

**Pitfall to demo:** LLM-as-judge inconsistency — run the same judge twice
with loose criteria, get different scores; fix with a rubric and structured
judge output.

**Good exercises:** write 5 eval cases for the RAG notebook including one
adversarial case; make a one-line prompt change and measure the delta.

## General guidance

- **From scratch before framework.** Every topic above that has a framework
  version (RAG, agents) should be built with plain Python first. The framework
  notebook then explicitly maps its abstractions to the hand-built parts.
- **Cheap first.** Structure notebooks so cells that cost money (API calls)
  are few and marked. Toy corpora, stub LLM functions, and numpy get most
  concepts across for free.
- **This reader's superpowers are Python, SQL, and classic ML.** Analogies to
  pandas/sklearn/SQL beat analogies to web dev. A `fit`/`predict` comparison
  or a SQL-join metaphor is worth 3 paragraphs.
- **Fast-moving libraries:** LangChain and friends change monthly. Verify
  current import paths against installed versions when writing cells, and
  prefer stable core APIs over the newest sugar.
