---
title: "When is multi-cloud a real requirement rather than a slogan?"
id: 99
category: "Multi-Cloud and Hybrid Platforms"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - multi-cloud-and-hybrid-platforms
  - interview-questions
---

# When is multi-cloud a real requirement rather than a slogan?

**Short answer:** It is real when something outside your control forces it - a regulator or customer contract requiring a specific provider or jurisdiction, an acquisition bringing an estate you cannot economically migrate, a capability that genuinely exists on only one provider, or a sovereignty requirement. It is a slogan when the justification is avoiding lock-in, negotiating leverage, or resilience against a provider outage, because in each of those cases the cost usually exceeds the benefit and there is a cheaper way to get most of the value.

## Detail

**The genuine drivers, and each is externally imposed:**

- **Regulatory or contractual.** A regulator, or a large customer's procurement terms, requires a named provider or a jurisdiction only one serves. Not arguable, and it is the most common real reason.
- **Acquisition.** You bought a company running elsewhere. Migration has a cost and a risk; sometimes running both is the rational answer for years.
- **A capability that exists in one place.** A specific managed service, a hardware type, or a partner integration with no adequate equivalent.
- **Sovereignty.** Data or operations must be under a specific national or provider-independent control regime.

**The reasons that usually do not survive examination:**

- **Avoiding lock-in.** Building on the lowest common denominator means giving up managed services and writing abstraction layers - you have exchanged provider lock-in for lock-in to your own abstraction, which has fewer maintainers and no documentation. The honest position is to choose which lock-in you accept, not to imagine you can avoid all of it.
- **Negotiating leverage.** Real but usually much smaller than the cost of maintaining genuine portability, and often achievable with a credible migration plan rather than an actual second estate.
- **Provider outage resilience.** Almost always the wrong tool. Provider-wide outages are rarer than regional ones, and multi-region within one provider is far cheaper and simpler. A genuinely active-active multi-cloud deployment means duplicated data with cross-provider consistency and egress costs, which is a large amount of complexity for a risk that multi-region already mostly addresses.
- **"Best of breed."** Occasionally true for a specific workload, and frequently a justification for a preference rather than a requirement.

**The honest cost, which is what makes this a judgement question.** Two of everything: identity models, network designs, IAM semantics, observability integrations, cost models, deployment paths, quota systems, and on-call expertise. The platform team's surface roughly doubles while its headcount does not. Deep expertise in one provider becomes shallow expertise in two - which shows up during incidents.

**Distinguish the useful middle ground.** Most organisations described as multi-cloud are one primary provider plus something small: a data warehouse elsewhere, a SaaS product that happens to run on another provider, or a legacy estate being wound down. That is not a portable platform and does not need one - it needs the primary platform to be excellent and the exception to be contained and explicitly bounded.

**If it is genuinely required, choose the depth deliberately.** Portable workloads only, with provider-specific data and managed services, is much cheaper than portable everything. Kubernetes gives you a common compute API, which is real value; it does not make your databases, IAM, or networking portable, and pretending otherwise is where multi-cloud programmes fail.

## Example

```text
Four claimed requirements, examined.

CLAIM  "we need multi-cloud to avoid vendor lock-in"
  test  what would you actually do differently in the next 12 months?
  reality  you would avoid managed databases, queues, and identity integration,
           and build abstractions over them
  verdict  SLOGAN. You have traded provider lock-in for lock-in to your own
           abstraction layer, which has one maintainer and no documentation.
           Better: choose the lock-in deliberately, keep an exit assessment
           current, and wrap the genuinely hard-to-exit pieces.

CLAIM  "we need multi-cloud for resilience against a provider outage"
  test  what is your actual availability target, and what does the incident
        history say?
  reality  target 99.95%; regional failures dominate; you are not multi-region
           within your current provider yet
  verdict  SLOGAN, and a distraction. Do multi-region first: far cheaper, addresses
           most of the risk, and you will learn whether you can even fail over.

CLAIM  "our largest customer's contract requires their data in provider X"
  test  is it in writing?
  reality  yes, and the contract is a material share of revenue
  verdict  REAL. Externally imposed and non-negotiable. Scope it to that
           customer's workloads rather than making the whole platform portable.

CLAIM  "we acquired a company running on another provider"
  test  what does migration cost, and what is the risk?
  reality  18 months of engineering, high risk, no product benefit
  verdict  REAL, at least for now. Run both, keep them separate, and make the
           migration decision on economics rather than tidiness.
```

```text
Depth of portability - pick one deliberately, because the cost differs enormously.

  LEVEL 0  single cloud, exit assessment kept current
           cost: none.  Most organisations should be here.

  LEVEL 1  containerised workloads, provider-specific everything else
           cost: low. Kubernetes as the compute API. Data, IAM, and networking
           stay native. Covers "we could move if we had to, with effort".

  LEVEL 2  workloads portable + one abstracted capability (e.g. object storage)
           cost: moderate. Justified when a specific requirement demands it.

  LEVEL 3  genuinely portable platform - abstracted data, identity, networking
           cost: HIGH and permanent. Managed services largely unavailable to you.
           Justified almost only by regulation or sovereignty.

  LEVEL 4  active-active across providers
           cost: very high. Cross-provider data consistency and egress.
           Justified by almost nothing outside specific regulated cases.

  The failure mode is claiming Level 1 and being surprised that the databases,
  IAM, and networking did not come along.
```

## Interview tips

- Structure the answer as externally imposed versus internally chosen. Real drivers come from outside; slogans come from architectural preference.
- Take the lock-in argument seriously and then dismantle it precisely: you exchange provider lock-in for lock-in to your own abstraction, with fewer maintainers and no documentation.
- The resilience argument is the one most worth redirecting - multi-region within one provider is cheaper, simpler, and addresses most of the risk. Suggesting it shows judgement.
- Quantify the cost as the platform team's surface roughly doubling while headcount does not, and note that deep expertise in one provider becomes shallow expertise in two, which shows up during incidents.
- Name the useful middle ground: one primary provider plus a contained exception is what most "multi-cloud" organisations actually are, and it does not require a portable platform.
- The portability levels are a strong structuring device, and the closing insight - that claiming portable workloads and being surprised the data did not come along - is the realistic failure.

---

[⬅ Back to Multi-Cloud and Hybrid Platforms](./README.md) · [All topics](../README.md)
