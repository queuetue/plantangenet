# Neutral Translation

This document is part of a Rosetta Stone for understanding the Plantangenet system. 

## Frame

A **frame** in Plantangenet defines a **bounded environment** for interaction, contribution, and value exchange. It specifies **who may act**, **what is allowed**, **how costs are priced**, and **how all results are reconciled**.

Frames set the **policy** that governs permissions, costs, redistribution, and resolution rules. They ensure that **all work and transfers of Dust happen within a declared, auditable scope**, preventing untracked or unfair outcomes.

Frames can be **short-lived** or **long-running**, with duration and trust boundaries defined by policy. They serve as **contracts of interaction**, providing transparency, predictability, and accountability for all participants.

**Note:**

> * Frames enforce **policy-defined rules**.
> * All Dust flows are **tracked and reconciled** within the frame.
> * Duration and resolution are **declared**, supporting both brief and extended collaborations.

## Policy

A **policy** in Plantangenet defines the **rules** for **who** can do **what**, **on what**, and **under what conditions** within a frame. Policies enforce **trust boundaries** by specifying permissions, costs, and restrictions in clear, auditable terms.

**Policies are active and enforced**: they are not just written agreements but runtime gatekeepers. Every action an agent takes--such as reading or writing a field--can be checked against the policy. This ensures that **all operations are subject to identity-aware, context-sensitive, and per-field control.**

Policies support **fine-grained access control**, allowing systems to balance **privacy**, **autonomy**, and **collaboration**. They enable roles, conditions, and context to shape what is allowed:

* **Roles** group permissions for easy management.
* **Identities** define the actors making requests.
* **Conditions** refine access decisions based on context, such as resolution level or time.
* **Statements** specify which roles may perform which actions on which resources.

Plantangenet’s policy system is **modular and pluggable**. It can be adapted for simple or complex use cases--from basic role-based access control to advanced, negotiated, context-sensitive models. It also supports **persistence and auditability**, ensuring that all policy decisions can be tracked and verified.

By embedding policy evaluation in every operation, Plantangenet guarantees that **all access and modification is explicitly authorized, recorded, and explainable**, supporting reliable, federated collaboration even among untrusted parties.

**Note:**

> * Policies define **who**, **what**, and **how** for all interactions.
> * All actions are **evaluated at runtime** against policy rules.
> * Supports **per-field**, **per-action**, and **per-identity** access control.
> * Fully **auditable** and **transparent**, ensuring trust in collaborative systems.
> * Enables both **simple role-based models** and **complex, negotiated access** with context-aware conditions.

## Session

A **Session** in Plantangenet is the **boundary** around a group of **agents** and their activities. It defines **who is present**, **what they are allowed to do**, and **how they share resources** within a controlled, policy-defined context.

Sessions act as **trust and coordination hubs**. They manage **identities**, **roles**, and **policies** that specify permissions and costs for all agent actions. By enforcing these shared rules, Sessions ensure that **all interactions remain visible, consistent, and accountable**.

Within a Session:

* **Agents** are attached and managed over their lifecycle.
* **Policies** govern what agents can do and what data they can access.
* **Cursors** define regions of interest or focus, shaping what data is retrieved or processed.
* **Compositors** may be queried to produce filtered, policy-compliant views of data.
* **Dust budgets** are enforced and tracked, ensuring fair allocation of costs and resources.

Sessions also enable **persistence**. They can save and restore state, supporting robust operation across disconnections or restarts while maintaining **auditability** and **policy compliance**.

Ultimately, a Session is the **trusted scope** where participants negotiate roles and permissions, coordinate their actions, and share data responsibly. It enables **collaboration** among independent agents while enforcing **clear boundaries**, **consistent policies**, and **transparent accounting**.

**Note:**

> * Sessions define the **boundary of trust** for a group of agents.
> * They enforce **policy-defined permissions** and **resource access**.
> * All **Dust spending** and **data sharing** are **tracked and auditable**.
> * Support for **lifecycle**, **persistence**, and **negotiated roles** ensures reliable, secure collaboration.


## Agent

An **agent** is any participant in a Plantangenet frame. Agents act by **requesting operations** and **spending Dust** under the frame’s policy-defined rules. They can represent individuals, services, automated processes, or institutions.

Agents may pursue **competitive, cooperative, or adversarial** strategies. The system does not assume they will behave honestly--it enforces **transparency, accounting, and conservation** so all actions remain fair and visible.

