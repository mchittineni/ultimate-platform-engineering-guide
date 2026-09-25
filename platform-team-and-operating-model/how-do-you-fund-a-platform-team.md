---
title: "How do you fund a platform team?"
id: 245
category: "Platform Team and Operating Model"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-team-and-operating-model
  - interview-questions
---

# How do you fund a platform team?

**Short answer:** Fund the team centrally as a long-lived product with a stable headcount, not as a series of projects, and justify it with a business case built on the time it saves product teams and the risk and cost it removes. Recover or attribute the _infrastructure_ it runs to consuming teams through showback, and only move to chargeback when teams have real control over their consumption. Charging teams for the platform team's own salaries usually backfires: it turns a shared capability into a price that teams route around, and adoption - the thing that makes the platform worth funding - falls.

## Detail

**Separate two costs that get conflated.** There is the cost of the platform _team_ (people, tooling licences, the portal) and the cost of the _infrastructure_ the platform provisions on teams' behalf (compute, storage, managed services). They should be funded differently. The team is a fixed investment, like a product; the infrastructure is variable consumption that should be visible to, and eventually owned by, the teams driving it.

**The funding models, and what each does to behaviour:**

| Model                         | How it works                                    | Effect on behaviour                                            |
| ----------------------------- | ----------------------------------------------- | -------------------------------------------------------------- |
| Central product funding       | Fixed annual budget for a persistent team       | Stable roadmap; risk of drifting from user needs               |
| Project funding               | Budget per initiative, team disbands after      | Builds then abandons; nobody owns the running platform         |
| Tax / allocation              | Cost spread across business units by a formula  | Simple; teams see a charge they cannot influence               |
| Showback of infrastructure    | Consumption attributed and reported, not billed | Awareness and accountability without a transactional barrier   |
| Chargeback of infrastructure  | Consumption billed to team budgets              | Strong cost discipline; needs accurate attribution and control |
| Chargeback of the team itself | Teams pay per seat, per service, or per request | Teams optimise away from the platform; shadow tooling appears  |

**Project funding is the most damaging model for a platform.** A platform is never finished - it must be upgraded, patched, and supported for as long as teams depend on it. Funding it as a project means the builders leave at the end, and the organisation is left operating something nobody is resourced to maintain. Long-lived, persistently staffed teams are the only model that matches how a platform actually behaves.

**Build the business case from avoided cost, not features.** The strongest argument is time returned to product engineers. If thirty teams each spend a fraction of an engineer on pipelines, cluster upgrades, and security scanning, consolidating that onto a platform team frees more capacity than the platform team consumes. Add the risk reduction - a consistent patching and signing story for an audit, fewer incidents from hand-rolled infrastructure - and the cost reduction from shared commitments and right-sizing. State the baseline explicitly, because you will be asked to prove it later.

**Showback first, chargeback later, and only for consumption.** Attribute infrastructure cost to each team through labels and account structure, and report it - ideally in the FinOps Foundation's FOCUS format so it joins cleanly with cloud billing data. Chargeback becomes reasonable once attribution is trusted and teams can actually change their spend through the platform (sizing, scaling, turning off preview environments). Billing teams for costs they cannot control produces arguments, not savings.

**Why charging for the team itself backfires.** If a team must pay per service to use the golden path, the golden path now has a price and hand-rolling has an invisible one. Rational teams pick the invisible one. The platform ends up competing against the very duplication it was funded to remove. A shared, centrally funded team with transparent consumption costs avoids this.

**Use a maturity lens to match investment to stage.** The CNCF Platform Engineering Maturity Model treats _investment_ as one of its five aspects, alongside adoption, interfaces, operations, and measurement. It describes a progression from provisional (voluntary, part-time effort) through operational (a dedicated team) to scalable (funded and run as a product) and optimising (an enabled ecosystem of contributors). The useful interview point is that funding should follow evidence: a small team proving value first, then a stable product budget once adoption justifies it.

**Recent evidence is a useful supporting argument.** The DORA 2025 research on AI-assisted development found that nearly all respondents' organisations had adopted at least one internal platform, and listed a quality internal platform as one of seven capabilities that determine whether AI adoption improves organisational performance. That gives a funding conversation a current business reason: AI coding tools increase the rate of change, and the platform is what makes that change safe to ship.

**Trade-offs.** Central funding can insulate a platform team from its users, which is why it must be paired with adoption and satisfaction measures. Chargeback gives strong cost signals but needs mature attribution and can create internal billing disputes. There is no model with no downside; the aim is to fund the team stably and make consumption visible.

## Example

```text
A funding proposal for a platform team, as presented to the engineering leadership.

  ASK
    persistent team of 6 engineers + 1 product manager, centrally funded
    reviewed annually against the scorecard below - not a 12-month project

  BASELINE (measured over the last quarter, before the platform)
    32 product teams; survey + time sampling show ~0.3 engineer per team on
    pipelines, cluster upgrades, image patching, and ad-hoc infrastructure
    -> ~9.6 engineers' worth of duplicated effort across the organisation
    time to create a new service: 3 days       onboarding to first deploy: 12 days
    services with a consistent patching and signing story: 38%

  CASE
    capacity: consolidate most of the ~9.6 engineers of duplicated work onto 7
    risk:     one patching, signing, and audit evidence path for all services
    cost:     shared commitments and right-sizing across all teams' workloads
    ai:       AI assistants have raised PR volume; the platform's guardrails
              are what keep change failure rate flat as throughput rises

  FUNDING SPLIT
    platform team salaries, tooling ......... central engineering budget
    infrastructure it provisions ............ SHOWBACK per team, monthly,
                                              exported in FOCUS format
    chargeback .............................. revisit in 2 quarters, only once
                                              attribution coverage > 95% and
                                              teams can resize via the platform
    per-service fee for using the platform .. REJECTED - would make hand-rolled
                                              infrastructure look cheaper

  SCORECARD that justifies next year's budget
    voluntary golden-path adoption, time to create a service, onboarding time,
    change failure rate, developer satisfaction, cost per service
```

## Interview tips

- Separate funding the team from funding the infrastructure it provisions; most weak answers conflate them.
- Say clearly that project funding is wrong for a platform because a platform is never finished.
- Build the business case on duplicated effort avoided, risk reduced, and cost pooled - with a measured baseline.
- Recommend showback before chargeback, and chargeback only for consumption teams can control. Explain why charging for the team itself reduces adoption.
- Mention the CNCF maturity model's investment aspect as a way to match funding to stage, and the DORA 2025 finding that platform quality is one of the capabilities that determines whether AI adoption pays off.
- Likely follow-ups: "what if leadership insists on chargeback?" and "how do you prove the platform paid for itself?" Related: [showback versus chargeback](../platform-finops/what-is-the-difference-between-showback-and-chargeback-and-which-works.md), [attributing shared platform cost](../platform-finops/how-do-you-attribute-shared-platform-cost-to-teams.md), and [sizing and staffing a platform team](./how-do-you-size-and-staff-a-platform-team.md).

---

[⬅ Back to Platform Team and Operating Model](./README.md) · [All topics](../README.md)
