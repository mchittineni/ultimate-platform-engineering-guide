---
title: "How do you scale a platform organisation from one team to several?"
id: 249
category: "Platform Team and Operating Model"
difficulty: "Advanced"
tags:
  - platform-engineering
  - platform-team-and-operating-model
  - interview-questions
---

# How do you scale a platform organisation from one team to several?

**Short answer:** Split when one team can no longer hold the platform in its head or prioritise one backlog coherently - not when headcount reaches an arbitrary number - and split along capability boundaries that match what product teams consume, not along technologies. Then deliberately keep the platform feeling like one product to its users: one front door, one interface convention, one roadmap view, shared standards. Team Topologies' second edition calls this a platform grouping - several teams under a shared mission - and the hard part is that the platform teams must also treat each other as X-as-a-Service consumers, or you rebuild the ticket queues inside the platform.

## Detail

**The trigger is cognitive load on the platform team, not size.** The same constraint the platform removes from product teams applies to the platform team itself. The signals are concrete: on-call engineers paged for components they have never touched, one backlog mixing cluster upgrades with CLI features so nothing gets prioritised well, planning meetings that cannot reach a decision because the scope is too wide, and a team past roughly eight or nine people where communication overhead is visible. Any one is a warning; several together mean it is time.

**Split along capability boundaries users recognise.** Good seams follow what product engineers consume: delivery (pipelines, deployment, progressive rollout), runtime (clusters, scaling, networking), data services (databases, queues, caches), observability, and developer experience (templates, portal, CLI). Each has a clear interface and a clear set of users. Splitting by technology - a "Kubernetes team", a "Terraform team" - produces teams that each own half of every user journey, so every request needs two teams.

**Consider the layer split, but know its cost.** Many organisations separate a substrate or foundations team (cloud accounts, landing zones, cluster fleet) from developer-facing capability teams. This works because the foundations team's users are the other platform teams, and its interface can be stable and well defined. The cost is that the foundations team can drift far from product engineers' needs; rotate people, and make it consume feedback from the teams above it.

**Conway's law will shape the product, so design for it.** Whatever the team boundaries are, the platform's interfaces will end up mirroring them. If three teams each ship their own CLI, users get three CLIs with three login flows. The antidote is explicit shared conventions: one service specification or API that multiple teams contribute fields to, one portal or CLI as the front door, a shared design standard for error messages and docs. Users should not need to know the platform's org chart.

**Inside the platform, use the same interaction modes.** The runtime team consuming the foundations team's clusters should do so through a documented interface, not by asking in chat. Collaboration between platform teams is fine when discovering a new capability, and should be time-boxed. A platform organisation whose teams need constant coordination to ship anything has recreated the bottleneck it was built to remove, just one level down.

**Each team needs a product owner and a team API.** Every platform team should have someone accountable for outcomes and a published "team API" - what it owns, how to consume it, how to reach it, what it is working on, and its interaction mode with each neighbour. Above the teams, a platform leadership group (head of platform, a principal engineer, a lead PM) owns the combined roadmap, cross-cutting standards, and resolving boundary disputes.

**Keep one set of success measures.** Adoption, lead time, onboarding time, and developer satisfaction should be reported for the platform as a whole as well as per team. Per-team metrics alone encourage local optimisation - the delivery team can hit its targets while the end-to-end "create a service" journey gets worse.

**Split on-call with the teams, with a documented boundary.** Each team runs its own rotation for what it owns, with a clear escalation path across boundaries. An incident that crosses two platform teams should have a named incident commander, not a debate about ownership.

**Add enabling capacity as the number of consumers grows.** Past a certain scale, product teams need help adopting capabilities well, not just access to them. A small enabling team or a rotation keeps the capability teams from drowning in support.

**Failure modes to name:** splitting too early (two teams of three with no rotation floor), fragmented user experience, platform teams depending on each other through tickets, a foundations team nobody consumes directly and nobody holds accountable for developer outcomes, and a platform leadership layer that grows faster than the teams it coordinates.

## Example

```text
Evolution of one platform organisation over three years.

  STAGE 1 - ONE TEAM (7 engineers, lead holds product role), 20 product teams
    owns everything: clusters, pipelines, templates, observability defaults
    signal to split, observed in year 2:
      - on-call paged for 14 components; engineers unfamiliar with half
      - backlog of 120 items mixing node upgrades with CLI features
      - planning ran 3 hours and still deferred the top two decisions

  STAGE 2 - PLATFORM GROUPING OF 3 TEAMS + LEADERSHIP, 45 product teams
    foundations (5)   cloud accounts, landing zones, cluster fleet, networking
                      users: the other two platform teams
                      interaction: X-as-a-Service via a fleet API
    runtime and data (6)  workloads, scaling, databases, queues, secrets
                      users: product engineers
    delivery and devex (6)  pipelines, progressive delivery, templates, CLI, portal
                      users: product engineers; owns the ONE front door
    leadership: head of platform, 1 principal engineer, 1 lead PM
                owns the service specification standard and combined roadmap

  STAGE 3 - ADD OBSERVABILITY AND ENABLING, 80 product teams
    observability (5)  split out of runtime once telemetry cost and OTel
                       pipeline ownership became a full backlog of their own
    enabling (3, rotating)  helps product teams adopt capabilities, feeds back
    PMs: one per capability team, lead PM across all

  WHAT STAYED SINGULAR, deliberately
    one service specification file   (teams own fields, not files)
    one CLI and one portal           (owned by delivery and devex)
    one scorecard                    (platform-wide AND per team)
    one incident process             (named incident commander across teams)
```

```yaml
# team-api.yaml - the published "team API" for one platform team,
# kept next to its code and rendered into the developer portal.
team: runtime-and-data
mission: "Product teams run and scale services and their data stores without tickets."
owns:
  - capability: workloads
    interface: "spec.runtime in service.yaml"
  - capability: managed-databases
    interface: "spec.database in service.yaml"
  - capability: secrets
    interface: "spec.secrets in service.yaml"
consumes:
  - team: foundations
    capability: cluster-fleet
    mode: x-as-a-service # via the fleet API; no ad-hoc requests
provides-to:
  - consumers: product-teams
    mode: x-as-a-service
  - consumers: team-ml
    mode: collaboration # GPU workloads, time-boxed discovery
    until: 2027-03-31
contact:
  support: "#platform-runtime"
  on-call: "runtime-and-data-primary"
roadmap: "go/platform-roadmap#runtime-and-data"
product-owner: "runtime-pm@example.com"
```

## Interview tips

- Lead with the trigger: split on cognitive load and backlog coherence, not headcount. Give concrete signals you would look for.
- Split by capability users consume, not by technology, and explain why technology splits make every request a two-team request.
- Invoke Conway's law and describe how you prevent the org chart leaking into the product: one front door, one specification, shared conventions.
- Mention that the Team Topologies second edition describes a platform as potentially a grouping of teams, and that the interaction modes apply between platform teams too.
- Name the users of each team, including the foundations team whose users are other platform teams.
- Keep platform-wide success measures alongside per-team ones to avoid local optimisation.
- Likely follow-ups: "how would you resolve a boundary dispute between two platform teams?" and "when would you merge teams back?" Related: [what Team Topologies says about platform teams](./what-does-team-topologies-say-about-platform-teams.md), [sizing and staffing a platform team](./how-do-you-size-and-staff-a-platform-team.md), and [what an enabling team does](./what-is-an-enabling-team-and-how-does-it-work-with-a-platform-team.md).

---

[⬅ Back to Platform Team and Operating Model](./README.md) · [All topics](../README.md)