Plantangenet supports different types of agents for varying complexity:

* **Basic Agents** – Act individually, spending and earning Dust.
* **Omnis** – Advanced agents with state, persistence, and detailed audit trails.
* **Squads** – Coordinated groups of agents applying shared rules to produce collective outcomes.

**Note:**

> * Agents operate **within frame-defined policy**.
> * All Dust use is **accounted and auditable**.
> * Supports diverse strategies while enforcing **fairness and integrity**.

## Squad

A **squad** organizes and coordinates **groups of agents or omnis** to achieve shared goals within a frame. Squads apply **policy-defined rules** that structure collaboration, manage contributions, and ensure fair distribution of Dust.

Squads can **compose** outputs from many agents, applying declared **transformations** and **validation steps** to produce reliable, auditable results. By coordinating multiple participants, squads support **complex workflows** while maintaining the system’s **conservation, transparency, and accountability** guarantees.

**Note:**

> * Squads enforce **shared rules** for collective work.
> * Outputs are **policy-defined and auditable**.
> * Support structured cooperation while preserving **bounded, visible Dust flows**.

## Dust

Plantangenet’s Dust system implements a **closed, policy-defined unit-of-account model** to allocate and track value within a cooperative or competitive environment. It is designed to ensure **strict conservation of value** per operational cycle, with complete auditability of all flows.

At its core, Dust is **pre-funded**: before any cycle of work or interaction begins, participants collectively or individually fund the Dust budget for that cycle. This upfront commitment defines the **total quantity of Dust** available, enforcing a known, bounded budget. There is no creation or destruction of Dust mid-cycle; all changes in allocation reflect policy-defined transfers within that closed system.

During a cycle, participants **spend** Dust to request or perform actions. Each action exists within a **policy-defined reference frame** that specifies allowed operations and their costs. Costs are not only for direct work but also include **coordination, validation, audit overhead**, and system-level friction. These are explicitly priced to reflect the real cost of maintaining secure, fair, and verifiable interactions.

At the end of each cycle, **all Dust must be accounted for**. Every unit either ends up in participant holdings, is spent on work, is routed to fees or overhead, or is explicitly allocated to reserves or system pools. There is no untracked surplus or deficit. This ensures full transparency and enables auditability, supporting trust among participants.

The system **supports policy-defined mechanisms for redistribution**. Participants may voluntarily direct part of their allocations--tipping, donations, or forfeitures--into system reserves or shared goals. These are planned behaviors, not leaks, and they maintain conservation because all flows are tracked and reconciled. Policy can enforce expirations, drifts, or specific redistribution rules to prevent hoarding or stagnation.

Plantangenet’s design explicitly encourages **optimization**. Participants can reduce their effective costs by designing workflows that lower coordination or audit overhead, enabling more work per unit of Dust. Such savings remain within the system, increasing future cycle value or reducing participant costs.

Ultimately, Dust provides a **framework** for defining, pricing, and verifying value exchange in any collaborative system. It is domain-agnostic but requires **careful policy design** to specify costs, distribution rules, allowed interactions, and conservation mechanisms. By enforcing these rules consistently, the system ensures that **all value is transparent, conserved, and fairly allocated**.

> **Note:**
> This implementation is deliberately closed, deterministic, and auditable.
>
> * The total Dust supply per cycle is pre-funded and fixed.
> * All spending paths are defined in policy.
> * Conservation is enforced: no untracked loss or creation.
> * Costs include direct work and system overhead.
> * Redistribution (tips, drift, expiration) is policy-specified and fully tracked.
> * Emergent optimizations must still obey conservation and auditability.
> * Audit logs enable transparent verification of all flows.

## Profit

Plantangenet’s Dust system supports **policy-defined profit models** designed to ensure that value exchange remains **fair, transparent, and sustainable** within the closed accounting environment.

**Profit**, in this context, is not an uncontrolled surplus but a **planned, trackable outcome** of providing value within the system’s rules. Agents, service providers, and participants can earn profit by delivering work or services more efficiently than baseline costs, charging clients for convenience, quality, or bundled offerings.

### Policy-Defined Pricing

Within each operational cycle, **participants can set prices** for their work or services, subject to **policy-defined reference frames**. These frames specify:

* **Permitted operations** and their costs
* **Minimum or maximum price bounds** (if enforced)
* **Redistribution obligations** (such as fees, taxes, or community contributions)

