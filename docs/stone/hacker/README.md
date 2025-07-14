# Hacker Translation

This document is part of a Rosetta Stone for understanding the Plantangenet system.

>A personal note from Queuetue:  If this "stone" speaks to you, please, I can use your help.  (continued below)

This is the *hacking* stone.  If you didn't already look at the code, you should probably start from another stone, like the (Neutral)[../neutral/README.md] one or the (index)[../README.md]

If you are where you should be then, please read the Neutral stone first.  This one assumes that one is a cakewalk for you.

## Dust

> TL;DR: Dust is a programmable economic layer for coordinating distributed systems at cost. It makes every interaction explicit, metered, auditable, and scriptable. No magic. No hidden costs. Just rules you can read, hack, and enforce, generate, infer, or etl on.

Plantangenet’s Dust system is **a fully accounted, programmable transaction layer** for distributed work.

It’s there to make *every* operation--no matter how asynchronous, parallel, or weird--**explicitly metered** and **auditable**.

This isn’t Kubernetes pretending to be “cloud-native.” It’s closer to **bare-metal economics for coordination itself**.

---

## Designed for People Who Want to Know How It Works

Dust isn’t some vague points system or blockchain hype. It’s a **closed, pre-funded pool** declared up front for each cycle:

* Every participant can see the budget.
* No magic inflation.
* No "free" unpaid coordination that gets eaten by someone else.

You can think of it like a **bounded gas tank** for your entire distributed workload:

* Every RPC, DB write, GPU batch, message queue push has a cost.
* Every audit, every validator step, every consensus round burns fuel.
* All of it is tracked.

---

## Compositors and Squads Actually Produce Output

Plantangenet doesn’t just log transactions--it **orchestrates work**:

* **Compositors** are pluggable, programmable pipelines for transforming structured state into shareable outputs. Think rendering pipelines, ETL flows, live dashboards.
* They can degrade, mask, summarize, or encrypt on the fly based on **policy**.
* Compositors are how the system takes raw agent actions and produces *pixels*, *JSON*, *binaries*, *archives*--anything.

**Squads** are like dynamic worker pools or service graphs:

* Defined in policy.
* Can be scaled up or down by budget.
* Bound to Dust limits.
* Can negotiate coordination overhead explicitly.

You're not just deploying YAML at Kubernetes. You're composing **live, auditable economic contracts** for cooperative workloads.

---

## Hackable, Auditable, and Fully Scriptable

Dust is enforced at runtime, but the *rules* are **declared in policy**:

* Who can do what.
* What it costs.
* How redistribution works (fees, drift, tips).
* How audit logs are recorded.

You can:

* Define roles with Python functions or JS snippets to evaluate conditions.
* Build macros to automate plan generation.
* Integrate with CI/CD to lint policy.
* Spin up ephemeral squads to run ML experiments with bounded budgets.
* Instrument it all with audit logs you can parse.

We built **Meatball** to handle macro-expansion safely. We built **Janet** to manage plan rendering, validation, and execution as code.

If you want to deploy a plan to stand up 10K simulations with ephemeral Redis and NATS, with precise budgeted coordination, that’s what this system is for.

---

## Optimizations Are Legit Work

Dust isn’t there to *stop* you hacking--it’s there to make **hacks count**.

* Reduce coordination overhead? You save Dust for real work.
* Batch operations? You get more done per cycle.
* Simplify policy? You reduce validation cost.
* Spot waste? That’s earned margin.

Plantangenet is designed for **emergent optimizations** that show up in the ledger. If you’re the person who makes the system cheaper to run, you *actually* get the credit.

---

## Local Experiments, Global Accounting

You can model **probabilistic**, **stochastic**, or **game-theoretic** strategies in your agents:

* Multi-armed bandits? Sure.
* Evolutionary strategies? Sure.
* Federated ML? That too.

But **at the end of the cycle**:

* All Dust is reconciled.
* All transfers are logged.
* Conservation is enforced.

Your local uncertainty collapses into a **deterministic global ledger**.

It’s like running Monte Carlo on your own time--but paying for actual compute and coordination as it happens.

---

## Bring Your Own Language

Plantangenet doesn’t care if you’re:

* Running Python batch jobs.
* Spinning Go microservices.
* Deploying Rust-compiled WASM agents.
* Or driving a React UI that lets parties inspect the ledger.

We’ve designed for:

