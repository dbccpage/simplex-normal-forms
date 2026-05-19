# Simplex Normal Forms Wiki

Welcome to the **Simplex / Anomalon Normal Forms** project wiki. This project organizes database theory into a disciplined, implementation-oriented framework that extends relational theory from static structures to dynamic data states—specifically data that changes representation, moves across network channels, expires, or is claimed by observers.

---

## Project Overview & Review

Classical relational database theory (1NF through 5NF/DKNF) operates primarily on data *at rest*, focusing on decomposing relations to prevent update anomalies. However, static normalization does not evaluate if a runtime transaction or write event can be repaired, if a replica view commutes, or if distributed stream channels are causally consistent.

The **Simplex Project** introduces a formal substrate to certify data *in motion* using topological cochain complexes. Under this framework:
1. **Quotient Normal Form (QNF)** classifies write events as boundary operations.
2. A write event induces a defect class in a layer's cochain complex.
3. If this defect class evaluates to zero in the quotient obstruction space, the layer is certified as locally repairable.
4. If the defect class is non-zero, the write is blocked or escalated to a fallback route (such as serialization, invalidation, or recomputation).

### Core Components
* **Contracts (`contracts/`)**: Machine-readable YAML schemas that declare structural and operational invariants (e.g., flow control, lightcone causality, time sync).
* **Atlas (`book/`)**: A detailed 12-chapter textbook that maps the relational baseline to higher-dimensional boundary certified databases.
* **Papers (`papers/`)**: Foundational research pre-prints establishing the mathematics of boundary repair, representation transport, and observer ontology.

---

## Project Documentation PDF
The complete textbook and specification have been compiled into a single PDF:
* **File Path**: [`book/pdf/output.pdf`](../book/pdf/output.pdf)

This document contains the complete readings from the [SUMMARY.md](../book/SUMMARY.md), compiling the preface, formal substrates, and advanced observer frameworks.

---

## Interactive Demo Dashboard
An interactive browser-based dashboard has been created to simulate before/after states for the three demos:
* **Local Link**: [examples/index.html](file:///C:/Users/a343o/source/repos/simplex-normal-forms/examples/index.html)

This interface implements the cochain boundary and observer-relative freshness rules locally in the browser to evaluate data state changes in real time.

---

## Wiki Navigation
Explore the technical details of the project:
* **[Theory & Cochain Substrate](Theory-and-Cochain-Substrate.md)**: Visualizations and details of the cochain boundary operators and normal form hierarchies.
* **[Observer-Relative Ontology](Observer-Relative-Ontology.md)**: Details on epistemic observer states, lightcone causality, and data locality.
* **[Concrete Examples](Concrete-Examples.md)**: Three demonstration scenarios (incremental repair, certificate validation, and freshness budgets).
