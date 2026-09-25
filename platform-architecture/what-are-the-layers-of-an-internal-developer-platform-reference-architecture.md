---
title: "What are the layers of an internal developer platform reference architecture?"
id: 29
category: "Platform Architecture"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-architecture
  - interview-questions
---

# What are the layers of an internal developer platform reference architecture?

**Short answer:** A common way to draw an internal developer platform is as five layers, often called planes: a developer-facing layer (portal, CLI, service specification, templates), an integration and delivery layer (CI, registry, GitOps, orchestration of the platform's own logic), a resource layer (clusters, databases, queues, networks), an observability layer, and a security layer that cuts across the rest. The value of the model is not the boxes - it is that each layer has a clear owner, a clear interface to the next, and can be swapped without rewriting the layers above it.

## Detail

**Where the model comes from.** There is no single standard, but most published reference architectures converge on the same shape. The platformengineering.org community reference architectures use five planes - developer control, integration and delivery, resource, monitoring and logging, and security - and the CNCF Platforms white paper lists the same capabilities (portals, APIs, templates, build and delivery automation, infrastructure and data services, observability, identity and secrets) without prescribing a vendor for any of them. Knowing that it is a convention, not a specification, is part of a good answer.

**1. Developer control plane - what developers touch.** The portal or service catalogue, the CLI, golden path templates, and above all the service specification: the file in a team's repository that says "this is a tier-2 service with a small Postgres". This layer is the platform's product surface. Everything a developer needs to do daily should be possible here without learning the layers below.

**2. Integration and delivery plane - what turns intent into running software.** CI pipelines, the artefact registry, signing and attestation, the GitOps reconciler, and the platform orchestrator or controllers that read the service specification and generate the environment-specific configuration. This is where most platform logic lives: applying defaults, choosing the right cluster, wiring dependencies.

**3. Resource plane - where things actually run.** Kubernetes clusters, managed databases, queues, buckets, DNS, networking. Provisioned through infrastructure as code or a Kubernetes-native control plane such as Crossplane. Developers should rarely address this layer directly; they ask for "a queue" and the delivery plane decides what that means.

**4. Monitoring and logging plane - how everyone sees what is happening.** Metrics, logs, traces, and increasingly profiles, usually collected through OpenTelemetry and routed to shared backends. The platform's job here is that every service gets useful telemetry, dashboards, and SLO alerting without writing code.

**5. Security plane - cross-cutting controls.** Identity (workload identity, SSO), secrets management, policy enforcement at admission and in CI, supply-chain verification. It is drawn as a separate plane because it touches every other one; in practice it is embedded at each layer's boundary.

**Who the layers serve.** The application developer mostly sees only layer 1 and the dashboards in layer 4. Platform engineers work across layers 2-5. Security and compliance teams consume the evidence produced by layer 5. Drawing the architecture this way makes it obvious which audience each capability is built for.

**Why the layering matters in practice.**

- **Replaceability.** If the service specification in layer 1 is independent of the tools in layers 2 and 3, you can swap a CI system or a cloud database offering without touching forty repositories.
- **Ownership.** Each layer can have a named owning team and its own roadmap.
- **Failure reasoning.** Layers 1 and 2 are mostly control plane - if they fail, deploys stop. Layers 3 and parts of 5 are in the request path - if they fail, customers notice. See [control plane versus data plane](./what-is-the-difference-between-a-control-plane-and-a-data-plane-in-a-platform.md).

**Trade-offs and limits.** A five-layer diagram can become an excuse to build five layers before shipping anything; the [thinnest viable platform](../platform-engineering-fundamentals/what-is-the-thinnest-viable-platform.md) is often a wiki page, a template, and a pipeline. Layers also leak: a slow database in layer 3 is still the developer's problem, so the layer-1 interface has to surface lower-layer state honestly. Finally, the layers are logical, not products - one tool such as Backstage or Argo CD may span two of them.

## Example

```text
One request, traced through the layers. A developer on the payments team
needs a new service with a database.

  LAYER                         WHAT HAPPENS                        TOOLS (examples)
  1 Developer control plane     picks "Go HTTP service" template;   Backstage, CLI,
                                repo created with service.yaml      service spec
                                (tier: 2, postgres: small)
          |
  2 Integration and delivery    CI builds, signs the image;         GitHub Actions,
                                orchestrator renders manifests;     cosign, Argo CD
                                GitOps syncs to the target cluster
          |
  3 Resource plane              namespace, Deployment created;      Kubernetes,
                                Postgres provisioned in the         Crossplane,
                                team's account                      managed Postgres
          |
  4 Monitoring and logging      OTel auto-instrumentation, default  OpenTelemetry,
                                dashboard, SLO burn-rate alerts     Prometheus, Grafana
          |
  5 Security (at every step)    template passes policy checks;      OIDC, Kyverno,
                                image signature verified at         External Secrets,
                                admission; DB credentials injected  workload identity
                                via workload identity, never pasted

  What the developer wrote: one template choice and a 15-line service.yaml.
  What they saw: layer 1 and the dashboard from layer 4.
```

## Interview tips

- Name the five planes, then say straight away that it is a convention, not a standard. That shows you have read more than one diagram.
- Put the service specification at the centre of layer 1 - it is the interface that keeps the lower layers swappable. That is the architectural point interviewers are looking for.
- Say who uses each layer. An answer that lists tools without saying the developer only sees two layers misses the product view.
- Link layers to failure modes: control-plane layers stop deploys, data-plane layers stop customers.
- Expect "would you build all of this first?" - the answer is no; start thin and add layers as demand proves them.

---

[⬅ Back to Platform Architecture](./README.md) · [All topics](../README.md)
