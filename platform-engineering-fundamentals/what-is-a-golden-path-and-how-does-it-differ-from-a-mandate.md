---
title: "What is a golden path and how does it differ from a mandate?"
id: 6
category: "Platform Engineering Fundamentals"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-engineering-fundamentals
  - interview-questions
---

# What is a golden path and how does it differ from a mandate?

**Short answer:** A golden path is a well-supported, opinionated route through building and running a service - a chosen language, framework, pipeline, runtime, and observability setup - that is genuinely the easiest way to get to production. A mandate is the same set of choices enforced by policy. The difference is what happens when a team has a real reason to deviate: a golden path lets them leave and accept more responsibility, a mandate does not, and mandates therefore produce shadow platforms.

## Detail

**Why the path has to be easier, not just approved.** Adoption follows the gradient of least effort. If the supported route requires reading three wiki pages and copying a chart from another repository, while doing it yourself takes an afternoon, teams will do it themselves regardless of policy. The design target is that the golden path is the fastest way to a running, monitored, compliant service - so that choosing it needs no persuasion.

**What a golden path actually contains.** It is a full route, not a recommendation: a scaffolding template that generates the repository, a pre-wired pipeline, a deployment mechanism, dashboards and alerts that exist on day one, secrets wiring, an owner recorded in the catalogue, and documentation for the whole journey. A "recommended stack" listed in Confluence is not a golden path.

**Golden paths are plural and narrow.** One per common workload shape - stateless HTTP service, scheduled job, event consumer, static frontend - each highly opinionated. Trying to build one path that covers every case produces a configuration surface as complex as the thing it was meant to hide.

**The escape hatch is a feature, and it must be designed.** Teams with genuine reasons - an unusual latency requirement, a GPU workload, a vendor constraint - need a way off the path. Make it explicit rather than accidental: deviation is allowed, it is recorded, the team takes on the operational responsibility the platform was absorbing, and the exemption has an owner and a review date. Indefinite silent exemptions become permanent forks you support anyway.

**Where the escape hatches get used is your best product feedback.** If four teams left the path for the same reason, that is a roadmap item, not a compliance problem. The instinct to close the hatch is almost always wrong; fix the path.

**Where mandates are legitimate.** Not everything can be optional. Controls with regulatory or security consequences - image signing, audit logging, encryption, no public storage buckets - should be enforced guardrails, not paths. The rule of thumb: mandate the properties you must be able to prove, offer paths for the choices that only affect the team making them.

## Example

```text
Golden path: stateless HTTP service (Go)

  platform create service --template go-http --name pricing --owner team-pricing

  Generated, working, on first commit:
    repo scaffold ....... handler, health endpoint, structured logging, Dockerfile
    pipeline ............ build, test, SBOM, scan, sign, deploy to staging
    runtime ............. Deployment + HPA + PodDisruptionBudget + resource requests
    observability ....... RED dashboards, latency + error SLO, burn-rate alerts
    ownership ........... catalogue entry, on-call routing, cost tag
    security ............ workload identity, secrets via CSI driver, network policy

  Time to production: ~30 minutes, no tickets.

Leaving the path (explicit, not accidental):

  # platform-exemption.yaml, reviewed in a PR
  capability: runtime
  reason: "GPU inference; needs node affinity + custom scheduler"
  accepts: [own-dashboards, own-alerts, own-upgrade-cadence]
  owner: team-ml
  review_by: 2027-03-31       # exemptions expire; they do not accumulate silently
```

## Interview tips

- "Golden paths, not mandates" is the phrase, but the reasoning is what earns credit: mandates create shadow platforms, convenience creates voluntary adoption.
- Say explicitly that some things _should_ be mandated - security and compliance guardrails - and that the skill is knowing which is which. Candidates who treat everything as optional sound naive.
- Treating escape-hatch usage as product feedback rather than misbehaviour is the senior signal in this answer.
- Expect "how do you get teams to adopt it without authority?" - make it faster, migrate them yourself, and show the numbers. That question has its own answer in the operating model topic.

---

[⬅ Back to Platform Engineering Fundamentals](./README.md) · [All topics](../README.md)
