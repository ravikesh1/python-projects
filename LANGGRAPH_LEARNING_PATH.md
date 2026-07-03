# LangGraph Learning Path: Initial to Advanced

A structured roadmap for learning [LangGraph](https://github.com/langchain-ai/langgraph), the library from the LangChain team for building stateful, multi-step, and multi-agent applications on top of LLMs.

## Prerequisites

Before starting, you should be comfortable with:

- **Python** — functions, classes, type hints (`TypedDict`, `Pydantic` models), async/await basics.
- **LangChain core concepts** — chat models, prompts, and simple chains (`prompt | llm`). LangGraph builds on these primitives rather than replacing them.
- **Basic graph/state-machine thinking** — nodes, edges, and the idea of state flowing through a system.

---

## Stage 1: Foundations

**Goal:** Understand why LangGraph exists and build your first graph.

- Understand the problem LangGraph solves: plain LangChain chains are directed acyclic graphs (DAGs) — great for linear pipelines, but they can't easily express loops, branching, or long-running stateful workflows (e.g. an agent that keeps calling tools until it's done).
- Install: `pip install langgraph`.
- Learn the core building blocks:
  - `StateGraph` — the graph object you build against a shared state schema.
  - **Nodes** — plain Python functions (or callables) that receive state and return updates to it.
  - **Edges** — connections that define what runs next.
  - **State schema** — typically a `TypedDict` or Pydantic model describing the shape of data passed between nodes.
- Build a minimal graph: define a state schema, add one or two nodes, wire them with `START` and `END`, compile the graph, and run it with `.invoke()`.
- Try `.stream()` to see intermediate state updates instead of only the final result.

**Checkpoint:** You can build and run a simple linear graph with 2-3 nodes.

---

## Stage 2: Control Flow

**Goal:** Learn what makes LangGraph different from a plain chain — cycles and branching.

- **Conditional edges** — use `add_conditional_edges` to route to different nodes based on the current state (e.g., a router function that inspects state and returns the name of the next node).
- **Loops/cycles** — build a graph where a node can route back to an earlier node (e.g., "keep retrying until a condition is met"). This is the key capability that distinguishes LangGraph from DAG-only chains.
- Understand `START` and `END` as special sentinel nodes marking entry and exit points.
- Practice: build a small "retry until valid" loop, or a simple router that sends input down different paths depending on content.

**Checkpoint:** You can build a graph with branching logic and at least one cycle.

---

## Stage 3: State Management

**Goal:** Understand how state is merged and updated across nodes.

- **Reducers** — functions that define how a node's returned update combines with existing state (e.g., `add_messages` appends to a list instead of overwriting it).
- **Multiple state channels** — a state schema can have several fields, each with its own reducer/merge behavior.
- **Partial updates** — nodes only need to return the keys they change; the rest of the state is preserved.
- **Typed state** — use Pydantic models for validation, or `TypedDict` for lighter-weight typing.
- Message-passing patterns — the common `messages: Annotated[list, add_messages]` pattern used for chat-style agents.

**Checkpoint:** You understand how to design a state schema for a multi-turn conversational graph.

---

## Stage 4: Tool-Using Agents

**Goal:** Build an agent that reasons and calls tools (the classic ReAct pattern).

- Bind tools to a chat model with `.bind_tools(...)`.
- Build an "agent" node that calls the LLM and a `ToolNode` that executes any tool calls the LLM requested.
- Wire a conditional edge that loops between the agent node and the tool node until the LLM responds without further tool calls.
- Handle tool errors gracefully (e.g., returning error messages back into state so the LLM can retry or adjust).
- Explore LangGraph's prebuilt `create_react_agent` helper to see a reference implementation before rolling your own.

**Checkpoint:** You can build a working tool-calling agent loop from scratch, and explain what the prebuilt helper does under the hood.

---

## Stage 5: Persistence & Memory

**Goal:** Make graphs stateful across runs, not just within a single invocation.

- **Checkpointers** — pluggable persistence backends (`MemorySaver` for in-process/dev use; SQLite/Postgres checkpointers for durable storage).
- **Threads** — each conversation/session is identified by a `thread_id`, letting the graph resume prior state.
- **Time travel** — replay or fork execution from an earlier checkpoint to debug or explore alternate paths.
- Practice: add a checkpointer to your Stage 4 agent so it remembers conversation history across multiple `.invoke()` calls with the same `thread_id`.

**Checkpoint:** You can build a chat agent that persists memory across separate invocations.

---

## Stage 6: Human-in-the-Loop

**Goal:** Add checkpoints where a human can inspect, approve, or edit state before execution continues.

- **Interrupts** — pause execution before or after specific nodes (`interrupt_before` / `interrupt_after`, or the newer `interrupt()` function).
- Inspect and edit the graph's state while paused, then resume execution.
- The `Command` primitive — used to resume a graph with updated state or a specific routing decision after an interrupt.
- Practice: build an agent that pauses before executing a "risky" tool (e.g., sending an email or writing to a database) and waits for approval.

**Checkpoint:** You can build an approval workflow where a human gates a sensitive action.

---

## Stage 7: Multi-Agent Systems

**Goal:** Compose multiple graphs/agents into larger systems.

- **Subgraphs** — a compiled graph can be used as a node within another graph.
- **Supervisor pattern** — a coordinating agent routes tasks to specialized worker agents based on the request.
- **Agent handoffs** — patterns for one agent to explicitly transfer control (and relevant context) to another.
- Shared vs. isolated state — decide whether sub-agents see the full parent state or only a scoped subset.
- Practice: build a supervisor that routes between two or three specialized agents (e.g., a "research" agent and a "writer" agent).

**Checkpoint:** You can design and build a small multi-agent system with a clear coordination pattern.

---

## Stage 8: Production & Advanced Topics

**Goal:** Prepare graphs for real-world deployment and operation.

- **Streaming modes** — `values` (full state after each step), `updates` (only the diff), and `messages` (token-level streaming from LLM calls).
- **Async execution** — use `ainvoke`/`astream` for concurrent, non-blocking workloads.
- **Parallel node execution & map-reduce patterns** — fan out work across multiple nodes and merge results back into state.
- **Observability** — integrate with LangSmith (or similar tracing tools) to inspect graph execution, debug failures, and monitor latency/cost.
- **Testing** — write unit tests for individual nodes and integration tests for full graph runs, including deterministic tests for conditional routing.
- **Deployment** — understand the basics of LangGraph Platform (or self-hosting a compiled graph behind an API) for serving graphs in production.

**Checkpoint:** You can reason about performance, observability, and testing strategy for a production LangGraph application.

---

## Suggested Projects (mapped to stages)

| Project | Stages exercised |
|---|---|
| Simple Q&A bot over a single document | 1-2 |
| Multi-step research assistant with retry loops | 2-3 |
| Tool-using agent (calculator, web search, code execution) | 3-4 |
| Persistent chat assistant with long-term memory | 5 |
| Agent with human approval before sending external messages | 6 |
| Multi-agent customer support system (router + specialists) | 7 |
| Production-ready agent service with tracing and streaming API | 8 |

---

## Reference Links

- Official docs: https://langchain-ai.github.io/langgraph/
- GitHub repository: https://github.com/langchain-ai/langgraph
- LangChain Academy (free course, includes a LangGraph module): https://academy.langchain.com/