This allows participants to **compete, differentiate, and optimize**, while ensuring that all pricing remains **transparent** and **auditable**.

**Profit Through Efficiency**

The Dust model explicitly encourages **optimization**. Participants who reduce coordination overhead, streamline validation, or lower system-level friction can offer competitive prices **or** maintain higher margins while charging standard rates.

Examples include:

* **Batching work** to lower per-unit overhead
* **Reducing coordination steps** through better design
* **Minimizing validation costs** with reliable practices
* **Bundling services** to deliver convenience

Because Dust flows are fully tracked, these profits are **visible** and **accountable**.

**Tracking Profit and Cost Discrepancies**

Every transaction in the Dust system records:

* **Price charged to the client**
* **Actual system cost incurred**
* **Resulting profit or loss**

This ensures that profits are not **hidden leaks** but **auditable, policy-compliant outcomes**. The system’s accounting guarantees **conservation**: profit for one participant corresponds to costs and payments accounted for elsewhere.

**Redistribution and Profit Sharing**

Policies can also define **redistribution mechanisms** for profit:

* **Tipping and Donations**: Voluntary transfers to other participants or system reserves
* **Fees or Taxes**: Automatic system-defined redistributions
* **Shared Pools**: Community funding or maintenance reserves

Such redistributions are **declared in advance**, fully tracked, and **auditable** to maintain fairness while supporting shared goals.

**Supporting Sustainable Incentives**

By making profits **explicit, planned, and traceable**, the Dust system ensures that participants have real incentives to improve processes, reduce waste, and deliver better experiences. At the same time, it prevents **unbounded extraction** or **hidden exploitation** that would undermine trust.

This approach enables **competitive and cooperative dynamics** to emerge without sacrificing **transparency, conservation, or fairness**.

**Note:**

> * Profit in Dust is **policy-defined** and **auditable**.
> * Pricing is **participant-driven** but constrained by system policy.
> * Cost discrepancies (profit or loss) are **tracked** and **reconciled**.
> * Redistribution mechanisms ensure **fairness** and **community sustainability**.
> * Optimization is **rewarded** but must respect **conservation** and **auditability**.

Excellent guide. Let’s fit **Membry** into that structure--short, clear paragraphs, a single bullet list, and a concluding **Note** box in the same style:

## Membry

**Membry** is Plantangenet’s **policy-aware memory layer**, designed to ensure that **all storage is intentional, bounded, and accountable**. It doesn’t ban keeping data forever--you can still export a JPEG or save receipts--but it ensures that *within the system*, persistence is always **declared, priced, and auditable**.

At its core, Membry is **not a store** but a **control layer** that wraps existing storage. It enforces **policy-defined rules** for writing, retaining, and retrieving data, applying costs in **Dust** that reflect capacity, duration, resolution, and secrecy. This turns memory from cheap, hidden accumulation into **negotiated, transparent resource use**.

All persistence is **policy-enforced**:

* **Writes** are checked for permission, lifespan (TTL), and secrecy level.
* **Reads** can be filtered or degraded based on access rights.
* **Retention** includes expiry, fading, or summarization over time.

Vaulted storage supports **secrecy with accountability**, allowing encrypted data to remain hidden for a paid duration, while logging commitments publicly. Users pay **Dust** for encryption strength, duration, and management, making secrecy explicit and auditable.

Because all Dust flows are **tracked and reconciled**, participants cannot store or share beyond policy-defined limits without paying for it. This ensures **fairness**, **privacy**, and **transparent resource allocation** while supporting both ephemeral and durable use cases.

**Note:**

> * Memory is **allowed and encouraged**, but must be **declared and priced**.
> * All persistence costs **Dust**, enforcing conservation and accountability.
> * Policy defines **what is stored, for how long, and at what cost**.
> * Audit logs ensure **transparency** while supporting **negotiated privacy**.

## Trust

Plantangenet’s Dust system is designed to support **trustworthy collaboration** in shared environments where participants may not know or fully trust one another. Trust in this context does not mean blind faith in individual intentions, but **confidence in the system’s ability to enforce declared rules, ensure transparency, and prevent hidden manipulation**.

Dust is **conserved and auditable by design**. The system enforces that **all value transfers are pre-funded, policy-defined, and reconciled**, making it impossible to create or lose Dust outside of agreed paths. This prevents untracked creation, silent extraction, or accumulation through loopholes.

