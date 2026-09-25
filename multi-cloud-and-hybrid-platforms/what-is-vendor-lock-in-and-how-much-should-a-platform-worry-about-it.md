---
title: "What is vendor lock-in and how much should a platform worry about it?"
id: 186
category: "Multi-Cloud and Hybrid Platforms"
difficulty: "Beginner"
tags:
  - platform-engineering
  - multi-cloud-and-hybrid-platforms
  - interview-questions
---

# What is vendor lock-in and how much should a platform worry about it?

**Short answer:** Vendor lock-in is the cost of leaving a provider - the engineering time, data transfer, retraining, contract penalties, and risk it would take to move. It is not binary and it is not always bad: using a managed database is lock-in, and it is also why you are not running that database yourself. A platform should worry about lock-in enough to know its exit cost and to avoid needless dependencies, but not so much that it rebuilds every managed service as a portable abstraction.

## Detail

**Lock-in has several distinct forms**, and they do not all move together:

- **Technical.** Your code and infrastructure depend on provider-specific APIs, services, or semantics - a proprietary queue, a serverless event model, an IAM policy language.
- **Data.** Large datasets are slow and costly to move, and every service attached to them raises the cost further. This is usually the heaviest form.
- **Skills and operations.** Runbooks, on-call knowledge, dashboards, and certifications are provider-specific. Moving means relearning under pressure.
- **Commercial.** Multi-year commitments, committed-use discounts, and marketplace purchases tie money to one provider.
- **Contractual and regulatory.** Certifications or customer contracts may name a provider, which is lock-in by agreement.

**Lock-in is a trade, not a mistake.** Every managed service you adopt swaps exit cost for something valuable: less operational toil, faster delivery, features you would never build. The mistake is taking on lock-in without noticing, or taking it on for something trivial where a standard alternative existed at no extra cost.

**The cheap defences are worth taking by default.** These reduce exit cost without giving up managed services:

- Containers and Kubernetes as the compute interface.
- OpenTelemetry for instrumentation, so telemetry is not tied to one backend.
- Standard protocols - PostgreSQL wire compatibility, S3-compatible object APIs, OIDC for identity.
- Infrastructure as code (OpenTofu or Terraform, Pulumi, Crossplane) rather than console clicks.
- OpenFeature for feature flags, so the flag vendor sits behind one adapter.

**The expensive defences need a specific reason.** Abstracting databases, IAM, or networking across providers means using only the features every provider shares, or self-hosting the portable equivalent. You then own that abstraction forever - you have swapped provider lock-in for lock-in to your own layer, which has one maintainer and thin documentation. See [What does a genuinely portable platform abstraction cost you?](./what-does-a-genuinely-portable-platform-abstraction-cost-you.md) for the full cost.

**Regulation has changed the conversation.** Two developments make exit planning a formal requirement rather than an architectural preference in Europe. The EU Data Act lets cloud customers switch providers and, from 12 January 2027, bans switching charges including data egress fees for the switch itself (ongoing egress for parallel multi-cloud use is still chargeable). DORA, applying since January 2025, requires financial entities to have documented, tested exit strategies for critical ICT providers. Neither requires running two clouds; both require knowing how you would leave.

**How much to worry: measure, then decide.** The practical platform answer is an exit assessment - a short, regularly refreshed document listing each capability, how hard it would be to move, a rough effort estimate, and what makes it hard. It gives leadership the risk visibility and negotiating position most people want from "avoiding lock-in", at a tiny fraction of the cost of building for portability.

**Name the user.** Application teams consume the platform's choices. If the platform standardises on a provider-specific queue, every team inherits that dependency. The platform team is therefore the right place to make lock-in decisions deliberately, record them in an ADR, and keep the exit assessment current - so individual teams do not each make the call inconsistently.

## Example

```text
Exit assessment - refreshed twice a year, owned by the platform team.

  CAPABILITY          LOCK-IN FORM        EXIT DIFFICULTY   EFFORT     WHY
  compute             technical           low               weeks      containers on Kubernetes
  CI/CD               technical           low               weeks      runners are portable
  observability       technical           low               weeks      OpenTelemetry end to end
  object storage      data                moderate          months     140 TB; S3-compatible API
  relational data     data + technical    high              months     managed failover, extensions
  identity (IAM)      technical + skills  very high         quarters   policies, roles, federation
  event bus           technical           high              months     proprietary routing rules
  analytics           data + technical    prohibitive       rebuild    no equivalent service

  Decisions recorded:
    - accept lock-in on relational data (ADR-0034): managed failover worth it
    - wrap the event bus behind an internal publishing library (ADR-0041)
    - no action on analytics; reassess if dataset growth changes the picture
```

```yaml
# ADR front matter capturing a deliberate lock-in decision.
id: ADR-0034
title: Use the provider's managed PostgreSQL for all tier-1 services
status: accepted
decision: >
  Adopt managed PostgreSQL with provider-native failover. Stay on the standard
  wire protocol and avoid proprietary extensions so the data remains movable.
lockIn:
  forms: [data, technical]
  exitEstimate: "3-4 months for the largest 5 databases"
  mitigations:
    - "no provider-only extensions without platform review"
    - "logical backups exported weekly to a neutral format"
review_by: 2027-03-31
```

## Interview tips

- Define lock-in as an exit cost, and say it is a trade rather than a failure. Candidates who treat all lock-in as bad sound inexperienced.
- Break it into forms - technical, data, skills, commercial, contractual - and name data as the heaviest.
- Separate cheap defences (containers, OpenTelemetry, standard protocols, IaC) from expensive ones (abstracting data, IAM, networking), and recommend the cheap ones even for single-cloud organisations.
- Mention the EU Data Act switching rules and DORA exit strategies as reasons exit planning is now formal in Europe - without claiming either requires multi-cloud.
- The strongest close is the exit assessment: measure lock-in, record decisions in ADRs, and refresh it rather than building for a migration that may never happen.

---

[⬅ Back to Multi-Cloud and Hybrid Platforms](./README.md) · [All topics](../README.md)
