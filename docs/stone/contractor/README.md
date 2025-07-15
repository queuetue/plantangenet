# Contractor Translation

This document is part of a Rosetta Stone for understanding the Plantangenet system.

---

### **Dust**

In Plantangenet, think of **Dust** as the **flow of current** through a circuit, but with a few key differences. Every operation cycle starts with a **pre-charged system**, like a capacitor or filling a pipe with water, where the **total amount of Dust (current)** is already set. There’s no “spontaneous generation” of extra Dust during the cycle, just like how you can’t get more water in a pipe than you’ve put in, unless there’s a pump (or an uncontrolled leak).

Each participant in the system is like a **valve** or **branch** in the system, and the **paths (reference frames)** they follow determine how the Dust (current) flows. When someone performs an action, it’s like **opening a valve** that allows current to flow through components, with each action having a **cost**. That cost represents **resistance** - the friction in the system, whether it's work done, system coordination, or validation. These resistances are defined upfront, like setting the pressure drop across a valve or fitting.

At the end of each cycle, **everything must balance**: just like you can’t have more or less water in a pipe than you started with, you can’t have Dust that hasn’t been tracked and allocated. Whether it’s **work performed**, **system overhead**, or any **redistribution** (tips, donations, etc.), everything must add up to the original budget.

The goal is to **reduce resistance**. The lower the resistance (fewer bottlenecks, less friction), the more efficient the flow of Dust becomes, which means more useful work can be done with less cost.

**Note:**

> * The total Dust available is **pre-charged**, like a pipe with a set amount of water.
> * Costs (resistances) are predefined and represent friction (work, overhead, validation).
> * Everything is **tracked and accounted for**, just like you can't have more water than was originally in the pipe.
> * Optimization means **reducing resistance**, which leads to more efficient work per unit of Dust.

---

### **Profit**

In Plantangenet, **profit** is the **net gain** achieved by improving the efficiency of the system. If you think about it like a water system, it’s the amount of **flow** (work) you can achieve with less **resistance** (overhead, validation, coordination).

Profit is visible and **auditable**. Just as you can measure how much water flows through a valve, you can measure how much **Dust** is used and how much profit is earned by completing work more efficiently than baseline costs. If you can deliver a service with less friction, or bundle services for more efficiency, that’s like reducing the pressure drop in a pipe - allowing more flow for less cost.

Every transaction (or flow of Dust) is recorded, showing exactly how much was spent on the action, how much was earned, and how the profit was distributed. Redistribution (like tips or donations) is tracked too, ensuring that all the flow of Dust is **accounted for** and that **surplus** doesn’t get lost.

**Note:**

> * Profit comes from reducing **resistance** - similar to improving water flow through a pipe.
> * All transactions are **tracked**, ensuring that no hidden profit or loss occurs.
> * Redistribution mechanisms are **predefined** and always transparent.

---

### **Policy**

In Plantangenet, **policy** is like the **schematic diagram** for a relay control system. It tells you how the **current (Dust)** should flow through the system and under what conditions, just like how a ladder relay diagram defines which switches close and when.

**Policy** defines:

* **Who can act** - like who is allowed to flip a switch or open a valve.
* **What actions are allowed** - just like how certain relay contacts may only close when specific conditions are met.
* **How costs are applied** - like how much energy or pressure is needed to operate the system.
* **What conditions must be met** - just like how relays depend on specific conditions (voltage, timing) before they can act.

Policies are **actively enforced** at runtime. It’s not just a list of rules - it’s like the control logic of your relay system, ensuring every action is **checked** against the policy before it’s allowed to happen.

**Note:**

> * Policy is the **control diagram** that specifies how Dust should flow.
> * Every action is **validated** to make sure it complies with policy.
> * Actions are only allowed when **conditions** are met, just like a relay circuit only completes when all conditions are right.

---

### **Compositors**

**Compositors** are like the **filters** and **transformers** in your control system. They take **raw signals** (data) and **transform** them into usable outputs, similar to how a filter may adjust the flow rate or pressure in a water system.

Compositors work by applying a series of **transformations** - like reducing resolution or masking sensitive data - just like how a pressure regulator may reduce the pressure or filter out impurities in a system. These transformations are **policy-defined**, ensuring that only the **approved flow** (data) is passed through and delivered to the right participants.

Just like how you might use a **flowmeter** to ensure only the right amount of water passes through, compositors ensure that only the data that’s **authorized** and **measured** is shared, maintaining efficiency and privacy.

**Note:**

> * Compositors ensure only **approved**, **policy-compliant** outputs are delivered, much like a regulator ensures the right flow in a pipe.
> * Transformations are **policy-defined**, and ensure only necessary data is passed through.

---

### **Squads**

**Squads** are **groups of agents** working together, like a team of relays or circuits that have been wired together for a specific purpose. Just as you might design a network of relays to complete a series of operations, a **Squad** coordinates a group of agents to perform work within a defined budget.

Each Squad has a **defined budget**, like how each section of a circuit may be allocated a certain amount of power or current. The **coordination** between the agents is tracked, just like how each relay’s actions are monitored to ensure that the system functions smoothly and efficiently.

Squads are responsible for **coordinating and paying** for their internal activities, like message passing or validation. This ensures that the system runs efficiently, with every action being tracked and accounted for.

**Note:**

> * Squads are like **teams of relays** working together, coordinating tasks and managing budgets.
> * Every internal action is tracked and accounted for, ensuring fair distribution of Dust.
> * Coordination overhead is **managed**, like ensuring no energy is wasted in the system.

---

### **Membry**

**Membry** in Plantangenet functions like a **state capacitor**. It’s a **memory layer** that enforces strict rules around storage, ensuring that everything stored in the system is **intentional** and **accounted for**.

When you store data in Membry, it’s like **charging a capacitor** - you must declare how long you plan to keep it and what kind of power (Dust) you’re willing to pay for it. Just like how a capacitor will discharge over time, Membry ensures that **storage has a cost** and that it **fades** or **expires** based on policy.

**Vaulted storage** ensures that even sensitive data can be kept private, just like storing energy in a shielded capacitor. It’s logged and tracked so that the system knows exactly how much storage (Dust) has been used, even if the contents are hidden.

**Note:**

> * Membry is like a **state capacitor**, storing data in a controlled, **policy-defined** way.
> * Storage has **costs** and **duration limits**, ensuring that nothing stays hidden without accountability.
> * All storage actions are **tracked** and **audited**, ensuring fair use of resources.
