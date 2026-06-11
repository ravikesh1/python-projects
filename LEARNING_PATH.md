# AI Learning Path

A practical roadmap for getting better at AI, building on existing Python + backend skills
(this repo's MCP MySQL server is the starting point). Work through the phases roughly in
order, but learn math on demand rather than front-loading it.

**Golden rule:** build and publish one real project per phase. One shipped repo teaches
more than five courses.

---

## Phase 1 — Applied LLM Engineering (months 1–2)

The highest-leverage area to deepen first.

### LLM APIs

- [ ] Tool use / function calling — [Anthropic tool use docs](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview)
- [ ] Streaming responses
- [ ] Structured outputs (JSON mode / schemas)
- [ ] Prompt caching and token economics — [Prompt caching docs](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)

### Agents

- [ ] Read [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) (Anthropic)
- [ ] Understand planning loops, tool orchestration, error recovery
- [ ] Know when to use multi-agent vs. a single loop

### How LLMs work (intuition level)

- [ ] Watch [Karpathy — Intro to Large Language Models](https://www.youtube.com/watch?v=zjkBMFhNj_g)
- [ ] Read [The Illustrated Transformer](https://jalammar.github.io/illustrated-transformer/) (Jay Alammar)

### 🛠 Project

- [ ] **Build an agent that uses this repo's MCP MySQL server** to answer
      natural-language questions over a real database (NL → SQL → answer, with
      error recovery when queries fail)

---

## Phase 2 — RAG + ML Fundamentals (months 3–4)

### RAG (retrieval-augmented generation)

- [ ] Embeddings — what they are, how to generate them
- [ ] A vector store: [pgvector](https://github.com/pgvector/pgvector), [Qdrant](https://qdrant.tech/), or [FAISS](https://github.com/facebookresearch/faiss)
- [ ] Chunking strategies and their trade-offs
- [ ] Hybrid search (keyword + vector) and reranking
- [ ] Read [Anthropic — Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval)

### ML fundamentals (in parallel)

Pick one course:

- [ ] [fast.ai — Practical Deep Learning for Coders](https://course.fast.ai/) (code-first, best fit for a developer), **or**
- [ ] [Andrew Ng — Machine Learning Specialization](https://www.coursera.org/specializations/machine-learning-introduction) (gentler, more theory)

Core concepts to be able to explain:

- [ ] Train / validation / test splits
- [ ] Overfitting and regularization
- [ ] Loss functions and gradient descent
- [ ] Classification vs. regression metrics (precision/recall, F1, AUC)
- [ ] Hands-on [scikit-learn](https://scikit-learn.org/stable/getting_started.html) on real tabular data (SQL skills pair well here)

### 🛠 Project

- [ ] **RAG pipeline end-to-end**: ingest documents → embed → store → retrieve →
      generate → evaluate retrieval quality

---

## Phase 3 — Deep Learning Internals + Evaluation (months 5–6)

### PyTorch & transformers from scratch

- [ ] [Karpathy — Neural Networks: Zero to Hero](https://karpathy.ai/zero-to-hero.html)
      (build a GPT from scratch; attention stops being magic)
- [ ] PyTorch basics: tensors, autograd, training loops — [PyTorch tutorials](https://pytorch.org/tutorials/)
- [ ] Tokenization (BPE), embeddings, why context windows cost what they do

### Fine-tuning (do it once)

- [ ] LoRA / QLoRA with Hugging Face [`transformers`](https://huggingface.co/docs/transformers) + [`peft`](https://huggingface.co/docs/peft)
      on a small open model (Llama, Qwen)

### Evaluation — the professional's skill

- [ ] Write evals for LLM outputs: assertions, LLM-as-judge, regression suites
- [ ] Try [promptfoo](https://www.promptfoo.dev/) or plain pytest with recorded cases
- [ ] Add an eval suite to one of your earlier projects

### 🛠 Project

- [ ] **Fine-tune a small model** for a narrow task and compare it against
      prompting a frontier model — write up the results

---

## Math — just enough, on demand

Don't front-load months of math. Learn a concept when it blocks you.

- [ ] [3Blue1Brown — Essence of Linear Algebra](https://www.3blue1brown.com/topics/linear-algebra)
      (matrix multiplication, dot products, vector spaces — most of what you'll use)
- [ ] Derivatives + chain rule (that's backprop) — [3Blue1Brown — Essence of Calculus](https://www.3blue1brown.com/topics/calculus)
- [ ] Probability basics: distributions, Bayes' rule, expectation

---

## Production / MLOps — ongoing

These multiply the value of everything above; backend instincts transfer directly.

- [ ] Serve an LLM app behind [FastAPI](https://fastapi.tiangolo.com/) in Docker
- [ ] Logging and tracing LLM calls ([LangSmith](https://www.langchain.com/langsmith), OpenTelemetry)
- [ ] GPU basics: VRAM, batch size, quantization
- [ ] Cost monitoring for API-based apps

---

## Progress log

| Date | Milestone |
| ---- | --------- |
|      |           |
