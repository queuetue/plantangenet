# Quantum Domain Translation

This document is part of a Rosetta Stone for understanding the Plantangenet system. 

## Dust

Plantangenet’s Dust system defines a **closed, deterministic accounting universe** in which all value flows must be explicitly measured and conserved across each operational cycle. Though individual agents may model uncertainty, negotiation, or probabilistic strategies internally, the system itself acts as the measurement framework that resolves these uncertainties into **discrete, auditable ledger entries** by cycle end.

Dust is **pre-funded** at the start of each cycle, setting an absolute, known quantity of value that circulates among participants. This enforces a strict conservation law: no Dust is spontaneously created or destroyed mid-cycle. All transfers--whether for work execution, validation, coordination overhead, or policy-defined redistributions like tips or drift--are governed by **explicit policy rules**.

Agents can locally maintain **probabilistic or superpositional models** to forecast strategies or outcomes within **reference frames**. However, these models must reconcile to consistent, shared accounting when measured. The system guarantees that every unit of Dust is tracked and accounted for, ensuring transparency and auditability across diverse agent behaviors.

Policy defines **all permitted operations and costs**, including friction introduced by audit and coordination. It also governs redistribution mechanisms--planned behaviors like tipping, voluntary forfeitures, or timed expirations--that maintain system-wide conservation while encouraging strategic, emergent interactions.

Critically, the system’s design enforces that **all local uncertainty collapses** to a deterministic, auditable state on measurement. This supports creative agent diversity while maintaining a consistent, shared accounting reality.

> **Note:**
> This system is deliberately closed, deterministic, and policy-defined.
>
> * The total Dust supply per cycle is fixed and pre-funded.
> * All spending paths and redistributions are defined in policy.
> * Conservation is enforced: no untracked creation or loss.
> * Local probabilistic models must collapse to clear, auditable ledger entries.
> * Redistribution mechanisms (tips, drift, expiration) are specified and tracked.
> * Emergent strategies must reconcile to shared accounting rules.
> * Audit logs guarantee transparent, verifiable outcomes.

## Policy

**Policy** in Plantangenet is the **Lagrangian** of the system.

It defines the **allowed paths** through the state space--specifying **who** may perform **what** operations **under what conditions**.

Just as the Lagrangian encodes the *physics* of a system--its symmetries, conservation laws, and constraints--**policy** encodes the *rules of interaction*. It ensures:

* All **permitted operations** are declared.
* Costs for actions (including coordination friction) are **explicit**.
* All transitions are **reversible in audit**, even if they’re not reversible in execution.

Agents can propose **any** move in their local frame of reference, even modeling probabilistic or adversarial strategies. But **policy** enforces **consistency across the entire manifold**:

* Moves must respect permission constraints.
* Costs must match declared pricing.
* Identity, role, and context are always checked.

Policy is **modular** and **pluggable**--like swapping potential energy terms in your Hamiltonian. It can define:

* Simple, symmetric rules (RBAC).
* Context-aware, negotiated conditions (ABAC).
* Dynamically evolving trust boundaries.

And importantly, **policy evaluation** is enforced at runtime, ensuring that even the most exotic local agent behavior **collapses to a deterministic, auditable global ledger**.

**Note:**

> Policy is the *physics engine* of Plantangenet. It governs the **causal structure** of all allowed interactions, ensuring conservation and accountability across the system.

---

## Compositors

**Compositors** in Plantangenet are **measurement operators**.

They map **raw, high-dimensional system states** onto **policy-compliant, observer-specific outputs**.

Think of a **wavefunction**: the system's full state might encode everything--agent identities, actions, secrets, histories. But no observer is allowed to see *all* of it. Instead:

* **Compositors** define **which observables** are measured.
* They apply **policy-defined filters**: degradation, masking, summarization.
* They **collapse** complex, entangled states to *authorized views*.

Examples:

* Graph queries for social networks.
* SQL-style workloads for structured data.
* Framebuffer compositors for UI rendering.
* Machine-learning buffers producing compressed or redacted features.

Compositors **decouple** generation from presentation. They ensure **ephemeral snapshots** respect policy and **asynchronous updates** are efficient.

Their transformations are **declared and auditable**--just like measurement operators in physics must respect the theory’s symmetries and conservation laws.

**Note:**