* Pluggable macro engines (Python, JS, Go templates, etc.).
* Extensible pipelines.
* Minimal JSON schemas for policy.
* Low-level access to audit logs.

If you want to get closer to the metal than Kubernetes will let you--**here’s your playground**.

---

## Invitation to Hack

Dust exists *because* we assume you’ll try to:

* Game it.
* Automate it.
* Exploit it.
* Outperform everyone else.

And we want you to.

But you can’t do it **for free** or **in secret**. You have to pay the coordination cost. You have to show your work. You have to balance the ledger.

That’s not a punishment. It’s the **terms of service for actual collaboration**.

If you want a system where your cleverness matters and gets paid--welcome.

---

**Note:**
This system is designed to be transparent, programmable, and auditable.

> * The Dust supply is pre-funded and fixed per cycle.
> * All costs are declared in policy.
> * Conservation is enforced--no hidden inflation or loss.
> * Macro expansion and plan execution are scriptable and safe.
> * Compositors and Squads are policy-defined, auditable workers.
> * Optimization, batching, and simplification are rewarded with real margin.
> * Audit logs mean everyone can see who did what--and why.

---

> A personal note from Queuetue:  If this "stone" speaks to you, please, I can use your help! Being able to discuss this with other people is VERY difficult, because first you need to teach them how to build a self-contained universe, and I might veer into ... caching debates, or aircraft statistics, or old stories. :)  

> Having people around who think about dna from the inside out, get why a packet would be able to decrypt itself, or question whether the planck constant indicates a *heck* of a lot more than we let on ... I'd like to chat on the reg, as difficult as that is for me and you.

> If you have ideas how to make money doing this, even more so.

Excellent--let’s write those **Hacker Translation** sections to match your voice so far: direct, technical, respectful of the reader's skill.

We’ll **lean on** the *Neutral Translation* content for accuracy, but *rephrase* for a tinkerer who wants to *get their hands dirty*, with a bias toward understanding underlying mechanisms.

---

# Policy

Plantangenet’s **policy system** is where you **declare your universe’s rules**--and enforce them *at runtime*.

Policies aren’t just documentation. They’re **executed logic** that controls **who** can do **what**, **under which conditions**--all enforced *field by field*, *action by action*, *agent by agent*.

Think of policy as the **bytecode of trust**:

* Want role-based access? Easy.
* Need context-aware permissions (time of day, budget, request origin)? Done.
* Need per-field masking, write barriers, read degradation? That’s built-in.

Policies are **modular and pluggable**. You can define rules in JSON or render them from templates. The system lets you write condition checks in **Python** or **JavaScript**--so you can actually express complex logic, not just "role X can read Y".

All of this is **auditable**. Every action gets evaluated, logged, and validated against the policy in real time. That means you can *prove*:

* Who called what.
* What data they saw.
* Which rule let them do it.

This isn’t Kubernetes RBAC. This is **programmable guardrails for trust**, designed to let you model **negotiated, federated, cross-org systems**--where agents might be *competitive*, *adversarial*, or *just misconfigured*.

You get to decide **how much** trust to allow, **where** to enforce it, and **how** to make it explicit in logs.

---

# Compositors

Compositors are Plantangenet’s **view engines**--but think bigger.

They’re programmable **pipelines** that take messy, high-dimensional, time-indexed data and turn it into **policy-compliant output**.

You want to generate a **SQL query result**, a **graph traversal**, a **framebuffer image**, or a **structured ML batch**? You define a **compositor** for that.

Compositors work with **axes**--essentially dimensions you want to slice by. For example:

* Time windows
* User IDs
* Geographic partitions
* Resolution layers

Need to **summarize**? The compositor degrades precision.
Need to **mask secrets**? The compositor enforces policy.
Need to **batch for ML training**? The compositor produces well-shaped tensors.
Need to **fill a UI framebuffer**? The compositor streams precisely what’s allowed.

They can support **graphs** for social networks, **SQL workloads** for ad hoc querying, **axes-frame compositors** for multidimensional time series, or **framebuffers** for real-time game UIs or dashboards.

**MLBuffers**? Yep. You can build policy-aware pipelines that produce training batches while respecting retention policies, data masking, and participant permissions.

All transformations are **declared**. All costs are **metered**. All outputs are **audited**.

For a hacker, that means **you can prototype and deploy ETL pipelines**, **data serving layers**, **live dashboards**, or **ML workloads**--without sacrificing **auditability** or **privacy compliance**.

