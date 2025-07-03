# Plantangenet

## 🪐 Build Tiny Universes with Negotiated Trust

**Plantangenet** is a framework for creating **bounded, policy-enforced worlds** where sharing is *negotiated*, *partial*, *auditable*, and *ephemeral* as a core feature.

It gives developers, system architects, and world-builders the tools to model **trust**, and **privacy** as first-class system features.

---

If you'd like to dive into technical details right away, see the [Technical README](README-TECHNICAL.md).

---

## Why?

Modern systems often assume static permissions and all-or-nothing sharing.

**Plantangenet** flips that model:

- **Negotiated Disclosure**  
  *Define exactly what you share, with whom, and at what level of detail.*
- **Enforceable Policies**  
  *Machine-enforced rules for access, roles, and conditions.*
- **Ephemeral Memory**  
  *Attention-shaped, fading storage that models forgetting as a feature.*
- **Economic Incentives**  
  *Control retention and access with explicit costs (Dust).*

---

## Who Is It For?

- **Hackers** building strange, constrained, privacy-aware systems
- **CTOs** designing federated or zero-trust architectures
- **Game and economy designers** modeling negotiated trade and partial disclosure
- **Collaborative creators** who need nuanced sharing contracts

---

## What Can You Build?

- Private federated services with role-based views
- Multiplayer games with secret negotiation
- Attention-priced data markets
- Privacy-conscious simulations
- Collaborative apps with time-bounded sharing

---

## Plantangenet isn’t just a library. It’s a philosophy of system design.

- *Boundaries are explicit.*
- *Trust is negotiated.*
- *Memory is shaped by attention.*
- *Privacy is enforced by policy.*

---

## Get Started

Plantangenet includes:

- Sessions with policy-bound lifecycle
- Agents modeling roles and permissions
- Cursors for fine-grained data focus
- Compositors for partial views
- Membry for attention-shaped, fading storage
- A pluggable Policy interface
- Economic incentives via Dust

---

## Economic Model: The Banker Agent

Plantangenet now uses a dedicated **Banker agent** to manage all economic logic, including Dust pricing, negotiation, and transaction auditing. All resource costs, payments, and economic policy enforcement are handled by the Banker, ensuring a single, auditable source of truth for all economic activity.

- All economic operations (pricing, negotiation, payment, refund) go through the Banker agent.
- Sessions and storage no longer manage Dust directly.
- For details, see [Banker Agent Integration](docs/BANKER_AGENT_INTEGRATION.md) and [Cost Base System](docs/COST_BASE.md).

---

## Status

Active, evolving, and open to collaboration.

---

## Support Development

Plantangenet is an independent, self-funded project. If you believe in building software that models trust, negotiation, and privacy as first-class features, please consider supporting development:

- **Emotional Support Tier ($5/mo):**  
  For those who want to see Plantangenet grow and receive regular updates. Your encouragement really matters.
- **On-Call Support Tier ($10,000/mo):**  
  For institutions or projects that want on-call help designing or deploying negotiated systems.

More support tiers are coming soon for individuals and teams seeking closer collaboration, early access to design discussions, or custom integrations. If you have ideas or needs, reach out!

👉 [Become a Patron](https://www.patreon.com/c/plantangenet)

Your support and participation help keep Plantangenet independent, evolving, and open.

👉 [Join our Discord](https://discord.gg/jKE4uN2RJc)

---

## About the Author

Hi! I'm Scott Russell (Queuetue), a systems architect and lifelong generalist with over 25 years of experience designing, scaling, and leading technical teams.

I specialize in turning early-stage ideas into resilient, high-performing systems, drawing on deep experience with simulation, agent-based modeling, and complex, decentralized infrastructure.

My work is informed by natural systems thinking: applying principles of feedback, resilience, and sustainable complexity to both software and organizations. Yes, for interested parties, I do consulting jobs on the side.

---

## License

© 1998–2025 Scott Russell  
SPDX-License-Identifier: MIT