> Compositors are the *measurement devices* of Plantangenet. They ensure that all shared views are **policy-shaped**, preserving trust and enforcing **causal consistency** in what is revealed.

---

## Squads

**Squads** are **localized systems** of interacting agents--like **bounded subsystems** in physics with their own **Hamiltonians**.

They are defined within **frames** that set:

* Who participates.
* What operations are allowed.
* How resources (Dust) are allocated and conserved.

Squads model **emergent phenomena**. Just as particles can form atoms, molecules, or macroscopic structures, **agents in squads** coordinate to produce collective outcomes.

Use cases include:

* **Tournaments** with negotiated rules and prize pools.
* **GAN training loops**, where agents model adversarial learning.
* **Systems modeling**, coordinating complex simulations.
* **Status dashboards**, merging multiple streams under a shared policy.
* **RPG sessions**, enforcing game logic while enabling player freedom.

Squads explicitly negotiate **coordination costs** and **budget constraints**. Their audit logs track **all causal interactions**, ensuring that no entangled dependency goes unmeasured.

Because they are **policy-defined**, Squads can be designed with **fine-grained causal models**--tracking which agent decisions influence which outputs, enforcing transparent attribution of cost and responsibility.

**Note:**

> Squads are **bounded causal systems** in Plantangenet. They let agents **coordinate, compete, or cooperate** while obeying the universal conservation laws of Dust.

---

## Membry

**Membry** is **persistent state** with **explicit decoherence controls**.

In quantum terms, it’s the **density matrix**: it tracks not just the current state but the **probabilities and uncertainties** that have been collapsed into **recorded, auditable history**.

Unlike naive, infinite storage, Membry enforces:

* **Declared retention policies** (lifespans, TTLs).
* **Costed writes and reads**, priced in Dust.
* **Degraded, redacted, or summarized storage** for privacy or economy.

You can think of Membry as enforcing **entropy accounting**. Nothing is free:

* Longer retention = higher cost.
* Higher resolution = higher cost.
* Secrecy (encryption) = higher cost.

Vaulted storage lets secrets be retained *with accountability*: even if content is hidden, the system tracks **commitments**--like publicly logging the hash of an encrypted message.

In effect, Membry ensures **all causal history** is preserved in a **policy-defined, costed way**, preventing hidden liabilities or uncontrolled information bloat.

**Note:**

> Membry is **auditable decoherence**. It turns ephemeral agent interactions into **persistent, policy-compliant records**, respecting conservation and privacy while ensuring accountability.

---

## Privacy & Delivery

**Privacy** in Plantangenet isn’t **absolute secrecy**. It’s **controlled, policy-defined information collapse**--just like measurement in quantum systems.

Agents may maintain **superpositional internal states**--plans, strategies, secrets. But when they communicate, they must **collapse those states** into **policy-compliant messages**.

Delivery channels enforce:

* **Policy-shaped views** (via Compositors).
* **Secrecy guarantees** priced in Dust.
* **Negotiated disclosures** based on roles and trust.

Examples:

* In **TicTacToe**, players can plan any move, but only the agreed state is revealed.
* In **Breakout**, internal physics may be hidden while scores and positions are shared.
* In **GAN training**, discriminators and generators negotiate what gradients or losses to reveal.

**Janet** acts as the **compiler**, ensuring plans respect **policy-defined transformations**.

**Meatball** is the **macro engine**, supporting **safe, auditable expansion** of generalized strategies into specific, executable forms.

Together, these ensure **causality is preserved**: no message can reveal information the policy forbids, no hidden channels can bypass accountability.

**Note:**

> Privacy & Delivery in Plantangenet enforce **information collapse** under policy. They guarantee that all communication is **intentional, priced, and consistent with the system’s causal model**, maintaining trust and preventing leakage.

## What's a Rosetta Stone?

The Rosetta Stone was an ancient artifact inscribed with the same text in multiple scripts, which enabled scholars to decode Egyptian hieroglyphs by comparing translations. (Wikipedia)

It shows the same system explained in different ways so that different kinds of people can understand it. Each version uses its own words and examples, but they all describe the same system: one with clear rules that makes sure nothing is lost or hidden. By reading these sections, everyone--designers, engineers, players, and organizers--can see how Dust works, how the rules are set, and how all the money or value is tracked and shared fairly.