No hand-waving about trust. Just code, policy, and Dust flows you can inspect.

---

# Squads

Squads are **composable, dynamic groups of agents**. They’re your **orchestration layer** for real work.

Think of a Squad as a **policy-bound actor system** that actually meters Dust costs for coordination:

* It knows who’s in it.
* It knows what they’re allowed to do.
* It knows the budget for coordination overhead.

You don’t just "run jobs"--you *negotiate coordination*.

Example use cases:

* **Tournaments**: Have players submit states, adjudicate moves, and pay for refereeing.
* **GAN Training**: Have generator and discriminator squads negotiate updates, pay for coordination, log outcomes.
* **Systems Modeling**: Have agents simulate different parts of a physical or economic system, synchronizing states with explicit budgeted communication.
* **System Status**: Aggregate microservice health, logs, and metrics into live dashboards--again, paying for coordination.
* **RPGs**: Multiplayer state machines with rule-bound adjudication, agent turns, persistence.

You define Squads in **policy**. They can be **ephemeral** (for a quick batch job) or **persistent** (long-running simulation). They enforce declared **coordination costs**:

* Every message push burns Dust.
* Every validation step is charged.
* Every audit trail is logged.

Squads are how you *pay for* and *trace* distributed coordination, turning spaghetti service meshes into **accounted economic contracts**.

# Membry

**Membry** is Plantangenet’s **memory layer**--but it’s designed for people who understand storage isn’t free.

In many systems, persistence is just "write and forget." Hidden costs, unbounded growth, accidental leaks.

Membry says:

> “You want to remember? Declare it. Pay for it. Track it.”

It doesn’t *store* your data for you. It **wraps** your storage with **policy enforcement**:

* All writes require permission.
* Lifespans (TTL) are declared and enforced.
* Costs in Dust reflect storage space, duration, secrecy.
* Reads can be filtered, degraded, or masked on policy rules.

You want secret storage? Great. Encrypt it. Pay Dust for management, rotation, and retention. Membry logs the commitment (not the secret) so it’s **accountable**.

Need ephemeral cache? Cheaper.
Long-term audit logs? Pay for the capacity and lifecycle.
Differential retention policies? Declarable.

For hackers, this means you get **storage with economic contracts baked in**.

You can script policies that decide:

* Who can read/write.
* How data expires or fades.
* How much detail is retained.

It’s not a DBMS. It’s the **control plane** for *making any DB behave like a cooperative, policy-bound store*.

# Privacy & Delivery

Plantangenet treats **privacy** not as absolute encryption, but as **declared, metered, policy-enforced sharing**.

That means **transformations**:

* Degrade resolution.
* Mask fields.
* Summarize.
* Aggregate.

You decide **what** to share, **how much**, and **to whom**.

**Compositors** enforce these transformations. For example:

* A **TicTacToe** compositor only exposes current board state and allowed moves.
* A **Breakout** compositor summarizes ball and paddle states but hides internal physics params.
* A graph compositor might limit visibility to local neighborhoods or aggregate edges.

This is implemented with **policy** that declares **who gets which view**.

**Janet** is your **plan renderer** and executor:

* It takes your policy, your roles, your macro templates, and produces **validated plans**.
* You can test, lint, version, and CI/CD them.

**Meatball** is your **macro-expansion engine**:

* Build re-usable plan templates with conditionals and loops.
* Generate dynamic plans at runtime.
* Ensure expansions are safe and predictable.

For delivery, **Comdecs** manage *how* these transformed views get to users or systems:

* Push to UIs as framebuffers.
* Stream to APIs with bounded detail.
* Log to audit systems for later verification.

The philosophy is:

> **Privacy** isn’t just encryption. It’s policy-shaped, negotiated, metered sharing.

You don’t rely on secrecy alone. You rely on **declared limits**, **priced retention**, and **auditable sharing**.

Hackers can script, test, and optimize these pipelines, ensuring **users only see what they’re allowed, at the resolution they pay for**, while keeping system integrity intact.

## What's a Rosetta Stone?

The Rosetta Stone was an ancient artifact inscribed with the same text in multiple scripts, which enabled scholars to decode Egyptian hieroglyphs by comparing translations. (Wikipedia)

This is **your** translation:

*The one that says: "You want to see the source? You want to see how it really works? You want to fork it? Go ahead."*

Because here, **the ledger is the code**. And you get to write your part of it.

