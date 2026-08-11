---
title: "What is an internal developer platform?"
id: 2
category: "Platform Engineering Fundamentals"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-engineering-fundamentals
  - interview-questions
---

# What is an internal developer platform?

**Short answer:** An internal developer platform (IDP) is the curated set of self-service capabilities a product team uses to build, deploy, and run software without filing tickets - scaffolding, CI/CD, environments, infrastructure provisioning, secrets, observability, and the guardrails around them. It is the concrete artefact that platform engineering produces, and it is defined by its interfaces rather than by the tools sitting behind them.

## Detail

**The planes it is usually described in.** This decomposition is the standard way to answer "what is in it", and it stops the answer becoming a tool list:

| Plane                    | Contains                                                            |
| ------------------------ | ------------------------------------------------------------------- |
| Developer control        | portal, CLI, or Git as the interface developers actually touch      |
| Integration and delivery | CI/CD, image build, GitOps reconciliation, environment provisioning |
| Resource                 | Kubernetes, cloud accounts, databases, queues, caches               |
| Monitoring               | metrics, logs, traces, SLOs, cost visibility                        |
| Security                 | identity, secrets, policy, image signing and verification           |

**The interface is the product.** Developers experience the platform through whatever they touch - a `service.yaml` in their repo, a `platform` CLI, a portal form, or a pull request template. Everything behind that is implementation detail you should be free to replace. Teams that expose Kubernetes manifests directly have not built a platform interface; they have added a shared cluster.

**Three common interface shapes**, and they compose rather than compete:

- **Git as the interface.** A declarative file in the service repository, reconciled by a controller. Cheapest to build, reviewable, works with existing habits, and is where most platforms should start.
- **CLI.** Good for scaffolding, local workflows, and one-off operations - `platform create service`, `platform env open`.
- **Portal.** Best for discovery, ownership, catalogues, and scorecards. Weakest as the primary path for routine changes, because a form submission is not reviewable or diffable.

**What it replaces.** Ticket-driven operations, per-team snowflake pipelines, and the situation where each service's reliability depends on which engineer set it up. The business case is cycle time and consistency: compliant logging, backups, tagging, and alerting arrive by default rather than by discipline.

**What it is not.** Not a Backstage instance - a portal without provisioning behind it is a catalogue. Not a wiki page listing approved tools. Not a Kubernetes cluster with namespaces handed out. Each of these is a common thing organisations call an IDP, and naming that gap is a strong interview move.

## Example

```yaml
# The developer-facing contract: a small, reviewable spec that yields a
# running service - monitored, owned, and compliant - with no tickets between.
apiVersion: platform.example.com/v1
kind: Service
metadata:
  name: checkout
spec:
  owner: team-payments # drives on-call routing and catalogue ownership
  tier: 1 # tier drives SLO defaults, backup policy, review requirements
  runtime:
    image: ghcr.io/example/checkout
    port: 8080
    resources: { cpu: 500m, memory: 512Mi }
    scaling: { min: 3, max: 30, metric: rps, target: 800 }
  dependencies:
    - postgres: { size: small, backups: daily, pitr: true }
    - queue: { name: orders, dlq: true }
  observability:
    slo: { availability: 99.9, latency: { threshold: 300ms, percentile: 99 } }
  network:
    ingress: internal
```

## Interview tips

- Lead with self-service and with the interface, then use the five planes to show breadth. Naming the planes reliably reads as experience.
- "The interface is the product, the tools are implementation detail" is the sentence that separates a strong answer from a memorised one.
- Expect "so is Backstage an IDP?" - no, it is a possible developer control plane; without provisioning behind it, it is a service catalogue.
- Have a concrete example of the developer-facing contract in your head. Being able to sketch the 20-line spec is far more convincing than describing it.

---

[⬅ Back to Platform Engineering Fundamentals](./README.md) · [All topics](../README.md)
