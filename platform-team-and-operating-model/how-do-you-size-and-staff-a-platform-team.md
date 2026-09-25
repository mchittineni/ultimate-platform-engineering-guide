---
title: "How do you size and staff a platform team?"
id: 242
category: "Platform Team and Operating Model"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-team-and-operating-model
  - interview-questions
---

# How do you size and staff a platform team?

**Short answer:** Size it from the operational load it must carry plus the capabilities it must build, and treat a sustainable on-call rotation as the hard floor - which in practice means at least four to five engineers before you can responsibly own production-critical infrastructure. Staff for breadth over depth in a single technology, include someone doing product work, and be aware that under-staffing produces the specific failure of a team that only operates and never builds.

## Detail

**The rotation is usually the binding constraint.** Once teams deploy through you, your outage is everyone's outage, which means on-call. A three-person rotation is one week in three, which is not sustainable for long. Four to five is workable if pages are rare. This floor matters more than the capability roadmap, because a team that cannot sustain its rotation loses people and then cannot sustain anything.

**Below the floor, the honest options are narrower scope or shared on-call** - not accepting an unsustainable rotation. A two-person platform effort can build templates, a shared pipeline, and documentation without owning production-critical infrastructure. Taking on the critical infrastructure without the staffing is how you end up with undocumented systems and a severe bus factor.

**The load has three components, and the second is the one that grows:**

| Component | Driven by                                                               |
| --------- | ----------------------------------------------------------------------- |
| Build     | The capability roadmap                                                  |
| Operate   | Number of clusters, accounts, components, tenants                       |
| Support   | Number of teams, and the quality of your documentation and self-service |

Operate scales with your own architectural choices - every additional cluster multiplies component upgrades - which is why cluster count and supported runtime count are staffing decisions disguised as technical ones. Support scales with adoption unless documentation and self-service decouple them, which is the argument for treating documentation as infrastructure.

**Roles to cover, not necessarily one person each:**

- **Infrastructure and control-plane engineering** - the substrate, provisioning, and reconciliation.
- **Delivery and developer experience** - pipelines, golden paths, the inner loop, the interfaces teams touch.
- **Observability and reliability** - telemetry, SLOs, and the platform's own reliability.
- **Security** - identity, policy, supply chain. Often shared with a security team rather than owned outright.
- **Product** - user research, prioritisation, saying no. Frequently missing, and its absence is why platforms get built that nobody adopts.

**Prefer breadth, and one deep specialist.** A team of Kubernetes specialists will build a Kubernetes-shaped platform and struggle with the developer experience, the cost model, and the product conversation. One person with genuine depth in the substrate plus several with breadth across delivery, observability, and cloud is a better shape.

**The product role is the one most often omitted.** Without someone accountable for outcomes rather than delivery, the roadmap fills with technically interesting work and adoption stalls. It does not have to be a product manager - a staff engineer or the team lead can hold it - but it must be someone's explicit responsibility.

**Watch the build-to-operate ratio as the health metric.** A team spending nearly all its time operating and supporting is not going to improve anything, and the fix is either reducing operational load - fewer clusters, fewer runtimes, more automation, better documentation - or adding people. Tracking that ratio makes the staffing conversation evidence-based rather than a matter of opinion.

**Grow the team behind adoption, not ahead of it.** Hiring six engineers before any capability exists produces a large team building speculatively. Two or three proving the golden path, then growing as adoption creates real operational and support load, is the sequence that works - and each hire can be justified with evidence.

## Example

```text
Staffing against load, at three stages of the same platform.

  STAGE 1 - 8 stream-aligned teams, 40 services
    scope: templates, one shared pipeline, IaC modules, documentation.
           NOT production-critical infrastructure.
    team: 2 engineers (or one engineer plus a rotation from a stream-aligned team)
    on-call: NONE of their own - they do not own anything that pages
    -> deliberately below the rotation floor, so the scope excludes anything
       requiring one. This is the honest trade, not an oversight.

  STAGE 2 - 20 teams, 120 services, one shared cluster per environment
    scope: golden paths, self-service provisioning, GitOps delivery, observability
           defaults, policy guardrails. Production-critical.
    team: 5 engineers + product responsibility held by the lead
      1 x deep: control plane and Kubernetes substrate
      2 x breadth: delivery, pipelines, developer experience
      1 x breadth: observability and reliability
      1 x breadth: cloud, security, cost (security shared with the security team)
    on-call: 5-person rotation, 1 week in 5, ~2 pages/shift
    -> 5 is the floor here BECAUSE of the rotation, not because of the roadmap.

  STAGE 3 - 40 teams, 220 services, 9 clusters, 3 clouds
    team: 9 engineers, split into two sub-teams + a dedicated product manager
      sub-team A (4): control plane, provisioning, fleet management
      sub-team B (4): developer experience, delivery, observability
      1 x reliability and cost across both
    on-call: two rotations aligned to the sub-teams, with a documented boundary
    -> the split happened because ONE backlog could no longer be prioritised
       coherently, not because of headcount.
```

```text
The build-to-operate ratio - the metric that makes staffing an evidence question.

  QUARTER   BUILD   OPERATE   SUPPORT   NOTE
  2025-Q4    55%      28%       17%     healthy
  2026-Q1    41%      34%       25%     cluster count 4 -> 7; support rising
  2026-Q2    28%      42%       30%     UNHEALTHY. Almost nothing being improved.
  2026-Q3    44%      33%       23%     after the interventions below

  What was done in Q3 - reduce load before adding people:
    consolidated 7 clusters to 5 .................. operate down
    dropped a second supported runtime ............ operate down
    automated the top 3 recurring pages ........... operate down
    exposed in-flight deploy status to teams ...... support down (41 -> ~3
                                                    questions/month in that
                                                    category)
    wrote the 6 most-asked-for how-to pages ....... support down
    THEN hired 2 engineers ........................ build up

  The order matters. Hiring first would have added capacity to an operational
  load that was growing faster than the team, and the ratio would not have moved.
```

## Interview tips

- Lead with the rotation as the hard floor and give a number - four to five before owning production-critical infrastructure. It is concrete and it is the constraint that actually binds.
- Say plainly that below the floor the answer is narrower scope or shared on-call, not an unsustainable rotation. That is the judgement interviewers are testing.
- The three load components, and specifically that operate scales with your own architectural choices, reframes cluster count and runtime count as staffing decisions.
- Support scaling with adoption unless documentation decouples them is the argument for treating documentation as infrastructure rather than a chore.
- Breadth over depth, with one deep specialist, and the observation that a team of Kubernetes specialists builds a Kubernetes-shaped platform, shows you think about the whole product.
- The missing product role is the highest-value gap to name, because its absence is why platforms get built that nobody adopts.
- The build-to-operate ratio, and reducing load before adding people, is the strongest close - it makes the staffing argument evidence-based and shows you would not simply ask for headcount.

---

[⬅ Back to Platform Team and Operating Model](./README.md) · [All topics](../README.md)
