---
title: "What is FinOps and what part of it does a platform team own?"
id: 224
category: "Platform FinOps"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-finops
  - interview-questions
---

# What is FinOps and what part of it does a platform team own?

**Short answer:** FinOps is the practice of bringing financial accountability to variable cloud spend, so that the people making technical decisions can see and own their cost consequences. A platform team owns the mechanics: making cost visible and attributable, building efficient defaults into the paved road, holding the commitments and capacity strategy centrally, and eliminating shared waste. It does not own the business decision about whether a given spend is worth it.

## Detail

**Why cloud cost needs a practice at all.** In a data centre, capacity was a procurement decision made once, by a small number of people. In the cloud an engineer's pull request changes the monthly bill, thousands of such decisions are made continuously, and the bill arrives a month later aggregated into something nobody can trace back. FinOps exists to close that feedback loop.

**The standard shape of the practice is three iterating phases** - inform, optimise, operate. Inform means visibility, allocation, and forecasting: teams knowing what they spend. Optimise means acting on that - right-sizing, commitments, eliminating waste. Operate means making it continuous: policy, automation, and accountability rather than a quarterly clean-up exercise. Most organisations attempt to optimise before they can inform, which produces argument rather than savings because nobody agrees on the numbers.

**The scope is wider than cloud now.** The FinOps Framework has grown from public cloud to "Cloud+" scopes - SaaS, software licensing, data centre, and AI spend including model APIs and GPUs - and the FinOps Foundation's FOCUS specification gives all of those sources a common billing schema. For a platform team this mostly means the observability vendor, the CI provider, and model API usage belong in the same cost view as compute. See [What is the FOCUS specification and why does it matter?](./what-is-the-focus-specification-and-why-does-it-matter.md).

**What a platform team specifically owns:**

| Platform owns                                     | Someone else owns                        |
| ------------------------------------------------- | ---------------------------------------- |
| Attribution: tags, accounts, allocation model     | Whether a product's margin is acceptable |
| Making cost visible where engineers work          | Budget setting per team                  |
| Efficient defaults in the paved road              | Prioritising cost work against features  |
| Commitment and spot strategy across the estate    | Contract negotiation with providers      |
| Shared infrastructure efficiency                  | Product pricing decisions                |
| Eliminating waste in platform-managed resources   | -                                        |
| Guardrails: budgets, anomaly alerts, quota limits | -                                        |

The division that matters: the platform makes cost visible and makes the efficient path the easy path. It does not decide whether spend is justified, and a platform team that tries to becomes an unpopular internal auditor rather than a service.

**Defaults are the highest-leverage thing a platform team has.** A right-sized default, scale-to-zero for non-production, a shorter retention tier for low-tier services, and spot capacity for interruptible work each save money across every service at once, with no team doing anything. One default change beats fifty conversations about optimisation, and this is the argument for the platform owning the paved road's efficiency.

**Commitments belong centrally.** Reserved capacity and savings plans need to be bought against aggregate usage; individual teams cannot commit sensibly for the estate. Centralising the commitment and passing the discount through is a clear case where the platform saves money that no team could save alone.

**Make cost visible at the point of decision, not in a monthly report.** An estimated cost on the pull request that provisions a resource, or in the interface where a size is chosen, changes behaviour. A report a month later informs an argument.

**Cost efficiency is not always the goal.** Sometimes the right answer is spending more - for reliability, for latency, or to ship faster. A platform team that reflexively minimises spend does damage. The useful framing is efficiency per unit of value rather than absolute reduction.

## Example

```text
The three phases, and what the platform contributes to each.

  INFORM  - can a team see and trust its number?
    account and tag hygiene enforced at provisioning
    allocation model for shared cost, agreed and published
    Kubernetes cost split by namespace
    unallocated percentage published as the credibility metric
    -> until this works, optimisation is argument rather than savings

  OPTIMISE - act on it
    right-sized defaults in the paved road           (platform, one change, all services)
    scale-to-zero for non-production                  (platform default)
    spot capacity for interruptible workloads          (platform node pools)
    commitments bought against aggregate usage         (platform, centrally)
    tiered retention for logs, metrics, traces         (platform default by tier)
    idle resource reaping                              (platform automation)
    per-service right-sizing recommendations           (platform surfaces; team acts)

  OPERATE - make it continuous, not a quarterly clean-up
    budgets and anomaly alerts to owning teams
    cost visible in the PR that provisions a resource
    monthly showback per team, published
    quotas that bound the worst case
    cost as a review dimension for new platform capabilities
```

```text
Where the platform's leverage actually is - one change versus fifty conversations.

  PLATFORM DEFAULT CHANGES (one action, whole estate, no team involved)
    non-production scale-to-zero after 20m idle ....... large, immediate
    default instance family moved to current generation  meaningful, no downside
    log retention 30d -> 7d for tier 3 ................. meaningful
    trace baseline sampling 10% -> 1% for tier 3 ....... meaningful
    preview environment TTL 7d -> 72h .................. meaningful
    interruptible workloads onto spot node pools ....... large
    -> each of these is a platform decision. Nobody negotiates, nobody prioritises
       it against feature work, and every service benefits at once.

  PER-TEAM OPTIMISATION (fifty conversations, each competing with product work)
    right-size this over-provisioned service
    remove that unused resource
    fix that high-cardinality metric
    -> real savings, but each one needs a team's attention. The platform's job
       here is to SURFACE the finding with the fix attached, not to chase it.

  The order matters: exhaust the defaults before asking teams to optimise.
```

## Interview tips

- Define FinOps by the feedback loop it closes: engineers make cost decisions continuously and the bill arrives a month later aggregated beyond recognition.
- Name the three phases and make the point that most organisations optimise before they can inform, which produces argument rather than savings because nobody trusts the numbers.
- Draw the ownership line clearly: the platform makes cost visible and makes the efficient path easy; it does not decide whether spend is justified. A platform team that becomes an internal auditor loses its relationship with teams.
- Defaults as the highest-leverage lever - one change beats fifty optimisation conversations - is the strongest platform-specific insight here.
- Central commitments as a saving no individual team could achieve is a clear, concrete example of the platform earning its place.
- Cost visible at the point of decision rather than in a monthly report is the behavioural mechanism.
- Close by saying efficiency is not always the goal, and that the right framing is cost per unit of value. Reflexive minimisation is a failure mode interviewers will probe for.

---

[⬅ Back to Platform FinOps](./README.md) · [All topics](../README.md)
