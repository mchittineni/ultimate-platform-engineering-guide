---
title: "How do you run an RFC process for platform decisions?"
id: 128
category: "Platform Team and Operating Model"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-team-and-operating-model
  - interview-questions
---

# How do you run an RFC process for platform decisions?

**Short answer:** A short written proposal, circulated for a bounded comment period to a defined audience, with a named decider and an explicit outcome recorded at the end. It exists so that decisions affecting many teams get their input before rather than their objection after - and it works only if the scope is narrow enough that most changes do not need one, and if the comment period actually ends in a decision.

## Detail

**What the process is for.** Platform decisions have wide blast radius - a change to the service specification affects forty repositories. An RFC gives the people who will live with the decision a chance to shape it, surfaces constraints the platform team could not know, and creates a record of why the choice was made. It is a consultation mechanism, not a consensus mechanism.

**Consultation, not consensus, and this must be explicit.** Everyone gets input; one named person decides. Requiring agreement means the loudest objection blocks progress and the process becomes something people route around. Stating "the decider is X" at the top of the document removes the ambiguity that makes RFCs drag.

**Scope it narrowly, or the process collapses under its own weight.** RFCs are for changes affecting other teams, hard to reverse, or genuinely contested: the platform interface, a new mandatory control, a deprecation, a tenancy model change, a new supported runtime. Not for internal implementation choices, reversible decisions, or routine work. A team that RFCs everything produces a queue nobody reads, which is the same outcome as having no process.

**Keep it short and structured.** Two pages: the problem, the constraints, the options considered, the proposal, what it costs, what it affects, and the open questions. Long documents are not read, and the discipline of brevity usually improves the thinking.

**Bound the comment period explicitly.** One to two weeks depending on scope, with the closing date in the document. Open-ended review is how RFCs die - not by rejection but by silence. State clearly that absence of comment is acceptance, because otherwise you wait indefinitely for people who have no objection.

**Define the audience per RFC.** Every engineer for a change to the service specification; the platform team and security for an internal security decision. Circulating everything to everyone trains people to ignore it.

**Record the outcome, always.** Accepted, rejected, or superseded, with the reasoning and the significant objections and how they were addressed. An RFC with an unrecorded outcome is worse than none, because the discussion happened and nobody can tell what was decided. For anything architecturally significant, the accepted RFC should also produce an architecture decision record - the RFC captures the debate, the record captures the decision.

**Address the objections in writing.** The value to a dissenting engineer is knowing their point was understood, not necessarily accepted. Summarising each substantive objection and the response is what makes people willing to engage with the next one.

**Watch the failure modes.** Rubber-stamping, where RFCs are published after the decision is effectively made - people notice and stop commenting. Design-by-committee, where the proposal is diluted to satisfy everyone. And process theatre, where the RFC exists but the actual decision happens in a meeting. Each destroys the mechanism's credibility, and the credibility is the only thing making it work.

## Example

```markdown
# RFC-0031: Add a `runtime.interruptible` field to the Service specification

- **Status:** Accepted
- **Author:** alice@example.com
- **Decider:** platform-lead@example.com <- ONE named decider, stated up front
- **Audience:** all engineers (this changes the interface every team uses)
- **Comment period:** 2026-06-02 to 2026-06-16 (2 weeks)
- **Absence of comment is taken as acceptance.**

## Problem

Batch jobs, CI runners, and preview environments currently run on on-demand
capacity. Spot capacity would reduce their cost substantially, but adopting it
requires interruption handling, disruption budgets, instance diversification, and
on-demand fallback. Three teams have attempted this independently; two got the
disruption budgets wrong and had outages during reclamation.

## Constraints

- Teams must not have to implement interruption handling themselves.
- The platform must be able to refuse the declaration where it is unsafe.
- No change to existing services' behaviour.

## Options

1. **Document how to do it.** Rejected: three teams already tried and two got it
   wrong. Documentation is not the missing piece.
2. **Platform decides automatically from the tier.** Rejected: tier 3 does not
   imply interruption-tolerant. A tier-3 job with a long unbreakable transaction
   is not safe to interrupt, and only the team knows that.
3. **A `runtime.interruptible` boolean, validated at admission.** Proposed.

## Proposal

Add `spec.runtime.interruptible` (default `false`). When true, the platform places
the workload on the spot node pool with tolerations, diversification across six
instance families and three zones, a termination handler, a tier-derived
PodDisruptionBudget, and on-demand fallback.

Admission rejects `interruptible: true` where it is unsafe: stateful singletons,
replicas at the minimum for the availability target, or a declared long
unbreakable operation. Rejection includes an explanation.

## Cost and impact

- Additive and optional; no existing service changes behaviour.
- New field on the interface: a permanent support obligation (see RFC-0012 on
  interface minimalism).
- Requires the spot node pool, which exists.
- Estimated saving on current batch and preview workloads: material.

## Open questions

1. Should preview environments default to `true`? (see resolution below)
2. Do we need a per-workload maximum interruption rate?

## Comments and resolution

- **team-data (bob):** "our ETL has a 40-minute unbreakable transaction; we would
  set this to true by mistake." → **Addressed.** Admission rejects the declaration
  when a long unbreakable operation is declared; the rejection names the reason.
- **team-search (carol):** "can preview environments default to true?" →
  **Accepted.** Preview environments will default to `true`; a team can override.
- **team-payments (dave):** "this should be inferred from tier, not declared." →
  **Not accepted.** Tier does not imply interruption tolerance (see option 2).
  Recorded as a substantive objection; dave agreed the ETL example settled it.

## Decision

**Accepted** by platform-lead 2026-06-17. Implementation in RFC-0031-impl.
Architecture decision record ADR-0028 created for the interface change.
```

```text
When to write one, and when not to - the scope discipline that keeps it working.

  RFC REQUIRED
    changes to the Service specification or any team-facing interface
    a new mandatory control or policy
    deprecating a capability
    changing the tenancy model
    adding a supported runtime or a new cloud provider
    anything affecting more than ~5 teams and hard to reverse

  NO RFC
    internal implementation choices with no interface change
    anything reversible in an afternoon
    routine operational work, upgrades, bug fixes
    adding an optional field with a safe default (an ADR is enough)

  Ratio in practice: roughly 1 RFC per month against dozens of changes. If it is
  one a week, the scope is too broad and nobody is reading them - which produces
  the same outcome as having no process at all.
```

## Interview tips

- "Consultation, not consensus, with one named decider" is the sentence that makes the process work, and naming the decider in the document is the concrete mechanism.
- Scope discipline is the other half. Give the ratio - roughly one a month - and say that RFC-ing everything produces a queue nobody reads.
- A bounded comment period with a stated closing date, and absence of comment counting as acceptance, is what stops RFCs dying of silence rather than rejection.
- Recording the outcome always, and addressing each substantive objection in writing, is what keeps people willing to engage with the next one.
- The RFC-versus-ADR distinction - the RFC captures the debate, the record captures the decision - shows you know how the two artefacts relate.
- Name the three failure modes: rubber-stamping, design-by-committee, and process theatre where the real decision happens in a meeting. Each destroys the credibility that is the only thing making the process work.
- If asked for the shape, keep it to two pages: problem, constraints, options, proposal, cost, open questions.

---

[⬅ Back to Platform Team and Operating Model](./README.md) · [All topics](../README.md)
