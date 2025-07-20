Physics incomplete
========================

What we call Turing Complete might be better expressed as Physics Incomplete.  The entirety of computational space involves a set of axioms that are not yet fully understood, and the Turing Machine is a model of computation that is designed to be able to interact with a subset of those axioms, and to be able to simulate a subset of those axioms.  I call these systems Euler-VonNeyman systems, and they are the basis of all modern computation.

If I had to find the "pop sci" version of what Euler-VonNeyman computation's distinction is, it would be that they require time.  Every modern computational system uses time to organize the steps of computation.  These systems are Euler-VonNeyman systems.

A more nuanced specific is that it only interacts with a model of scalars that move along a single axis, that single axis commonly being time.

* Multiaxis computation (what Star Trek called Holographic computation, I suppose) is a model of computation that can allow a set of dimentions upon which scalar values can interacted with, that has an E-V sitting at each vertice of the space to emulate a scalar presentation. We sometimes simulate this in computer games, using a 3d model of space, and then allowing the scalar values to interact with that space, simulated within the aforementioned single axis model of computation.

These systems are genrally limited by how much E-V you can force into a single vertice, and how hard you want to work on the presentation, which translates the scalar values into a form that can be interacted with by the user.

* Disaxial computation is a model of computation that allows scalar values to represent a themselves within a set of higher dimensional space, not requiring any axis, and in fact expecting the axis will be applied by the user of the system.  Scalars in a disaxial system represent predictable but unknowable fields of values, and the system is designed to allow the user to interact with those fields, in subtle and gross ways.

The Omni is a disaxial system simulator.  It uses a distributed infinite field of structured noise (latent space) to represent the scalar values, the omni created artifacts that represent vector-based modification to the field, which are interpreted by local effectors. The Omni maintains a presentation balanced on this point (it's set of indices along axise sit is interested in), and has the ability to relocate. "useful" systems are vuild on thop of this mechanism, and the Omni is designed to be able to interact with those systems, probably more conventionally designed.  These systems are 100% idempotent and reliable, within specific reference frames.  The system becomes largely about managing rules and controlling reference frame, as an architectural exercise.
---
Latent fields are a way of representing a field of values that is not yet known.  This is maintained locally by distributed agents named "modifiers" Think of a modifier as a single video card out there in space. It has a set of instructions, and a set of values, and it's job is to apply those instructions to those values, and then send the result to the next modifier in the chain.  The Ocean is a system of modifiers that are designed to be able to interact with each other, and to be able to interact with the Omni, and one current implementation of rules that runs is named Autotown, internally as AUTOTOWN_CORE:0.

Other use verticals are encouraged to develop thier own rule sets, and to interact with the Omni, and with each other.

In addition, the Omni has access to an entire conventional E-T system cpu, and this processor is used to manage it's internal state, respond to signals, and perform message passing.  A sublassed Omni usually represents a single abstracted assembly.  "Pools" "Spaceship" "Gravity" "GameTile" "ColorPallete" - the sort of thing we think of "classes" as representing in conventional programming.  What is really does is push states to guide a disconnected and more abstract system and build an interpretation of the reported field.

These concepts map well onto "game engines", "simulation engines" and "rendering engines" in conventional computing, as well as sophisticated machine models or biological models, systems that already run well on "real physics".