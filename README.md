<div align="center">

# 🛠️ Ultimate Platform Engineering Guide

**262 questions across 20 topics - answered to the depth an interviewer actually expects.**

Role tracks: **Platform Engineer** (junior → staff) · **DevEx** · **Platform Architect** · **Kubernetes Platform** · **Platform Security** · **Platform SRE** · **AWS** · **Azure** · **GCP** · **FinOps** · **Platform Lead**

Every answer gives you a short answer you can say out loud, the detail and trade-offs behind it, a runnable example, and the follow-ups to expect.

[![Validate](https://github.com/mchittineni/ultimate-platform-engineering-guide/actions/workflows/validate-and-format.yml/badge.svg)](https://github.com/mchittineni/ultimate-platform-engineering-guide/actions/workflows/validate-and-format.yml)
![Questions](https://img.shields.io/badge/questions-262-blue)
![Topics](https://img.shields.io/badge/topics-20-blueviolet)
![Difficulty](https://img.shields.io/badge/difficulty-🟢%2011%20·%20🟡%2056%20·%20🔴%2069-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

[Pick your role](#-pick-your-role) · [Browse topics](#-browse-all-topics) · [All questions](#-all-questions) · [Knowledge graph](#-the-knowledge-graph) · [How answers are structured](#-how-answers-are-structured) · [Contributing](./CONTRIBUTING.md)

**[🌌 Explore the knowledge graph →](https://mchittineni.github.io/ultimate-platform-engineering-guide/)** - all 262 questions as a live map of the concepts they share.

⭐ Star the project if it helps you land the role.

</div>

---

## 🎯 What this guide is

Platform engineering interviews are not infrastructure interviews with a new title. They probe a specific set of judgements: whether you can design an interface other engineers will voluntarily use, where you put a guardrail versus a golden path, how you version a contract forty teams depend on, and how you know whether any of it worked.

This guide is organised around those judgements. It assumes you already know what a Pod is, and spends its pages on the decisions above that line - tenancy boundaries, control-plane design, escapable abstractions, rollout policy, cost attribution, and the operating model of a team whose customers are other engineers.

> **New to the field, or moving in from DevOps or SRE?** Start with [Platform Engineering Fundamentals](./platform-engineering-fundamentals/README.md), then [Developer Experience](./developer-experience/README.md). The vocabulary in those two topics is assumed by everything else.

---

## 🚀 Pick your role

Eleven tracks, each a reading order rather than a pile of links. Start at the left and work right.

> **Interview in a fortnight?** Start with [Platform Engineering Interviews](./platform-engineering-interviews/README.md) - it covers the loop structure, the platform design round, how to present work you have done, and what to ask back, cross-linked to the rest of the guide.

| 🎯 Target role               | Read in this order                                                                                                                                                                                                                                                                                                            |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Interviewing now**         | [Interviews](./platform-engineering-interviews/README.md) → [Fundamentals](./platform-engineering-fundamentals/README.md) → [Architecture](./platform-architecture/README.md) → [Kubernetes Platform](./kubernetes-platform/README.md) → [GitOps](./gitops-and-continuous-delivery/README.md)                                 |
| **Junior / Associate**       | [Fundamentals](./platform-engineering-fundamentals/README.md) → [Developer Experience](./developer-experience/README.md) → [Kubernetes Platform](./kubernetes-platform/README.md) → [GitOps](./gitops-and-continuous-delivery/README.md) → [Environments](./environments-and-ephemeral-infrastructure/README.md)              |
| **Senior Platform Engineer** | [Architecture](./platform-architecture/README.md) → [Control Planes](./control-planes-and-abstractions/README.md) → [Multi-Tenancy](./multi-tenancy-and-isolation/README.md) → [Reliability](./platform-reliability/README.md) → [Security](./platform-security/README.md)                                                    |
| **Platform Architect**       | [Architecture](./platform-architecture/README.md) → [Multi-Tenancy](./multi-tenancy-and-isolation/README.md) → [Control Planes](./control-planes-and-abstractions/README.md) → [Multi-Cloud](./multi-cloud-and-hybrid-platforms/README.md) → [Governance](./policy-as-code-and-governance/README.md)                          |
| **Developer Experience**     | [Developer Experience](./developer-experience/README.md) → [Fundamentals](./platform-engineering-fundamentals/README.md) → [Environments](./environments-and-ephemeral-infrastructure/README.md) → [GitOps](./gitops-and-continuous-delivery/README.md) → [Operating Model](./platform-team-and-operating-model/README.md)    |
| **Kubernetes Platform**      | [Kubernetes Platform](./kubernetes-platform/README.md) → [Control Planes](./control-planes-and-abstractions/README.md) → [Multi-Tenancy](./multi-tenancy-and-isolation/README.md) → [GitOps](./gitops-and-continuous-delivery/README.md) → [Governance](./policy-as-code-and-governance/README.md)                            |
| **Platform Security**        | [Security](./platform-security/README.md) → [Governance](./policy-as-code-and-governance/README.md) → [Multi-Tenancy](./multi-tenancy-and-isolation/README.md) → [Control Planes](./control-planes-and-abstractions/README.md) → [Observability](./platform-observability/README.md)                                          |
| **Platform SRE**             | [Reliability](./platform-reliability/README.md) → [Observability](./platform-observability/README.md) → [Progressive Delivery](./progressive-delivery-and-feature-flags/README.md) → [Kubernetes Platform](./kubernetes-platform/README.md) → [Multi-Tenancy](./multi-tenancy-and-isolation/README.md)                        |
| **AWS Platform Engineer**    | [AWS](./aws-platform-engineering/README.md) → [Control Planes](./control-planes-and-abstractions/README.md) → [Security](./platform-security/README.md) → [Kubernetes Platform](./kubernetes-platform/README.md) → [FinOps](./platform-finops/README.md)                                                                      |
| **Azure / GCP Platform**     | [Azure](./azure-platform-engineering/README.md) · [GCP](./gcp-platform-engineering/README.md) → [Control Planes](./control-planes-and-abstractions/README.md) → [Governance](./policy-as-code-and-governance/README.md) → [Multi-Cloud](./multi-cloud-and-hybrid-platforms/README.md) → [FinOps](./platform-finops/README.md) |
| **Platform Lead / Staff+**   | [Operating Model](./platform-team-and-operating-model/README.md) → [FinOps](./platform-finops/README.md) → [Fundamentals](./platform-engineering-fundamentals/README.md) → [Architecture](./platform-architecture/README.md) → [Reliability](./platform-reliability/README.md)                                                |

---

## 📚 Browse all topics

Grouped by theme, with question counts and difficulty mix. Click a topic to open its index, which opens with what interviewers probe there.

<!-- STATS:START -->

**262 questions** across **20 topics** - 🟢 100 Beginner · 🟡 82 Intermediate · 🔴 80 Advanced

### 🧱 Platform Foundations

| Topic                                                                                  | Questions | 🟢  | 🟡  | 🔴  | What it covers                                                                                  |
| -------------------------------------------------------------------------------------- | --------- | --- | --- | --- | ----------------------------------------------------------------------------------------------- |
| **[Platform Engineering Fundamentals](./platform-engineering-fundamentals/README.md)** | 13        | 5   | 5   | 3   | what a platform actually is, why self-service is the defining property, and where platform…     |
| **[Developer Experience](./developer-experience/README.md)**                           | 13        | 5   | 6   | 2   | cognitive load, service catalogues, portals, scorecards, onboarding time, and the metrics that… |

### 🏗️ Platform Architecture

| Topic                                                                      | Questions | 🟢  | 🟡  | 🔴  | What it covers                                                                                |
| -------------------------------------------------------------------------- | --------- | --- | --- | --- | --------------------------------------------------------------------------------------------- |
| **[Platform Architecture](./platform-architecture/README.md)**             | 13        | 5   | 4   | 4   | control plane versus data plane, the developer-facing API, escapable abstractions, interface… |
| **[Multi-Tenancy and Isolation](./multi-tenancy-and-isolation/README.md)** | 13        | 5   | 4   | 4   | tenancy models, namespace versus cluster boundaries, noisy neighbours, quotas, network…       |

### ☸️ Kubernetes and Control Planes

| Topic                                                                              | Questions | 🟢  | 🟡  | 🔴  | What it covers                                                                                    |
| ---------------------------------------------------------------------------------- | --------- | --- | --- | --- | ------------------------------------------------------------------------------------------------- |
| **[Kubernetes Platform](./kubernetes-platform/README.md)**                         | 13        | 5   | 3   | 5   | cluster topology, node pools and scheduling, fleet upgrades, admission control as a platform…     |
| **[Control Planes and Abstractions](./control-planes-and-abstractions/README.md)** | 13        | 5   | 3   | 5   | Crossplane, custom resources as platform contracts, workload specifications, Terraform at scale,… |

### 🔁 Delivery and Progressive Rollout

| Topic                                                                                                  | Questions | 🟢  | 🟡  | 🔴  | What it covers                                                                               |
| ------------------------------------------------------------------------------------------------------ | --------- | --- | --- | --- | -------------------------------------------------------------------------------------------- |
| **[GitOps and Continuous Delivery](./gitops-and-continuous-delivery/README.md)**                       | 13        | 5   | 5   | 3   | Argo CD and Flux, repository structure at scale, environment promotion, secrets, drift…      |
| **[Progressive Delivery and Feature Flags](./progressive-delivery-and-feature-flags/README.md)**       | 14        | 5   | 3   | 6   | flags as a platform capability, flag debt and its SLAs, rollout curves with abort criteria,… |
| **[Environments and Ephemeral Infrastructure](./environments-and-ephemeral-infrastructure/README.md)** | 13        | 5   | 5   | 3   | preview environments per pull request, data seeding without leaking production, environment… |

### 🔐 Security and Governance

| Topic                                                                          | Questions | 🟢  | 🟡  | 🔴  | What it covers                                                                               |
| ------------------------------------------------------------------------------ | --------- | --- | --- | --- | -------------------------------------------------------------------------------------------- |
| **[Platform Security](./platform-security/README.md)**                         | 14        | 5   | 3   | 6   | workload identity without long-lived keys, secretless pipelines, secrets management,…        |
| **[Policy as Code and Governance](./policy-as-code-and-governance/README.md)** | 13        | 5   | 5   | 3   | OPA and Kyverno, rolling out policy without breaking teams, compliance frameworks mapped to… |

### ☁️ Cloud Platforms

| Topic                                                                                | Questions | 🟢  | 🟡  | 🔴  | What it covers                                                                                |
| ------------------------------------------------------------------------------------ | --------- | --- | --- | --- | --------------------------------------------------------------------------------------------- |
| **[AWS Platform Engineering](./aws-platform-engineering/README.md)**                 | 13        | 5   | 4   | 4   | multi-account organisation design, account vending, EKS pod identity, runtime selection,…     |
| **[Azure Platform Engineering](./azure-platform-engineering/README.md)**             | 13        | 5   | 4   | 4   | management groups and landing zones, Azure Policy guardrails, AKS workload identity, runtime… |
| **[GCP Platform Engineering](./gcp-platform-engineering/README.md)**                 | 13        | 5   | 4   | 4   | the folder and project hierarchy, organisation policies, Workload Identity Federation, GKE…   |
| **[Multi-Cloud and Hybrid Platforms](./multi-cloud-and-hybrid-platforms/README.md)** | 13        | 5   | 4   | 4   | genuine drivers versus slogans, the cost of portable abstractions, cross-provider primitive…  |

### 📈 Reliability and Observability

| Topic                                                            | Questions | 🟢  | 🟡  | 🔴  | What it covers                                                                                  |
| ---------------------------------------------------------------- | --------- | --- | --- | --- | ----------------------------------------------------------------------------------------------- |
| **[Platform Reliability](./platform-reliability/README.md)**     | 13        | 5   | 3   | 5   | SLOs for a platform rather than an app, error budget policy, platform on-call, incidents where… |
| **[Platform Observability](./platform-observability/README.md)** | 13        | 5   | 4   | 4   | OpenTelemetry collectors as shared infrastructure, cardinality and cost control, zero-effort…   |

### 💰 Economics and Operating Model

| Topic                                                                                  | Questions | 🟢  | 🟡  | 🔴  | What it covers                                                                                  |
| -------------------------------------------------------------------------------------- | --------- | --- | --- | --- | ----------------------------------------------------------------------------------------------- |
| **[Platform FinOps](./platform-finops/README.md)**                                     | 13        | 5   | 4   | 4   | cost attribution for shared infrastructure, showback versus chargeback, unit economics,…        |
| **[Platform Team and Operating Model](./platform-team-and-operating-model/README.md)** | 13        | 5   | 4   | 4   | Team Topologies, staffing, adoption metrics, migration without a mandate, deprecation, the RFC… |

### 🎤 Interview Prep

| Topic                                                                              | Questions | 🟢  | 🟡  | 🔴  | What it covers                                                                     |
| ---------------------------------------------------------------------------------- | --------- | --- | --- | --- | ---------------------------------------------------------------------------------- |
| **[Platform Engineering Interviews](./platform-engineering-interviews/README.md)** | 13        | 5   | 5   | 3   | the loop structure, the platform design round, presenting your own platform work,… |

<!-- STATS:END -->

---

## 📋 All questions

Every question in the repository, collapsed by topic - open only the ones you are studying.

<!-- TOC:START -->

### 🧱 Platform Foundations

_26 questions_

<details>
<summary><b>Platform Engineering Fundamentals</b> · 13 questions · 🟢 5 🟡 5 🔴 3</summary>

[Open the Platform Engineering Fundamentals index →](./platform-engineering-fundamentals/README.md)

| No. | Question                                                                                                                                                                                                 | Difficulty      |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 1   | [What is platform engineering?](./platform-engineering-fundamentals/what-is-platform-engineering.md)                                                                                                     | 🟢 Beginner     |
| 2   | [What is an internal developer platform?](./platform-engineering-fundamentals/what-is-an-internal-developer-platform.md)                                                                                 | 🟢 Beginner     |
| 3   | [How is platform engineering different from DevOps and SRE?](./platform-engineering-fundamentals/how-is-platform-engineering-different-from-devops-and-sre.md)                                           | 🟢 Beginner     |
| 4   | [What is self-service and why is it the defining property of a platform?](./platform-engineering-fundamentals/what-is-self-service-and-why-is-it-the-defining-property-of-a-platform.md)                 | 🟢 Beginner     |
| 5   | [What is the difference between a platform and a collection of tools?](./platform-engineering-fundamentals/what-is-the-difference-between-a-platform-and-a-collection-of-tools.md)                       | 🟢 Beginner     |
| 6   | [What is a golden path and how does it differ from a mandate?](./platform-engineering-fundamentals/what-is-a-golden-path-and-how-does-it-differ-from-a-mandate.md)                                       | 🟡 Intermediate |
| 7   | [What is the thinnest viable platform?](./platform-engineering-fundamentals/what-is-the-thinnest-viable-platform.md)                                                                                     | 🟡 Intermediate |
| 8   | [How do you decide whether your organisation needs a platform team?](./platform-engineering-fundamentals/how-do-you-decide-whether-your-organisation-needs-a-platform-team.md)                           | 🟡 Intermediate |
| 9   | [What is the CNCF platform engineering maturity model and how do you use it?](./platform-engineering-fundamentals/what-is-the-cncf-platform-engineering-maturity-model-and-how-do-you-use-it.md)         | 🟡 Intermediate |
| 10  | [What are platform capabilities and how do you decide which ones to offer first?](./platform-engineering-fundamentals/what-are-platform-capabilities-and-how-do-you-decide-which-ones-to-offer-first.md) | 🟡 Intermediate |
| 11  | [What does it mean to run a platform as a product?](./platform-engineering-fundamentals/what-does-it-mean-to-run-a-platform-as-a-product.md)                                                             | 🔴 Advanced     |
| 12  | [What are the most common ways platform initiatives fail?](./platform-engineering-fundamentals/what-are-the-most-common-ways-platform-initiatives-fail.md)                                               | 🔴 Advanced     |
| 13  | [How do AI coding agents change what a platform must provide?](./platform-engineering-fundamentals/how-do-ai-coding-agents-change-what-a-platform-must-provide.md)                                       | 🔴 Advanced     |

</details>

<details>
<summary><b>Developer Experience</b> · 13 questions · 🟢 5 🟡 6 🔴 2</summary>

[Open the Developer Experience index →](./developer-experience/README.md)

| No. | Question                                                                                                                                                                            | Difficulty      |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 14  | [How do you run documentation as a platform capability?](./developer-experience/how-do-you-run-documentation-as-a-platform-capability.md)                                           | 🟢 Beginner     |
| 15  | [What is a developer portal and how does it differ from the platform?](./developer-experience/what-is-a-developer-portal-and-how-does-it-differ-from-the-platform.md)               | 🟢 Beginner     |
| 16  | [What are the DORA metrics and what do they measure?](./developer-experience/what-are-the-dora-metrics-and-what-do-they-measure.md)                                                 | 🟢 Beginner     |
| 17  | [What is a software template and how does scaffolding work?](./developer-experience/what-is-a-software-template-and-how-does-scaffolding-work.md)                                   | 🟢 Beginner     |
| 18  | [How do you find out where developers lose time?](./developer-experience/how-do-you-find-out-where-developers-lose-time.md)                                                         | 🟢 Beginner     |
| 19  | [What is developer experience and how do you measure it?](./developer-experience/what-is-developer-experience-and-how-do-you-measure-it.md)                                         | 🟡 Intermediate |
| 20  | [What is cognitive load and why does it drive platform design?](./developer-experience/what-is-cognitive-load-and-why-does-it-drive-platform-design.md)                             | 🟡 Intermediate |
| 21  | [What is a service catalogue and why does a platform need one?](./developer-experience/what-is-a-service-catalogue-and-why-does-a-platform-need-one.md)                             | 🟡 Intermediate |
| 22  | [What is Backstage and when is it the wrong choice?](./developer-experience/what-is-backstage-and-when-is-it-the-wrong-choice.md)                                                   | 🟡 Intermediate |
| 23  | [How do you reduce the time it takes a new engineer to ship to production?](./developer-experience/how-do-you-reduce-the-time-it-takes-a-new-engineer-to-ship-to-production.md)     | 🟡 Intermediate |
| 24  | [How do SPACE, DevEx, and DX Core 4 differ as measurement frameworks?](./developer-experience/how-do-space-devex-and-dx-core-4-differ-as-measurement-frameworks.md)                 | 🟡 Intermediate |
| 25  | [How do you design service scorecards that teams do not resent?](./developer-experience/how-do-you-design-service-scorecards-that-teams-do-not-resent.md)                           | 🔴 Advanced     |
| 26  | [How do you measure the impact of AI coding tools on developer productivity?](./developer-experience/how-do-you-measure-the-impact-of-ai-coding-tools-on-developer-productivity.md) | 🔴 Advanced     |

</details>

### 🏗️ Platform Architecture

_26 questions_

<details>
<summary><b>Platform Architecture</b> · 13 questions · 🟢 5 🟡 4 🔴 4</summary>

[Open the Platform Architecture index →](./platform-architecture/README.md)

| No. | Question                                                                                                                                                                                   | Difficulty      |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------- |
| 27  | [How do you write an architecture decision record for a platform choice?](./platform-architecture/how-do-you-write-an-architecture-decision-record-for-a-platform-choice.md)               | 🟢 Beginner     |
| 28  | [What is the difference between declarative and imperative configuration?](./platform-architecture/what-is-the-difference-between-declarative-and-imperative-configuration.md)             | 🟢 Beginner     |
| 29  | [What are the layers of an internal developer platform reference architecture?](./platform-architecture/what-are-the-layers-of-an-internal-developer-platform-reference-architecture.md)   | 🟢 Beginner     |
| 30  | [What is idempotency and why do platform APIs need it?](./platform-architecture/what-is-idempotency-and-why-do-platform-apis-need-it.md)                                                   | 🟢 Beginner     |
| 31  | [What is a leaky abstraction and why do platform teams worry about it?](./platform-architecture/what-is-a-leaky-abstraction-and-why-do-platform-teams-worry-about-it.md)                   | 🟢 Beginner     |
| 32  | [What is the difference between a control plane and a data plane in a platform?](./platform-architecture/what-is-the-difference-between-a-control-plane-and-a-data-plane-in-a-platform.md) | 🟡 Intermediate |
| 33  | [When should a platform capability be a service, a library, or a template?](./platform-architecture/when-should-a-platform-capability-be-a-service-a-library-or-a-template.md)             | 🟡 Intermediate |
| 34  | [How do you choose a datastore for a platform service?](./platform-architecture/how-do-you-choose-a-datastore-for-a-platform-service.md)                                                   | 🟡 Intermediate |
| 35  | [How do you use events to integrate platform components?](./platform-architecture/how-do-you-use-events-to-integrate-platform-components.md)                                               | 🟡 Intermediate |
| 36  | [How do you design the developer-facing API of a platform?](./platform-architecture/how-do-you-design-the-developer-facing-api-of-a-platform.md)                                           | 🔴 Advanced     |
| 37  | [How do you keep a platform abstraction escapable?](./platform-architecture/how-do-you-keep-a-platform-abstraction-escapable.md)                                                           | 🔴 Advanced     |
| 38  | [How do you version a platform interface and migrate consumers?](./platform-architecture/how-do-you-version-a-platform-interface-and-migrate-consumers.md)                                 | 🔴 Advanced     |
| 39  | [How do you decide whether to build or buy a platform capability?](./platform-architecture/how-do-you-decide-whether-to-build-or-buy-a-platform-capability.md)                             | 🔴 Advanced     |

</details>

<details>
<summary><b>Multi-Tenancy and Isolation</b> · 13 questions · 🟢 5 🟡 4 🔴 4</summary>

[Open the Multi-Tenancy and Isolation index →](./multi-tenancy-and-isolation/README.md)

| No. | Question                                                                                                                                                               | Difficulty      |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 40  | [What is multi-tenancy and why do platforms need it?](./multi-tenancy-and-isolation/what-is-multi-tenancy-and-why-do-platforms-need-it.md)                             | 🟢 Beginner     |
| 41  | [What is a tenant, and how do you define one in a platform?](./multi-tenancy-and-isolation/what-is-a-tenant-and-how-do-you-define-one-in-a-platform.md)                | 🟢 Beginner     |
| 42  | [What does a Kubernetes namespace isolate, and what does it not?](./multi-tenancy-and-isolation/what-does-a-kubernetes-namespace-isolate-and-what-does-it-not.md)      | 🟢 Beginner     |
| 43  | [What are resource quotas and limit ranges?](./multi-tenancy-and-isolation/what-are-resource-quotas-and-limit-ranges.md)                                               | 🟢 Beginner     |
| 44  | [How does role-based access control scope what a tenant can do?](./multi-tenancy-and-isolation/how-does-role-based-access-control-scope-what-a-tenant-can-do.md)       | 🟢 Beginner     |
| 45  | [What tenancy models can a platform offer?](./multi-tenancy-and-isolation/what-tenancy-models-can-a-platform-offer.md)                                                 | 🟡 Intermediate |
| 46  | [How do you isolate tenants at the network layer?](./multi-tenancy-and-isolation/how-do-you-isolate-tenants-at-the-network-layer.md)                                   | 🟡 Intermediate |
| 47  | [How do virtual clusters change the tenancy trade-off?](./multi-tenancy-and-isolation/how-do-virtual-clusters-change-the-tenancy-trade-off.md)                         | 🟡 Intermediate |
| 48  | [How do Pod Security Standards harden a shared cluster?](./multi-tenancy-and-isolation/how-do-pod-security-standards-harden-a-shared-cluster.md)                       | 🟡 Intermediate |
| 49  | [When do you give a tenant its own cluster instead of a namespace?](./multi-tenancy-and-isolation/when-do-you-give-a-tenant-its-own-cluster-instead-of-a-namespace.md) | 🔴 Advanced     |
| 50  | [How do you stop one tenant degrading another?](./multi-tenancy-and-isolation/how-do-you-stop-one-tenant-degrading-another.md)                                         | 🔴 Advanced     |
| 51  | [How do you isolate tenant identity and data?](./multi-tenancy-and-isolation/how-do-you-isolate-tenant-identity-and-data.md)                                           | 🔴 Advanced     |
| 52  | [How do you design tenant onboarding and offboarding?](./multi-tenancy-and-isolation/how-do-you-design-tenant-onboarding-and-offboarding.md)                           | 🔴 Advanced     |

</details>

### ☸️ Kubernetes and Control Planes

_26 questions_

<details>
<summary><b>Kubernetes Platform</b> · 13 questions · 🟢 5 🟡 3 🔴 5</summary>

[Open the Kubernetes Platform index →](./kubernetes-platform/README.md)

| No. | Question                                                                                                                                                                            | Difficulty      |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 53  | [Why does Kubernetes end up as the substrate for most platforms?](./kubernetes-platform/why-does-kubernetes-end-up-as-the-substrate-for-most-platforms.md)                          | 🟢 Beginner     |
| 54  | [What is the difference between a Deployment, a StatefulSet, and a DaemonSet?](./kubernetes-platform/what-is-the-difference-between-a-deployment-a-statefulset-and-a-daemonset.md)  | 🟢 Beginner     |
| 55  | [What are resource requests and limits, and why does a platform set defaults?](./kubernetes-platform/what-are-resource-requests-and-limits-and-why-does-a-platform-set-defaults.md) | 🟢 Beginner     |
| 56  | [What is the Gateway API and why is it replacing Ingress?](./kubernetes-platform/what-is-the-gateway-api-and-why-is-it-replacing-ingress.md)                                        | 🟢 Beginner     |
| 57  | [What are liveness, readiness, and startup probes?](./kubernetes-platform/what-are-liveness-readiness-and-startup-probes.md)                                                        | 🟢 Beginner     |
| 58  | [How do you design node pools and scheduling for mixed workloads?](./kubernetes-platform/how-do-you-design-node-pools-and-scheduling-for-mixed-workloads.md)                        | 🟡 Intermediate |
| 59  | [What is admission control and how do you use it as a platform lever?](./kubernetes-platform/what-is-admission-control-and-how-do-you-use-it-as-a-platform-lever.md)                | 🟡 Intermediate |
| 60  | [How do you run GPU and AI workloads on a Kubernetes platform?](./kubernetes-platform/how-do-you-run-gpu-and-ai-workloads-on-a-kubernetes-platform.md)                              | 🟡 Intermediate |
| 61  | [How do you design cluster topology for a platform?](./kubernetes-platform/how-do-you-design-cluster-topology-for-a-platform.md)                                                    | 🔴 Advanced     |
| 62  | [How do you upgrade a fleet of clusters without breaking tenants?](./kubernetes-platform/how-do-you-upgrade-a-fleet-of-clusters-without-breaking-tenants.md)                        | 🔴 Advanced     |
| 63  | [When should you write a Kubernetes operator?](./kubernetes-platform/when-should-you-write-a-kubernetes-operator.md)                                                                | 🔴 Advanced     |
| 64  | [How do you run a service mesh as a platform capability?](./kubernetes-platform/how-do-you-run-a-service-mesh-as-a-platform-capability.md)                                          | 🔴 Advanced     |
| 65  | [How do you keep platform components consistent across many clusters?](./kubernetes-platform/how-do-you-keep-platform-components-consistent-across-many-clusters.md)                | 🔴 Advanced     |

</details>

<details>
<summary><b>Control Planes and Abstractions</b> · 13 questions · 🟢 5 🟡 3 🔴 5</summary>

[Open the Control Planes and Abstractions index →](./control-planes-and-abstractions/README.md)

| No. | Question                                                                                                                                                                                                           | Difficulty      |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------- |
| 66  | [What is infrastructure as code?](./control-planes-and-abstractions/what-is-infrastructure-as-code.md)                                                                                                             | 🟢 Beginner     |
| 67  | [What is a reconciliation loop?](./control-planes-and-abstractions/what-is-a-reconciliation-loop.md)                                                                                                               | 🟢 Beginner     |
| 68  | [What is a custom resource definition?](./control-planes-and-abstractions/what-is-a-custom-resource-definition.md)                                                                                                 | 🟢 Beginner     |
| 69  | [What is the difference between Terraform and OpenTofu?](./control-planes-and-abstractions/what-is-the-difference-between-terraform-and-opentofu.md)                                                               | 🟢 Beginner     |
| 70  | [What is Terraform state and why does it need protecting?](./control-planes-and-abstractions/what-is-terraform-state-and-why-does-it-need-protecting.md)                                                           | 🟢 Beginner     |
| 71  | [What problem does a workload specification like Score solve?](./control-planes-and-abstractions/what-problem-does-a-workload-specification-like-score-solve.md)                                                   | 🟡 Intermediate |
| 72  | [What changed in Crossplane v2 and why does it matter?](./control-planes-and-abstractions/what-changed-in-crossplane-v2-and-why-does-it-matter.md)                                                                 | 🟡 Intermediate |
| 73  | [How do kro, Crossplane compositions, and Helm charts differ for composing resources?](./control-planes-and-abstractions/how-do-kro-crossplane-compositions-and-helm-charts-differ-for-composing-resources.md)     | 🟡 Intermediate |
| 74  | [What is Crossplane and how does it differ from Terraform?](./control-planes-and-abstractions/what-is-crossplane-and-how-does-it-differ-from-terraform.md)                                                         | 🔴 Advanced     |
| 75  | [How do you model a platform API with Kubernetes custom resources?](./control-planes-and-abstractions/how-do-you-model-a-platform-api-with-kubernetes-custom-resources.md)                                         | 🔴 Advanced     |
| 76  | [How do you manage Terraform at platform scale?](./control-planes-and-abstractions/how-do-you-manage-terraform-at-platform-scale.md)                                                                               | 🔴 Advanced     |
| 77  | [How do you handle resource deletion safely in a control plane?](./control-planes-and-abstractions/how-do-you-handle-resource-deletion-safely-in-a-control-plane.md)                                               | 🔴 Advanced     |
| 78  | [How do you provide self-service infrastructure without handing out cloud credentials?](./control-planes-and-abstractions/how-do-you-provide-self-service-infrastructure-without-handing-out-cloud-credentials.md) | 🔴 Advanced     |

</details>

### 🔁 Delivery and Progressive Rollout

_40 questions_

<details>
<summary><b>GitOps and Continuous Delivery</b> · 13 questions · 🟢 5 🟡 5 🔴 3</summary>

[Open the GitOps and Continuous Delivery index →](./gitops-and-continuous-delivery/README.md)

| No. | Question                                                                                                                                                                                                                                          | Difficulty      |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 79  | [What is GitOps and what does it actually guarantee?](./gitops-and-continuous-delivery/what-is-gitops-and-what-does-it-actually-guarantee.md)                                                                                                     | 🟢 Beginner     |
| 80  | [What is the difference between continuous integration, continuous delivery, and continuous deployment?](./gitops-and-continuous-delivery/what-is-the-difference-between-continuous-integration-continuous-delivery-and-continuous-deployment.md) | 🟢 Beginner     |
| 81  | [What is Helm and what problem does it solve?](./gitops-and-continuous-delivery/what-is-helm-and-what-problem-does-it-solve.md)                                                                                                                   | 🟢 Beginner     |
| 82  | [What is Kustomize and how does it differ from Helm?](./gitops-and-continuous-delivery/what-is-kustomize-and-how-does-it-differ-from-helm.md)                                                                                                     | 🟢 Beginner     |
| 83  | [What is the difference between push-based and pull-based deployment?](./gitops-and-continuous-delivery/what-is-the-difference-between-push-based-and-pull-based-deployment.md)                                                                   | 🟢 Beginner     |
| 84  | [How do Argo CD and Flux differ, and how do you choose?](./gitops-and-continuous-delivery/how-do-argo-cd-and-flux-differ-and-how-do-you-choose.md)                                                                                                | 🟡 Intermediate |
| 85  | [How do you handle secrets in a GitOps workflow?](./gitops-and-continuous-delivery/how-do-you-handle-secrets-in-a-gitops-workflow.md)                                                                                                             | 🟡 Intermediate |
| 86  | [What is configuration drift and how does a platform detect it?](./gitops-and-continuous-delivery/what-is-configuration-drift-and-how-does-a-platform-detect-it.md)                                                                               | 🟡 Intermediate |
| 87  | [How do you keep templated manifests reviewable?](./gitops-and-continuous-delivery/how-do-you-keep-templated-manifests-reviewable.md)                                                                                                             | 🟡 Intermediate |
| 88  | [How do you use Argo CD ApplicationSets to manage many clusters?](./gitops-and-continuous-delivery/how-do-you-use-argo-cd-applicationsets-to-manage-many-clusters.md)                                                                             | 🟡 Intermediate |
| 89  | [How do you structure repositories for GitOps at scale?](./gitops-and-continuous-delivery/how-do-you-structure-repositories-for-gitops-at-scale.md)                                                                                               | 🔴 Advanced     |
| 90  | [How do you promote a change from staging to production in GitOps?](./gitops-and-continuous-delivery/how-do-you-promote-a-change-from-staging-to-production-in-gitops.md)                                                                         | 🔴 Advanced     |
| 91  | [How do you give teams self-service pipelines without maintaining 200 of them?](./gitops-and-continuous-delivery/how-do-you-give-teams-self-service-pipelines-without-maintaining-200-of-them.md)                                                 | 🔴 Advanced     |

</details>

<details>
<summary><b>Progressive Delivery and Feature Flags</b> · 14 questions · 🟢 5 🟡 3 🔴 6</summary>

[Open the Progressive Delivery and Feature Flags index →](./progressive-delivery-and-feature-flags/README.md)

| No. | Question                                                                                                                                                                            | Difficulty      |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 92  | [What is progressive delivery?](./progressive-delivery-and-feature-flags/what-is-progressive-delivery.md)                                                                           | 🟢 Beginner     |
| 93  | [What is a feature flag?](./progressive-delivery-and-feature-flags/what-is-a-feature-flag.md)                                                                                       | 🟢 Beginner     |
| 94  | [What is a canary deployment?](./progressive-delivery-and-feature-flags/what-is-a-canary-deployment.md)                                                                             | 🟢 Beginner     |
| 95  | [What is a blue-green deployment?](./progressive-delivery-and-feature-flags/what-is-a-blue-green-deployment.md)                                                                     | 🟢 Beginner     |
| 96  | [What is the difference between deploying and releasing?](./progressive-delivery-and-feature-flags/what-is-the-difference-between-deploying-and-releasing.md)                       | 🟢 Beginner     |
| 97  | [When do you use a feature flag instead of a canary deployment?](./progressive-delivery-and-feature-flags/when-do-you-use-a-feature-flag-instead-of-a-canary-deployment.md)         | 🟡 Intermediate |
| 98  | [How do you test code that sits behind feature flags?](./progressive-delivery-and-feature-flags/how-do-you-test-code-that-sits-behind-feature-flags.md)                             | 🟡 Intermediate |
| 99  | [What is OpenFeature and why does a vendor-neutral flag API matter?](./progressive-delivery-and-feature-flags/what-is-openfeature-and-why-does-a-vendor-neutral-flag-api-matter.md) | 🟡 Intermediate |
| 100 | [How do you run feature flags as a platform capability?](./progressive-delivery-and-feature-flags/how-do-you-run-feature-flags-as-a-platform-capability.md)                         | 🔴 Advanced     |
| 101 | [How do you manage feature flag debt?](./progressive-delivery-and-feature-flags/how-do-you-manage-feature-flag-debt.md)                                                             | 🔴 Advanced     |
| 102 | [How do you design a progressive rollout and its abort criteria?](./progressive-delivery-and-feature-flags/how-do-you-design-a-progressive-rollout-and-its-abort-criteria.md)       | 🔴 Advanced     |
| 103 | [How do you design a kill switch you can trust?](./progressive-delivery-and-feature-flags/how-do-you-design-a-kill-switch-you-can-trust.md)                                         | 🔴 Advanced     |
| 104 | [How do you keep percentage rollouts consistent across services?](./progressive-delivery-and-feature-flags/how-do-you-keep-percentage-rollouts-consistent-across-services.md)       | 🔴 Advanced     |
| 105 | [What can a feature flag not roll back?](./progressive-delivery-and-feature-flags/what-can-a-feature-flag-not-roll-back.md)                                                         | 🔴 Advanced     |

</details>

<details>
<summary><b>Environments and Ephemeral Infrastructure</b> · 13 questions · 🟢 5 🟡 5 🔴 3</summary>

[Open the Environments and Ephemeral Infrastructure index →](./environments-and-ephemeral-infrastructure/README.md)

| No. | Question                                                                                                                                                                             | Difficulty      |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------- |
| 106 | [What are dev, staging, and production environments for?](./environments-and-ephemeral-infrastructure/what-are-dev-staging-and-production-environments-for.md)                       | 🟢 Beginner     |
| 107 | [What is a cloud development environment?](./environments-and-ephemeral-infrastructure/what-is-a-cloud-development-environment.md)                                                   | 🟢 Beginner     |
| 108 | [What is a dev container and why do platforms standardise on them?](./environments-and-ephemeral-infrastructure/what-is-a-dev-container-and-why-do-platforms-standardise-on-them.md) | 🟢 Beginner     |
| 109 | [How do you keep environment configuration out of the code?](./environments-and-ephemeral-infrastructure/how-do-you-keep-environment-configuration-out-of-the-code.md)               | 🟢 Beginner     |
| 110 | [What is a sandbox environment and who is it for?](./environments-and-ephemeral-infrastructure/what-is-a-sandbox-environment-and-who-is-it-for.md)                                   | 🟢 Beginner     |
| 111 | [What is an ephemeral environment and when is it worth it?](./environments-and-ephemeral-infrastructure/what-is-an-ephemeral-environment-and-when-is-it-worth-it.md)                 | 🟡 Intermediate |
| 112 | [What does environment parity actually require?](./environments-and-ephemeral-infrastructure/what-does-environment-parity-actually-require.md)                                       | 🟡 Intermediate |
| 113 | [How do you stop ephemeral environments becoming a cost problem?](./environments-and-ephemeral-infrastructure/how-do-you-stop-ephemeral-environments-becoming-a-cost-problem.md)     | 🟡 Intermediate |
| 114 | [How do you give developers a fast inner development loop?](./environments-and-ephemeral-infrastructure/how-do-you-give-developers-a-fast-inner-development-loop.md)                 | 🟡 Intermediate |
| 115 | [How do you give each pull request its own database?](./environments-and-ephemeral-infrastructure/how-do-you-give-each-pull-request-its-own-database.md)                             | 🟡 Intermediate |
| 116 | [How do you build preview environments for every pull request?](./environments-and-ephemeral-infrastructure/how-do-you-build-preview-environments-for-every-pull-request.md)         | 🔴 Advanced     |
| 117 | [How do you seed realistic test data without copying production?](./environments-and-ephemeral-infrastructure/how-do-you-seed-realistic-test-data-without-copying-production.md)     | 🔴 Advanced     |
| 118 | [How do you model environments as a first-class platform resource?](./environments-and-ephemeral-infrastructure/how-do-you-model-environments-as-a-first-class-platform-resource.md) | 🔴 Advanced     |

</details>

### 🔐 Security and Governance

_27 questions_

<details>
<summary><b>Platform Security</b> · 14 questions · 🟢 5 🟡 3 🔴 6</summary>

[Open the Platform Security index →](./platform-security/README.md)

| No. | Question                                                                                                                                                                                   | Difficulty      |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------- |
| 119 | [What is least privilege and how does a platform enforce it by default?](./platform-security/what-is-least-privilege-and-how-does-a-platform-enforce-it-by-default.md)                     | 🟢 Beginner     |
| 120 | [What is an SBOM and why do platforms generate one?](./platform-security/what-is-an-sbom-and-why-do-platforms-generate-one.md)                                                             | 🟢 Beginner     |
| 121 | [What is container image signing?](./platform-security/what-is-container-image-signing.md)                                                                                                 | 🟢 Beginner     |
| 122 | [What is the shared responsibility model for a platform?](./platform-security/what-is-the-shared-responsibility-model-for-a-platform.md)                                                   | 🟢 Beginner     |
| 123 | [What is shift-left security and where does it go wrong?](./platform-security/what-is-shift-left-security-and-where-does-it-go-wrong.md)                                                   | 🟢 Beginner     |
| 124 | [How do you manage secrets as a platform capability?](./platform-security/how-do-you-manage-secrets-as-a-platform-capability.md)                                                           | 🟡 Intermediate |
| 125 | [How do you keep base images patched across every team?](./platform-security/how-do-you-keep-base-images-patched-across-every-team.md)                                                     | 🟡 Intermediate |
| 126 | [What does the EU Cyber Resilience Act mean for a platform team?](./platform-security/what-does-the-eu-cyber-resilience-act-mean-for-a-platform-team.md)                                   | 🟡 Intermediate |
| 127 | [How does a platform provide workload identity without long-lived credentials?](./platform-security/how-does-a-platform-provide-workload-identity-without-long-lived-credentials.md)       | 🔴 Advanced     |
| 128 | [How do you run a secretless CI/CD pipeline?](./platform-security/how-do-you-run-a-secretless-ci-cd-pipeline.md)                                                                           | 🔴 Advanced     |
| 129 | [How do you secure the software supply chain for everything the platform builds?](./platform-security/how-do-you-secure-the-software-supply-chain-for-everything-the-platform-builds.md)   | 🔴 Advanced     |
| 130 | [How do you respond to a critical CVE that affects every service on the platform?](./platform-security/how-do-you-respond-to-a-critical-cve-that-affects-every-service-on-the-platform.md) | 🔴 Advanced     |
| 131 | [How do you design break-glass access to production?](./platform-security/how-do-you-design-break-glass-access-to-production.md)                                                           | 🔴 Advanced     |
| 132 | [How do you threat model a platform?](./platform-security/how-do-you-threat-model-a-platform.md)                                                                                           | 🔴 Advanced     |

</details>

<details>
<summary><b>Policy as Code and Governance</b> · 13 questions · 🟢 5 🟡 5 🔴 3</summary>

[Open the Policy as Code and Governance index →](./policy-as-code-and-governance/README.md)

| No. | Question                                                                                                                                                                                     | Difficulty      |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 133 | [What is a guardrail and how does it differ from a gate?](./policy-as-code-and-governance/what-is-a-guardrail-and-how-does-it-differ-from-a-gate.md)                                         | 🟢 Beginner     |
| 134 | [What is Open Policy Agent?](./policy-as-code-and-governance/what-is-open-policy-agent.md)                                                                                                   | 🟢 Beginner     |
| 135 | [What is the difference between preventive and detective controls?](./policy-as-code-and-governance/what-is-the-difference-between-preventive-and-detective-controls.md)                     | 🟢 Beginner     |
| 136 | [What is the difference between audit mode and enforce mode for a policy?](./policy-as-code-and-governance/what-is-the-difference-between-audit-mode-and-enforce-mode-for-a-policy.md)       | 🟢 Beginner     |
| 137 | [Which compliance frameworks do platform teams meet most often?](./policy-as-code-and-governance/which-compliance-frameworks-do-platform-teams-meet-most-often.md)                           | 🟢 Beginner     |
| 138 | [What is policy as code and where does it belong in a platform?](./policy-as-code-and-governance/what-is-policy-as-code-and-where-does-it-belong-in-a-platform.md)                           | 🟡 Intermediate |
| 139 | [How do Gatekeeper and Kyverno differ, and how do you choose?](./policy-as-code-and-governance/how-do-gatekeeper-and-kyverno-differ-and-how-do-you-choose.md)                                | 🟡 Intermediate |
| 140 | [How do you handle policy exceptions without eroding the guardrails?](./policy-as-code-and-governance/how-do-you-handle-policy-exceptions-without-eroding-the-guardrails.md)                 | 🟡 Intermediate |
| 141 | [What audit trail does a platform owe its auditors?](./policy-as-code-and-governance/what-audit-trail-does-a-platform-owe-its-auditors.md)                                                   | 🟡 Intermediate |
| 142 | [What is ValidatingAdmissionPolicy and when does it replace a policy engine?](./policy-as-code-and-governance/what-is-validatingadmissionpolicy-and-when-does-it-replace-a-policy-engine.md) | 🟡 Intermediate |
| 143 | [How do you roll out a new policy without breaking every team?](./policy-as-code-and-governance/how-do-you-roll-out-a-new-policy-without-breaking-every-team.md)                             | 🔴 Advanced     |
| 144 | [How do you turn a compliance framework into automated platform controls?](./policy-as-code-and-governance/how-do-you-turn-a-compliance-framework-into-automated-platform-controls.md)       | 🔴 Advanced     |
| 145 | [How do you test and version policies like application code?](./policy-as-code-and-governance/how-do-you-test-and-version-policies-like-application-code.md)                                 | 🔴 Advanced     |

</details>

### ☁️ Cloud Platforms

_52 questions_

<details>
<summary><b>AWS Platform Engineering</b> · 13 questions · 🟢 5 🟡 4 🔴 4</summary>

[Open the AWS Platform Engineering index →](./aws-platform-engineering/README.md)

| No. | Question                                                                                                                                                                                           | Difficulty      |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 146 | [What are AWS Organizations and service control policies?](./aws-platform-engineering/what-are-aws-organizations-and-service-control-policies.md)                                                  | 🟢 Beginner     |
| 147 | [What does AWS Control Tower set up for a platform?](./aws-platform-engineering/what-does-aws-control-tower-set-up-for-a-platform.md)                                                              | 🟢 Beginner     |
| 148 | [What is the difference between an IAM user and an IAM role?](./aws-platform-engineering/what-is-the-difference-between-an-iam-user-and-an-iam-role.md)                                            | 🟢 Beginner     |
| 149 | [What is a VPC and how should a platform design one on AWS?](./aws-platform-engineering/what-is-a-vpc-and-how-should-a-platform-design-one-on-aws.md)                                              | 🟢 Beginner     |
| 150 | [What does Amazon EKS manage for you, and what is left to the platform?](./aws-platform-engineering/what-does-amazon-eks-manage-for-you-and-what-is-left-to-the-platform.md)                       | 🟢 Beginner     |
| 151 | [How do you give pods on EKS access to AWS resources safely?](./aws-platform-engineering/how-do-you-give-pods-on-eks-access-to-aws-resources-safely.md)                                            | 🟡 Intermediate |
| 152 | [How do you choose between ECS, EKS, Lambda, and App Runner for a platform runtime?](./aws-platform-engineering/how-do-you-choose-between-ecs-eks-lambda-and-app-runner-for-a-platform-runtime.md) | 🟡 Intermediate |
| 153 | [How do you allocate AWS cost back to teams?](./aws-platform-engineering/how-do-you-allocate-aws-cost-back-to-teams.md)                                                                            | 🟡 Intermediate |
| 154 | [What is EKS Auto Mode and when would a platform use it?](./aws-platform-engineering/what-is-eks-auto-mode-and-when-would-a-platform-use-it.md)                                                    | 🟡 Intermediate |
| 155 | [How do you structure a multi-account AWS platform?](./aws-platform-engineering/how-do-you-structure-a-multi-account-aws-platform.md)                                                              | 🔴 Advanced     |
| 156 | [What is account vending and how do you automate it?](./aws-platform-engineering/what-is-account-vending-and-how-do-you-automate-it.md)                                                            | 🔴 Advanced     |
| 157 | [How do you manage EKS node capacity with Karpenter?](./aws-platform-engineering/how-do-you-manage-eks-node-capacity-with-karpenter.md)                                                            | 🔴 Advanced     |
| 158 | [How do you build a paved road for AWS infrastructure self-service?](./aws-platform-engineering/how-do-you-build-a-paved-road-for-aws-infrastructure-self-service.md)                              | 🔴 Advanced     |

</details>

<details>
<summary><b>Azure Platform Engineering</b> · 13 questions · 🟢 5 🟡 4 🔴 4</summary>

[Open the Azure Platform Engineering index →](./azure-platform-engineering/README.md)

| No. | Question                                                                                                                                                                                            | Difficulty      |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 159 | [What is an Azure subscription and why is it the unit of a landing zone?](./azure-platform-engineering/what-is-an-azure-subscription-and-why-is-it-the-unit-of-a-landing-zone.md)                   | 🟢 Beginner     |
| 160 | [How do Microsoft Entra ID and Azure RBAC relate?](./azure-platform-engineering/how-do-microsoft-entra-id-and-azure-rbac-relate.md)                                                                 | 🟢 Beginner     |
| 161 | [What is a managed identity?](./azure-platform-engineering/what-is-a-managed-identity.md)                                                                                                           | 🟢 Beginner     |
| 162 | [How do Azure Resource Manager, ARM templates, and Bicep relate?](./azure-platform-engineering/how-do-azure-resource-manager-arm-templates-and-bicep-relate.md)                                     | 🟢 Beginner     |
| 163 | [What does AKS manage for you, and what is left to the platform?](./azure-platform-engineering/what-does-aks-manage-for-you-and-what-is-left-to-the-platform.md)                                    | 🟢 Beginner     |
| 164 | [How do you use Azure Policy as a platform guardrail?](./azure-platform-engineering/how-do-you-use-azure-policy-as-a-platform-guardrail.md)                                                         | 🟡 Intermediate |
| 165 | [How do workload identities work on AKS?](./azure-platform-engineering/how-do-workload-identities-work-on-aks.md)                                                                                   | 🟡 Intermediate |
| 166 | [How do you choose between AKS, Container Apps, App Service, and Functions?](./azure-platform-engineering/how-do-you-choose-between-aks-container-apps-app-service-and-functions.md)                | 🟡 Intermediate |
| 167 | [What is AKS Automatic and when would a platform use it?](./azure-platform-engineering/what-is-aks-automatic-and-when-would-a-platform-use-it.md)                                                   | 🟡 Intermediate |
| 168 | [How do you structure an Azure platform with management groups and landing zones?](./azure-platform-engineering/how-do-you-structure-an-azure-platform-with-management-groups-and-landing-zones.md) | 🔴 Advanced     |
| 169 | [How do you use Bicep for platform modules and subscription vending?](./azure-platform-engineering/how-do-you-use-bicep-for-platform-modules-and-subscription-vending.md)                           | 🔴 Advanced     |
| 170 | [How do you design private networking for Azure PaaS services?](./azure-platform-engineering/how-do-you-design-private-networking-for-azure-paas-services.md)                                       | 🔴 Advanced     |
| 171 | [How do you manage a fleet of AKS clusters with Azure Kubernetes Fleet Manager?](./azure-platform-engineering/how-do-you-manage-a-fleet-of-aks-clusters-with-azure-kubernetes-fleet-manager.md)     | 🔴 Advanced     |

</details>

<details>
<summary><b>GCP Platform Engineering</b> · 13 questions · 🟢 5 🟡 4 🔴 4</summary>

[Open the GCP Platform Engineering index →](./gcp-platform-engineering/README.md)

| No. | Question                                                                                                                                                                                                    | Difficulty      |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 172 | [What is a GCP project and why is it the unit of isolation?](./gcp-platform-engineering/what-is-a-gcp-project-and-why-is-it-the-unit-of-isolation.md)                                                       | 🟢 Beginner     |
| 173 | [How do IAM roles and service accounts work on GCP?](./gcp-platform-engineering/how-do-iam-roles-and-service-accounts-work-on-gcp.md)                                                                       | 🟢 Beginner     |
| 174 | [What does Cloud Run manage for you?](./gcp-platform-engineering/what-does-cloud-run-manage-for-you.md)                                                                                                     | 🟢 Beginner     |
| 175 | [What is Artifact Registry and why did it replace Container Registry?](./gcp-platform-engineering/what-is-artifact-registry-and-why-did-it-replace-container-registry.md)                                   | 🟢 Beginner     |
| 176 | [How is a VPC on GCP different from one on AWS?](./gcp-platform-engineering/how-is-a-vpc-on-gcp-different-from-one-on-aws.md)                                                                               | 🟢 Beginner     |
| 177 | [How does Workload Identity Federation remove service account keys?](./gcp-platform-engineering/how-does-workload-identity-federation-remove-service-account-keys.md)                                       | 🟡 Intermediate |
| 178 | [How do you choose between GKE, GKE Autopilot, and Cloud Run?](./gcp-platform-engineering/how-do-you-choose-between-gke-gke-autopilot-and-cloud-run.md)                                                     | 🟡 Intermediate |
| 179 | [How do you automate project vending on GCP?](./gcp-platform-engineering/how-do-you-automate-project-vending-on-gcp.md)                                                                                     | 🟡 Intermediate |
| 180 | [How do you use GKE fleets to manage many clusters?](./gcp-platform-engineering/how-do-you-use-gke-fleets-to-manage-many-clusters.md)                                                                       | 🟡 Intermediate |
| 181 | [How do you structure a GCP platform with folders, projects, and organisation policies?](./gcp-platform-engineering/how-do-you-structure-a-gcp-platform-with-folders-projects-and-organisation-policies.md) | 🔴 Advanced     |
| 182 | [How do you design Shared VPC for a multi-team GCP platform?](./gcp-platform-engineering/how-do-you-design-shared-vpc-for-a-multi-team-gcp-platform.md)                                                     | 🔴 Advanced     |
| 183 | [How do you use Config Connector and Config Sync as a GCP control plane?](./gcp-platform-engineering/how-do-you-use-config-connector-and-config-sync-as-a-gcp-control-plane.md)                             | 🔴 Advanced     |
| 184 | [How do you use VPC Service Controls to prevent data exfiltration?](./gcp-platform-engineering/how-do-you-use-vpc-service-controls-to-prevent-data-exfiltration.md)                                         | 🔴 Advanced     |

</details>

<details>
<summary><b>Multi-Cloud and Hybrid Platforms</b> · 13 questions · 🟢 5 🟡 4 🔴 4</summary>

[Open the Multi-Cloud and Hybrid Platforms index →](./multi-cloud-and-hybrid-platforms/README.md)

| No. | Question                                                                                                                                                                              | Difficulty      |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 185 | [What is the difference between multi-cloud and hybrid cloud?](./multi-cloud-and-hybrid-platforms/what-is-the-difference-between-multi-cloud-and-hybrid-cloud.md)                     | 🟢 Beginner     |
| 186 | [What is vendor lock-in and how much should a platform worry about it?](./multi-cloud-and-hybrid-platforms/what-is-vendor-lock-in-and-how-much-should-a-platform-worry-about-it.md)   | 🟢 Beginner     |
| 187 | [Which tools help a platform span more than one cloud?](./multi-cloud-and-hybrid-platforms/which-tools-help-a-platform-span-more-than-one-cloud.md)                                   | 🟢 Beginner     |
| 188 | [How does identity federation work across clouds?](./multi-cloud-and-hybrid-platforms/how-does-identity-federation-work-across-clouds.md)                                             | 🟢 Beginner     |
| 189 | [Where does edge computing fit in a hybrid platform?](./multi-cloud-and-hybrid-platforms/where-does-edge-computing-fit-in-a-hybrid-platform.md)                                       | 🟢 Beginner     |
| 190 | [When is multi-cloud a real requirement rather than a slogan?](./multi-cloud-and-hybrid-platforms/when-is-multi-cloud-a-real-requirement-rather-than-a-slogan.md)                     | 🟡 Intermediate |
| 191 | [How do you map equivalent primitives across AWS, Azure, and GCP?](./multi-cloud-and-hybrid-platforms/how-do-you-map-equivalent-primitives-across-aws-azure-and-gcp.md)               | 🟡 Intermediate |
| 192 | [How do you connect networks across clouds?](./multi-cloud-and-hybrid-platforms/how-do-you-connect-networks-across-clouds.md)                                                         | 🟡 Intermediate |
| 193 | [How do you handle data residency and sovereignty requirements?](./multi-cloud-and-hybrid-platforms/how-do-you-handle-data-residency-and-sovereignty-requirements.md)                 | 🟡 Intermediate |
| 194 | [What does a genuinely portable platform abstraction cost you?](./multi-cloud-and-hybrid-platforms/what-does-a-genuinely-portable-platform-abstraction-cost-you.md)                   | 🔴 Advanced     |
| 195 | [How do you design a hybrid platform spanning on-premises and cloud?](./multi-cloud-and-hybrid-platforms/how-do-you-design-a-hybrid-platform-spanning-on-premises-and-cloud.md)       | 🔴 Advanced     |
| 196 | [How does data gravity constrain platform design?](./multi-cloud-and-hybrid-platforms/how-does-data-gravity-constrain-platform-design.md)                                             | 🔴 Advanced     |
| 197 | [How do you design multi-cloud disaster recovery without doubling cost?](./multi-cloud-and-hybrid-platforms/how-do-you-design-multi-cloud-disaster-recovery-without-doubling-cost.md) | 🔴 Advanced     |

</details>

### 📈 Reliability and Observability

_26 questions_

<details>
<summary><b>Platform Reliability</b> · 13 questions · 🟢 5 🟡 3 🔴 5</summary>

[Open the Platform Reliability index →](./platform-reliability/README.md)

| No. | Question                                                                                                                                                                      | Difficulty      |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 198 | [What are SLIs, SLOs, and SLAs?](./platform-reliability/what-are-slis-slos-and-slas.md)                                                                                       | 🟢 Beginner     |
| 199 | [What is an error budget?](./platform-reliability/what-is-an-error-budget.md)                                                                                                 | 🟢 Beginner     |
| 200 | [What is a blameless postmortem?](./platform-reliability/what-is-a-blameless-postmortem.md)                                                                                   | 🟢 Beginner     |
| 201 | [What are RTO and RPO, and how do they differ from high availability?](./platform-reliability/what-are-rto-and-rpo-and-how-do-they-differ-from-high-availability.md)          | 🟢 Beginner     |
| 202 | [What is toil and how does a platform team reduce it?](./platform-reliability/what-is-toil-and-how-does-a-platform-team-reduce-it.md)                                         | 🟢 Beginner     |
| 203 | [How do you run on-call for a platform team?](./platform-reliability/how-do-you-run-on-call-for-a-platform-team.md)                                                           | 🟡 Intermediate |
| 204 | [How do you use chaos engineering to test platform guarantees?](./platform-reliability/how-do-you-use-chaos-engineering-to-test-platform-guarantees.md)                       | 🟡 Intermediate |
| 205 | [How do you run a production readiness review?](./platform-reliability/how-do-you-run-a-production-readiness-review.md)                                                       | 🟡 Intermediate |
| 206 | [How do you define SLOs for a platform rather than an application?](./platform-reliability/how-do-you-define-slos-for-a-platform-rather-than-an-application.md)               | 🔴 Advanced     |
| 207 | [What does an error budget policy look like for a platform team?](./platform-reliability/what-does-an-error-budget-policy-look-like-for-a-platform-team.md)                   | 🔴 Advanced     |
| 208 | [How do you run an incident when the platform itself is the incident?](./platform-reliability/how-do-you-run-an-incident-when-the-platform-itself-is-the-incident.md)         | 🔴 Advanced     |
| 209 | [How do you make a platform degrade gracefully instead of failing closed?](./platform-reliability/how-do-you-make-a-platform-degrade-gracefully-instead-of-failing-closed.md) | 🔴 Advanced     |
| 210 | [How do you plan disaster recovery for the platform itself?](./platform-reliability/how-do-you-plan-disaster-recovery-for-the-platform-itself.md)                             | 🔴 Advanced     |

</details>

<details>
<summary><b>Platform Observability</b> · 13 questions · 🟢 5 🟡 4 🔴 4</summary>

[Open the Platform Observability index →](./platform-observability/README.md)

| No. | Question                                                                                                                                                                                             | Difficulty      |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 211 | [What is the difference between monitoring and observability?](./platform-observability/what-is-the-difference-between-monitoring-and-observability.md)                                              | 🟢 Beginner     |
| 212 | [What are metrics, logs, and traces, and why is "three pillars" an incomplete framing?](./platform-observability/what-are-metrics-logs-and-traces-and-why-is-three-pillars-an-incomplete-framing.md) | 🟢 Beginner     |
| 213 | [What is OpenTelemetry?](./platform-observability/what-is-opentelemetry.md)                                                                                                                          | 🟢 Beginner     |
| 214 | [What are the RED and USE methods?](./platform-observability/what-are-the-red-and-use-methods.md)                                                                                                    | 🟢 Beginner     |
| 215 | [What is structured logging and why does a platform enforce it?](./platform-observability/what-is-structured-logging-and-why-does-a-platform-enforce-it.md)                                          | 🟢 Beginner     |
| 216 | [How do you provide observability as a platform capability?](./platform-observability/how-do-you-provide-observability-as-a-platform-capability.md)                                                  | 🟡 Intermediate |
| 217 | [What telemetry should every service get without writing code?](./platform-observability/what-telemetry-should-every-service-get-without-writing-code.md)                                            | 🟡 Intermediate |
| 218 | [How do you give teams visibility into platform state that affects them?](./platform-observability/how-do-you-give-teams-visibility-into-platform-state-that-affects-them.md)                        | 🟡 Intermediate |
| 219 | [How do you design alerts that page only for real problems?](./platform-observability/how-do-you-design-alerts-that-page-only-for-real-problems.md)                                                  | 🟡 Intermediate |
| 220 | [How do you run an OpenTelemetry collector as a platform service?](./platform-observability/how-do-you-run-an-opentelemetry-collector-as-a-platform-service.md)                                      | 🔴 Advanced     |
| 221 | [How do you control metric cardinality and observability cost?](./platform-observability/how-do-you-control-metric-cardinality-and-observability-cost.md)                                            | 🔴 Advanced     |
| 222 | [How do you make traces useful across team boundaries?](./platform-observability/how-do-you-make-traces-useful-across-team-boundaries.md)                                                            | 🔴 Advanced     |
| 223 | [How do you add continuous profiling to a platform?](./platform-observability/how-do-you-add-continuous-profiling-to-a-platform.md)                                                                  | 🔴 Advanced     |

</details>

### 💰 Economics and Operating Model

_26 questions_

<details>
<summary><b>Platform FinOps</b> · 13 questions · 🟢 5 🟡 4 🔴 4</summary>

[Open the Platform FinOps index →](./platform-finops/README.md)

| No. | Question                                                                                                                                                                | Difficulty      |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 224 | [What is FinOps and what part of it does a platform team own?](./platform-finops/what-is-finops-and-what-part-of-it-does-a-platform-team-own.md)                        | 🟢 Beginner     |
| 225 | [What are the main cloud pricing models?](./platform-finops/what-are-the-main-cloud-pricing-models.md)                                                                  | 🟢 Beginner     |
| 226 | [What is cost allocation tagging and why does it fail?](./platform-finops/what-is-cost-allocation-tagging-and-why-does-it-fail.md)                                      | 🟢 Beginner     |
| 227 | [What is rightsizing?](./platform-finops/what-is-rightsizing.md)                                                                                                        | 🟢 Beginner     |
| 228 | [Why is Kubernetes cost allocation hard?](./platform-finops/why-is-kubernetes-cost-allocation-hard.md)                                                                  | 🟢 Beginner     |
| 229 | [What is the difference between showback and chargeback, and which works?](./platform-finops/what-is-the-difference-between-showback-and-chargeback-and-which-works.md) | 🟡 Intermediate |
| 230 | [How do you find and remove idle platform cost?](./platform-finops/how-do-you-find-and-remove-idle-platform-cost.md)                                                    | 🟡 Intermediate |
| 231 | [What is the FOCUS specification and why does it matter?](./platform-finops/what-is-the-focus-specification-and-why-does-it-matter.md)                                  | 🟡 Intermediate |
| 232 | [How do you put cost feedback into the developer workflow?](./platform-finops/how-do-you-put-cost-feedback-into-the-developer-workflow.md)                              | 🟡 Intermediate |
| 233 | [How do you attribute shared platform cost to teams?](./platform-finops/how-do-you-attribute-shared-platform-cost-to-teams.md)                                          | 🔴 Advanced     |
| 234 | [How do you build unit economics for a platform?](./platform-finops/how-do-you-build-unit-economics-for-a-platform.md)                                                  | 🔴 Advanced     |
| 235 | [How do you use commitments and spot capacity on behalf of every team?](./platform-finops/how-do-you-use-commitments-and-spot-capacity-on-behalf-of-every-team.md)      | 🔴 Advanced     |
| 236 | [How do you manage the cost of GPU and AI workloads on a platform?](./platform-finops/how-do-you-manage-the-cost-of-gpu-and-ai-workloads-on-a-platform.md)              | 🔴 Advanced     |

</details>

<details>
<summary><b>Platform Team and Operating Model</b> · 13 questions · 🟢 5 🟡 4 🔴 4</summary>

[Open the Platform Team and Operating Model index →](./platform-team-and-operating-model/README.md)

| No. | Question                                                                                                                                                                                       | Difficulty      |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 237 | [What does Team Topologies say about platform teams?](./platform-team-and-operating-model/what-does-team-topologies-say-about-platform-teams.md)                                               | 🟢 Beginner     |
| 238 | [What does a platform product manager do?](./platform-team-and-operating-model/what-does-a-platform-product-manager-do.md)                                                                     | 🟢 Beginner     |
| 239 | [What is the difference between a platform team and an infrastructure team?](./platform-team-and-operating-model/what-is-the-difference-between-a-platform-team-and-an-infrastructure-team.md) | 🟢 Beginner     |
| 240 | [What is an enabling team and how does it work with a platform team?](./platform-team-and-operating-model/what-is-an-enabling-team-and-how-does-it-work-with-a-platform-team.md)               | 🟢 Beginner     |
| 241 | [How do you gather feedback from platform users?](./platform-team-and-operating-model/how-do-you-gather-feedback-from-platform-users.md)                                                       | 🟢 Beginner     |
| 242 | [How do you size and staff a platform team?](./platform-team-and-operating-model/how-do-you-size-and-staff-a-platform-team.md)                                                                 | 🟡 Intermediate |
| 243 | [How do you measure platform adoption and success?](./platform-team-and-operating-model/how-do-you-measure-platform-adoption-and-success.md)                                                   | 🟡 Intermediate |
| 244 | [How do you run an RFC process for platform decisions?](./platform-team-and-operating-model/how-do-you-run-an-rfc-process-for-platform-decisions.md)                                           | 🟡 Intermediate |
| 245 | [How do you fund a platform team?](./platform-team-and-operating-model/how-do-you-fund-a-platform-team.md)                                                                                     | 🟡 Intermediate |
| 246 | [How do you migrate teams onto the platform without a mandate?](./platform-team-and-operating-model/how-do-you-migrate-teams-onto-the-platform-without-a-mandate.md)                           | 🔴 Advanced     |
| 247 | [How do you deprecate a platform capability?](./platform-team-and-operating-model/how-do-you-deprecate-a-platform-capability.md)                                                               | 🔴 Advanced     |
| 248 | [How do you build a platform roadmap and say no?](./platform-team-and-operating-model/how-do-you-build-a-platform-roadmap-and-say-no.md)                                                       | 🔴 Advanced     |
| 249 | [How do you scale a platform organisation from one team to several?](./platform-team-and-operating-model/how-do-you-scale-a-platform-organisation-from-one-team-to-several.md)                 | 🔴 Advanced     |

</details>

### 🎤 Interview Prep

_13 questions_

<details>
<summary><b>Platform Engineering Interviews</b> · 13 questions · 🟢 5 🟡 5 🔴 3</summary>

[Open the Platform Engineering Interviews index →](./platform-engineering-interviews/README.md)

| No. | Question                                                                                                                                                                                 | Difficulty      |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 250 | [What does a platform engineering interview loop look like?](./platform-engineering-interviews/what-does-a-platform-engineering-interview-loop-look-like.md)                             | 🟢 Beginner     |
| 251 | [What should you ask your interviewer about their platform?](./platform-engineering-interviews/what-should-you-ask-your-interviewer-about-their-platform.md)                             | 🟢 Beginner     |
| 252 | [How do you prepare for a platform engineering interview?](./platform-engineering-interviews/how-do-you-prepare-for-a-platform-engineering-interview.md)                                 | 🟢 Beginner     |
| 253 | [What should a platform engineering CV emphasise?](./platform-engineering-interviews/what-should-a-platform-engineering-cv-emphasise.md)                                                 | 🟢 Beginner     |
| 254 | [How do you answer 'tell me about yourself' for a platform role?](./platform-engineering-interviews/how-do-you-answer-tell-me-about-yourself-for-a-platform-role.md)                     | 🟢 Beginner     |
| 255 | [How do you present platform work you have done?](./platform-engineering-interviews/how-do-you-present-platform-work-you-have-done.md)                                                   | 🟡 Intermediate |
| 256 | [How do you handle a troubleshooting round?](./platform-engineering-interviews/how-do-you-handle-a-troubleshooting-round.md)                                                             | 🟡 Intermediate |
| 257 | [What behavioural questions do platform interviews ask, and why?](./platform-engineering-interviews/what-behavioural-questions-do-platform-interviews-ask-and-why.md)                    | 🟡 Intermediate |
| 258 | [How do you handle a live infrastructure-as-code exercise?](./platform-engineering-interviews/how-do-you-handle-a-live-infrastructure-as-code-exercise.md)                               | 🟡 Intermediate |
| 259 | [How do you talk about the impact and metrics of platform work?](./platform-engineering-interviews/how-do-you-talk-about-the-impact-and-metrics-of-platform-work.md)                     | 🟡 Intermediate |
| 260 | [How do you answer a platform design interview question?](./platform-engineering-interviews/how-do-you-answer-a-platform-design-interview-question.md)                                   | 🔴 Advanced     |
| 261 | [How do you answer 'how would you build a platform from scratch'?](./platform-engineering-interviews/how-do-you-answer-how-would-you-build-a-platform-from-scratch.md)                   | 🔴 Advanced     |
| 262 | [How do you approach a staff or principal platform engineering interview?](./platform-engineering-interviews/how-do-you-approach-a-staff-or-principal-platform-engineering-interview.md) | 🔴 Advanced     |

</details>

<!-- TOC:END -->

---

## 🧠 How answers are structured

Every answer follows the same four beats, so you can read one section deep or all four:

| Section            | What it gives you                                                                                             |
| ------------------ | ------------------------------------------------------------------------------------------------------------- |
| **Short answer**   | Two or three sentences you could say out loud. Start here.                                                    |
| **Detail**         | The substance - mechanisms, trade-offs, and the vocabulary that signals experience.                           |
| **Example**        | Real manifests, policies, commands, or diagrams you can run and adapt.                                        |
| **Interview tips** | The follow-up questions, the common traps, and the points that separate a strong answer from a memorised one. |

Difficulty is marked 🟢 Beginner · 🟡 Intermediate · 🔴 Advanced. Every topic carries at least five Beginner, three Intermediate, and two Advanced questions, so each one can be read as a path: the Beginner answers build the vocabulary, and the Intermediate and Advanced answers are about judgement rather than recall - which is where most platform roles, filled at senior and above, are actually decided.

**Three ways to work through it:**

- **Preparing for a specific role** - take the track from [Pick your role](#-pick-your-role), and read each topic README's "What interviewers probe here" before its questions.
- **Broad revision** - read the short answers across a topic, then go deep only where you hesitate.
- **Obsidian / note vault** - every file carries YAML frontmatter (`title`, `id`, `category`, `difficulty`, `tags`), so the whole repository can be dropped into a vault and browsed by tag.

---

## 🌌 The knowledge graph

Platform engineering questions do not sit in neat boxes: tenancy decides your isolation boundary, which decides your policy model, which decides what your golden path can promise. The [knowledge graph](https://mchittineni.github.io/ultimate-platform-engineering-guide/) makes those dependencies visible - every question is a node, and two questions are linked when they genuinely argue about the same concept.

The links are **derived, not hand-maintained**. Each answer is scanned for the ~70 concepts this field turns on (control plane, golden path, policy as code, blast radius, error budget, chargeback, …), and a pair is linked when the concepts they share are rare across the vault. Rarity weighting is what stops "kubernetes" linking everything to everything; length normalisation stops the longest answers becoming hubs.

```bash
python3 scripts/build_knowledge_graph.py --output docs/index.html   # the deployed page
python3 scripts/build_knowledge_graph.py --stats                    # edge counts, hubs, orphans
python3 scripts/build_knowledge_graph.py --json docs/graph.json     # the raw graph
python3 scripts/inject_wikilinks.py                                 # write the same edges into the question files
```

Three renderings ship with the builder and are selectable with `--prototype`:

| Prototype           | What it is for                                                                                                          |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| **`constellation`** | _(deployed)_ Force-directed map of the whole vault, clustered by theme. Click a question to light up its neighbourhood. |
| **`atlas`**         | The capability map: groups and topics laid out in reading order, with concept links drawn on demand.                    |
| **`pathway`**       | Difficulty lanes that generate a study route - the questions to read before the hard one makes sense.                   |

The page is a single self-contained HTML file with no dependencies, deployed to GitHub Pages by [`knowledge-graph.yml`](./.github/workflows/knowledge-graph.yml) on every push to `main`.

`inject_wikilinks.py` writes the same edges into each question's `## Related Questions` block, between `<!-- RELATED:START -->` and `<!-- RELATED:END -->` markers, as both `[[wikilinks]]` (for Obsidian-style vaults) and relative links (for GitHub). It is idempotent, and `--check` fails CI when a block has drifted from the graph.

---

## 🛠️ Repository structure

```text
.
├── platform-engineering-fundamentals/   # topic-slug/
│   ├── README.md                        #   generated topic index
│   └── what-is-platform-engineering.md  #   question-slug.md
├── ...
├── scripts/
│   ├── lib_content.py                   # shared frontmatter/vault parsing
│   ├── generate_indexes.py              # regenerates all indexes from question files
│   ├── validate_content.py              # CI validation of the whole vault
│   ├── build_knowledge_graph.py         # derives the concept graph, renders the HTML site
│   ├── inject_wikilinks.py              # writes graph edges into `## Related Questions` blocks
│   └── topic_meta.json                  # topic registry: order, group, description, study notes
├── docs/
│   └── index.html                       # generated knowledge graph, deployed to GitHub Pages
└── .github/workflows/
    ├── validate-and-format.yml          # runs validation + Prettier on every PR
    └── knowledge-graph.yml              # rebuilds and deploys the graph on push to main
```

Directories and filenames carry **no numeric prefixes** - they are pure slugs. Ordering comes from two places instead:

- **Topic order** - the `order` field in `scripts/topic_meta.json`, which is also the registry of which directories count as topics.
- **Question order** - the `id` field in each question's frontmatter, unique across the repository.

Renaming or reordering is therefore a metadata edit, not a mass file rename.

Every question file starts with frontmatter:

```yaml
---
title: "What is a golden path and how does it differ from a mandate?"
id: 4
category: "Platform Engineering Fundamentals"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-engineering-fundamentals
  - interview-questions
---
```

**The indexes are generated, not hand-written.** The question files are the single source of truth; topic READMEs and the tables above are rendered from their frontmatter. After adding or editing a question:

```bash
python3 scripts/generate_indexes.py       # rewrite all indexes
python3 scripts/inject_wikilinks.py       # refresh the related-questions blocks
python3 scripts/build_knowledge_graph.py --output docs/index.html   # rebuild the graph page
python3 scripts/validate_content.py       # verify frontmatter, naming, links, index freshness
```

Both are stdlib-only Python 3.11+ - no dependencies to install. CI runs the same commands and fails the pull request on drift.

---

## 🤝 Contributing

New questions, better answers, and corrections are all welcome. [CONTRIBUTING.md](./CONTRIBUTING.md) covers the file format, naming rules, and the local checks to run before opening a pull request.

Not sure where to start? Open an issue - there are templates for [a new question](https://github.com/mchittineni/ultimate-platform-engineering-guide/issues/new?template=1-new-question.yml), [a correction to an existing answer](https://github.com/mchittineni/ultimate-platform-engineering-guide/issues/new?template=2-improve-answer.yml), [a new topic](https://github.com/mchittineni/ultimate-platform-engineering-guide/issues/new?template=3-new-topic.yml), and [broken links or tooling](https://github.com/mchittineni/ultimate-platform-engineering-guide/issues/new?template=4-bug-or-tooling.yml).

Two documents set the ground rules: the [Code of Conduct](./CODE_OF_CONDUCT.md) - including the rules on interviewer privacy, NDAs, and plagiarism - and the [Security Policy](./SECURITY.md), which covers how to report a committed credential, a workflow vulnerability, or a dangerously over-permissive example policy privately.

## 🧭 Related

Three sibling repositories, same structure, same tooling - pick the one that matches the role you are interviewing for:

- **[Ultimate DevOps Guide](https://github.com/mchittineni/ultimate-devops-guide)** - DevOps, SRE, DevSecOps, and cloud engineering. Start there for container, CI/CD, Linux, and networking fundamentals; this guide assumes them.
- **[Ultimate AI Engineering Guide](https://github.com/mchittineni/ultimate-ai-engineering-guide)** - LLM fundamentals, prompt engineering, RAG, agents and MCP, fine-tuning, evaluation, and LLMOps. The counterpart for AI platform and AI engineering loops, where this guide covers the infrastructure the models run on.
- **Ultimate Platform Engineering Guide** _(you are here)_ - the platform layer between the two: golden paths, control planes, tenancy, and the operating model of a team whose customers are other engineers.

## 🙏 Acknowledgements

The vocabulary this guide uses is not invented here. It leans on the work of the platform engineering community:

- **[Team Topologies](https://teamtopologies.com/)** by Matthew Skelton and Manuel Pais - platform teams as enabling teams, cognitive load as the design constraint, and the thinnest viable platform.
- **[CNCF Platforms Working Group](https://tag-app-delivery.cncf.io/whitepapers/platforms/)** - the platform maturity model and the capability-plane vocabulary.
- **[Google SRE](https://sre.google/books/)** - SLOs, error budgets, and the toil framing that platform reliability builds on.
- **[OpenFeature](https://openfeature.dev/)**, **[OpenTelemetry](https://opentelemetry.io/)**, **[Crossplane](https://www.crossplane.io/)**, **[Backstage](https://backstage.io/)**, and **[Argo CD](https://argo-cd.readthedocs.io/)** - the open standards and projects most of these answers reference.
- **[DORA](https://dora.dev/)** - the delivery metrics used throughout to argue about outcomes rather than output.

## 📄 License

Released under the [MIT License](./LICENSE).
