---
title: "What is platform engineering?"
id: 1
category: "Platform Engineering Fundamentals"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-engineering-fundamentals
  - interview-questions
---

# What is platform engineering?

**Short answer:** Platform engineering is the discipline of building and running an internal product whose users are your own engineers. It takes the infrastructure, delivery, and operational capabilities that every team would otherwise assemble separately, and packages them as self-service interfaces with sensible defaults and guardrails built in. The output is not a set of tools; it is a reduction in the number of decisions a product team has to make to ship safely.

## Detail

**The problem it exists to solve.** The "you build it, you run it" model handed product teams the full operational surface: containers, orchestration, networking, IAM, observability, secrets, cost, compliance. That works for a handful of strong teams and collapses at scale, because every team independently solves the same problems at different quality levels. The result is not autonomy but inconsistency - twelve pipelines, nine logging conventions, and reliability that depends on which engineer happened to set the service up.

**The defining property is self-service.** If getting a database requires filing a ticket that a human picks up, that capability is not part of a platform - it is a service desk with better branding. The working test: can a new engineer go from empty repository to a service running in production, with monitoring, an owner, and backups recorded, without a human approving each step? If not, you have tooling, not a platform.

**It is a product, not a project.** A platform has users who can choose not to use it, which means it needs the ordinary apparatus of a product: research into what its users actually struggle with, a roadmap, versioned interfaces, documentation, support, and adoption metrics. Platforms delivered as internal projects tend to ship what the platform team found interesting and get routed around.

**What it is measured on.** Not components shipped. The honest measures are lead time from commit to production, the time a new service takes to reach production, the proportion of services on the supported path, and change failure rate - plus rework rate, which DORA added in 2024 to capture unplanned fixes after a release. Those are outcomes for the platform's users, and they are the numbers an interviewer will push you toward.

**The trade-off.** Every abstraction you add buys convenience and costs flexibility, and you now own a piece of critical infrastructure with its own reliability, upgrade, and support burden. A platform that is not adopted is pure cost. That is why "when should you not build one" is a fair and common question.

## Example

```text
Without a platform - each team assembles the same stack, differently:

  team-payments   Dockerfile + Helm chart + Jenkins + Datadog + hand-rolled IAM
  team-search     Dockerfile + Kustomize + GH Actions + Prometheus + hand-rolled IAM
  team-billing    Dockerfile + Helm chart + GitLab CI + ELK + hand-rolled IAM
                  ^ three answers to every question; reliability varies per team

With a platform - one supported path, teams declare intent:

  service.yaml  ->  platform  ->  pipeline, image build, deploy, DNS, TLS,
  (20 lines)                      dashboards, alerts, SLO, backups, budget,
                                  audit trail, on-call routing
                  ^ one answer, applied consistently; teams opt out deliberately
```

## Interview tips

- Define it by self-service and by having users - a tool list ("we use Kubernetes, Terraform, and Argo CD") is the weak answer and interviewers hear it constantly.
- Have a one-sentence contrast ready with DevOps and SRE; it is almost always the immediate follow-up.
- Name a metric. Saying you would measure lead time and the share of services on the golden path signals you have run a platform rather than read about one.
- Be ready for "when is a platform the wrong investment?" - small organisations with one deployment target should buy a good pipeline and a template repository instead.

---

[⬅ Back to Platform Engineering Fundamentals](./README.md) · [All topics](../README.md)