To maintain **system integrity**, Plantangenet explicitly acknowledges that participants (agents) may act in self-interested, adversarial, or unpredictable ways. The system itself remains **deterministic and transparent**, enforcing:

* **Policy-defined permissions and costs** for all operations
* **Full accounting** of every Dust transfer
* **Audit logs** enabling verification of all flows

Plantangenet encourages **optimization and competition** while enforcing **fairness and conservation**. Profit, redistribution, and pricing strategies are allowed but must remain **policy-compliant and fully tracked**. By requiring that all costs and redistributions be declared and reconciled, the system ensures that **no participant can gain at others’ unaccounted expense**.

Ultimately, Plantangenet’s approach to trust is **structural**. Instead of assuming participants will behave well, it ensures that **all interactions remain visible, bounded by policy, and resistant to abuse**, providing a reliable foundation for shared work, negotiation, and value exchange.

**Note:**

> * Trust in Dust comes from **enforced rules**, not assumed good intentions.
> * All value flows are **pre-funded, conserved, and auditable**.
> * Policy defines **who may do what, at what cost**, and **how redistribution occurs**.
> * Audit logs ensure **transparency and accountability**.
> * Optimization and competition are **welcomed**, but **exploitation is prevented** by design.

## Risk

Plantangenet’s Dust system is designed to **welcome risk-taking** while ensuring that **all risk is deliberate, bounded, and accountable**. Rather than banning experimentation or competitive strategies, the system enforces that **all participants know what is at stake, where it came from, and where it goes when it is lost**.

At its core, Dust is **pre-funded** for each operational cycle. Participants, sponsors, or institutions must commit resources up front, defining the **total available budget**. This requirement prevents unplanned or limitless losses by ensuring **all risk is declared in advance**. Participants cannot spend Dust they do not have or promise work beyond the cycle’s capacity.

All spending paths are **policy-defined**. Risk-taking activities--bets, high-stakes operations, speculative strategies--must specify:

* **Permitted operations and costs**
* **Potential redistributions or forfeitures**
* **Resolution and reconciliation rules**

This makes **the risk itself transparent**. Participants and observers can see **how much was risked**, **who accepted it**, and **where forfeited value is redistributed**--whether into system reserves, other participants’ accounts, or shared goals.

Because Dust is **conserved and auditable**, losses for one participant become **tracked gains or reserves elsewhere**. Nothing disappears or appears without policy-defined justification. This ensures fairness even in competitive or adversarial contexts, maintaining trust in the integrity of the shared system.

Ultimately, Plantangenet does not forbid ambitious or risky behavior. Instead, it insists on **clarity and accountability**, allowing participants to innovate, compete, and experiment while **protecting the system and its users from hidden, unbounded, or unfair losses**.

**Note:**

> * Risk is **allowed and encouraged**, but must be **declared and bounded**.
> * All Dust flows are **pre-funded and conserved**.
> * Policy defines **where forfeited value goes**, supporting fairness and transparency.
> * Audit logs ensure **every loss and gain is accounted for**.
> * The system enables **experimentation** without compromising **trust or integrity**.

## Compositors

Plantangenet’s **compositors** are the system’s *view factories*, transforming raw, high-dimensional, time-indexed data into meaningful, policy-compliant outputs. They decouple *generation* from *presentation*, letting many independent axes produce domain-specific impulses while ensuring consumers receive filtered, shaped, and negotiated views tailored to their focus and trust level.

A compositor holds **composition rules**: pluggable, ordered transformations that turn frames or graphs into usable forms. These rules can degrade resolution, mask sensitive data, filter regions, or compute derived features--like graph connectivity, communication patterns, or physical quantities. This layered approach enforces *modularity*, *privacy*, and *negotiation* without hardcoding assumptions about how data is used.

Compositors support **ephemeral snapshots** (frames) and **structured graphs** (like squads), unifying agents, sessions, and resources into shared semantic buffers. Consumers declare interests through *cursors*, which shape what detail is prioritized. The compositor respects these signals while applying policy to ensure what’s shared aligns with negotiated permissions.

By tracking *dirty regions* and supporting *asynchronous updates*, compositors avoid recomputing or sending stale data. This allows large, distributed systems to remain responsive under load while maintaining precise control over what changes are processed and delivered. Frames can be skipped or summarized as needed, supporting lossy, demand-driven memory.

**Membry** relies on compositors to store *degraded*, policy-shaped views of frames for long-term memory. When a turn of raw data is collated, the compositor produces simplified, redacted, or aggregated versions suited to negotiated retention policies and paid-for detail levels. This ensures memory isn't just cheaper or lossy--but *intentional* and *auditable*.

Compositors also support advanced models like **GraphCompositors** and **FBCompositors**, handling agent networks, UI buffers, and even streaming protocols. These implementations enforce shared principles: data is transformed intentionally, privacy is maintained through policy, and outputs are negotiated rather than blindly copied.

* **Separation of Concerns:** Compositors decouple raw production from policy-shaped, focus-aware consumption.
* **Negotiated Views:** They enforce filtering, degradation, and transformation rules for privacy, trust, and economic fairness.


**Note:**

> * Compositors ensure **everyone sees only what they’re allowed**, in the form they need.
> * They don’t dictate *how* data is rendered or interpreted, only *what* is exposed and *how* it is shaped for consumers.
> * This enables scalable, federated, policy-compliant sharing that adapts to different trust levels, use cases, and economic constraints.

Excellent--this second example (your **DigitalHandballReferee**) is *simpler* but **still proves the generality of the Referee abstraction**. Let’s analyze how it fits:

## Referee

A **Referee** in Plantangenet is an **adjudication agent** that resolves *conflicting claims* about system state or operations. Unlike policies that enforce permissions, Referees **decide what is true** when participants disagree.

Referees operate on **submitted states** or **proposed actions** from agents. They apply **policy-defined validation rules** and return standardized **judgements**:

* **WIN / LOSE / DRAW** – Outcome adjudication
* **CONTEST** – Multiple valid conflicting proposals
* **CHEAT / ERROR** – Invalid or malicious submissions
* **UNKNOWN** – Insufficient data

Referees are **pluggable** and **domain-agnostic**. They can:

* Enforce rules for games (e.g., TicTacToe, Breakout)
* Validate sensor inputs in IoT systems
* Resolve edits in collaborative documents
* Mediate shared resource conflicts

By formalizing adjudication as a **first-class concept**, Plantangenet ensures **auditable, policy-compliant resolution** of disagreements, even among untrusted participants.

**Note:**

> * Referees enable **conflict resolution** within sessions and squads.
> * They produce **transparent, explainable judgements**.
> * Judgements are standardized for interoperability.
> * Any domain can define **custom referee logic** while preserving auditability.

## Privacy

Plantangenet doesn’t treat privacy as absolute secrecy enforced only by encryption. Instead, it uses **mathematical transforms**--like degradation, masking, summarization--to control *what* is shared, *how much* detail is revealed, and *to whom*. This approach enables collaboration across trust boundaries by ensuring that even shared data respects policy and context, without relying solely on unbreakable locks.

At its core, the system enforces **policy-defined, auditable sharing**:

* Data can be transformed before leaving its source.
* Consumers see only authorized, negotiated views.
* Sensitive details can be masked or degraded as needed.

**Chem**

A **chem** is a **negotiated, policy-bound identity** that acts as a privacy-preserving boundary:

* Bridges **private session state** and **network-facing persona**.
* Filters and transforms data to enforce **partial disclosure**.
* Supports **asymmetric trust**: consumers see only what they’re allowed.
* Enables **auditable, negotiated sharing** between untrusted peers.


**Comdec**

A **comdec** is the **delivery layer** that distributes these composed, policy-shaped views to external systems:

* Streams video, updates UIs, feeds APIs.
* Ensures **policy-shaped outputs** remain consistent at delivery.
* Separates **internal state** from **external presentation**.


**Notes:**

> * Privacy is enforced through **transformations**, not just encryption.
> * Chems negotiate **who sees what** under policy-defined rules.
> * Comdecs manage **how** these approved views are delivered.
> * All sharing is **explicit, bounded, and auditable**.


## What's a Rosetta Stone?

The Rosetta Stone was an ancient artifact inscribed with the same text in multiple scripts, which enabled scholars to decode Egyptian hieroglyphs by comparing translations. (Wikipedia)

It shows the same system explained in different ways so that different kinds of people can understand it. Each version uses its own words and examples, but they all describe the same system: one with clear rules that makes sure nothing is lost or hidden. By reading these sections, everyone--designers, engineers, players, and organizers--can see how Dust works, how the rules are set, and how all the money or value is tracked and shared fairly.

