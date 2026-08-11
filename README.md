<div align="center">

# 🛠️ Ultimate Platform Engineering Guide

**136 questions across 20 topics - answered to the depth an interviewer actually expects.**

Role tracks: **Platform Engineer** (junior → staff) · **DevEx** · **Platform Architect** · **Kubernetes Platform** · **Platform Security** · **Platform SRE** · **AWS** · **Azure** · **GCP** · **FinOps** · **Platform Lead**

Every answer gives you a short answer you can say out loud, the detail and trade-offs behind it, a runnable example, and the follow-ups to expect.

[![Validate](https://github.com/mchittineni/ultimate-platform-engineering-guide/actions/workflows/validate-and-format.yml/badge.svg)](https://github.com/mchittineni/ultimate-platform-engineering-guide/actions/workflows/validate-and-format.yml)
![Questions](https://img.shields.io/badge/questions-136-blue)
![Topics](https://img.shields.io/badge/topics-20-blueviolet)
![Difficulty](https://img.shields.io/badge/difficulty-🟢%2011%20·%20🟡%2056%20·%20🔴%2069-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

[Pick your role](#-pick-your-role) · [Browse topics](#-browse-all-topics) · [All questions](#-all-questions) · [How answers are structured](#-how-answers-are-structured) · [Contributing](./CONTRIBUTING.md)

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

**136 questions** across **20 topics** - 🟢 11 Beginner · 🟡 56 Intermediate · 🔴 69 Advanced

### 🧱 Platform Foundations

| Topic                                                                                  | Questions | 🟢  | 🟡  | 🔴  | What it covers                                                                                  |
| -------------------------------------------------------------------------------------- | --------- | --- | --- | --- | ----------------------------------------------------------------------------------------------- |
| **[Platform Engineering Fundamentals](./platform-engineering-fundamentals/README.md)** | 8         | 3   | 3   | 2   | what a platform actually is, why self-service is the defining property, and where platform…     |
| **[Developer Experience](./developer-experience/README.md)**                           | 7         | 1   | 5   | 1   | cognitive load, service catalogues, portals, scorecards, onboarding time, and the metrics that… |

### 🏗️ Platform Architecture

| Topic                                                                      | Questions | 🟢  | 🟡  | 🔴  | What it covers                                                                                |
| -------------------------------------------------------------------------- | --------- | --- | --- | --- | --------------------------------------------------------------------------------------------- |
| **[Platform Architecture](./platform-architecture/README.md)**             | 8         | 1   | 3   | 4   | control plane versus data plane, the developer-facing API, escapable abstractions, interface… |
| **[Multi-Tenancy and Isolation](./multi-tenancy-and-isolation/README.md)** | 6         | 0   | 2   | 4   | tenancy models, namespace versus cluster boundaries, noisy neighbours, quotas, network…       |

### ☸️ Kubernetes and Control Planes

| Topic                                                                              | Questions | 🟢  | 🟡  | 🔴  | What it covers                                                                                    |
| ---------------------------------------------------------------------------------- | --------- | --- | --- | --- | ------------------------------------------------------------------------------------------------- |
| **[Kubernetes Platform](./kubernetes-platform/README.md)**                         | 8         | 1   | 2   | 5   | cluster topology, node pools and scheduling, fleet upgrades, admission control as a platform…     |
| **[Control Planes and Abstractions](./control-planes-and-abstractions/README.md)** | 6         | 0   | 1   | 5   | Crossplane, custom resources as platform contracts, workload specifications, Terraform at scale,… |

### 🔁 Delivery and Progressive Rollout

| Topic                                                                                                  | Questions | 🟢  | 🟡  | 🔴  | What it covers                                                                               |
| ------------------------------------------------------------------------------------------------------ | --------- | --- | --- | --- | -------------------------------------------------------------------------------------------- |
| **[GitOps and Continuous Delivery](./gitops-and-continuous-delivery/README.md)**                       | 8         | 1   | 4   | 3   | Argo CD and Flux, repository structure at scale, environment promotion, secrets, drift…      |
| **[Progressive Delivery and Feature Flags](./progressive-delivery-and-feature-flags/README.md)**       | 8         | 0   | 2   | 6   | flags as a platform capability, flag debt and its SLAs, rollout curves with abort criteria,… |
| **[Environments and Ephemeral Infrastructure](./environments-and-ephemeral-infrastructure/README.md)** | 6         | 0   | 4   | 2   | preview environments per pull request, data seeding without leaking production, environment… |

### 🔐 Security and Governance

| Topic                                                                          | Questions | 🟢  | 🟡  | 🔴  | What it covers                                                                               |
| ------------------------------------------------------------------------------ | --------- | --- | --- | --- | -------------------------------------------------------------------------------------------- |
| **[Platform Security](./platform-security/README.md)**                         | 8         | 0   | 2   | 6   | workload identity without long-lived keys, secretless pipelines, secrets management,…        |
| **[Policy as Code and Governance](./policy-as-code-and-governance/README.md)** | 6         | 0   | 4   | 2   | OPA and Kyverno, rolling out policy without breaking teams, compliance frameworks mapped to… |

### ☁️ Cloud Platforms

| Topic                                                                                | Questions | 🟢  | 🟡  | 🔴  | What it covers                                                                                |
| ------------------------------------------------------------------------------------ | --------- | --- | --- | --- | --------------------------------------------------------------------------------------------- |
| **[AWS Platform Engineering](./aws-platform-engineering/README.md)**                 | 7         | 0   | 3   | 4   | multi-account organisation design, account vending, EKS pod identity, runtime selection,…     |
| **[Azure Platform Engineering](./azure-platform-engineering/README.md)**             | 6         | 0   | 3   | 3   | management groups and landing zones, Azure Policy guardrails, AKS workload identity, runtime… |
| **[GCP Platform Engineering](./gcp-platform-engineering/README.md)**                 | 6         | 0   | 3   | 3   | the folder and project hierarchy, organisation policies, Workload Identity Federation, GKE…   |
| **[Multi-Cloud and Hybrid Platforms](./multi-cloud-and-hybrid-platforms/README.md)** | 5         | 0   | 2   | 3   | genuine drivers versus slogans, the cost of portable abstractions, cross-provider primitive…  |

### 📈 Reliability and Observability

| Topic                                                            | Questions | 🟢  | 🟡  | 🔴  | What it covers                                                                                  |
| ---------------------------------------------------------------- | --------- | --- | --- | --- | ----------------------------------------------------------------------------------------------- |
| **[Platform Reliability](./platform-reliability/README.md)**     | 7         | 0   | 2   | 5   | SLOs for a platform rather than an app, error budget policy, platform on-call, incidents where… |
| **[Platform Observability](./platform-observability/README.md)** | 6         | 0   | 3   | 3   | OpenTelemetry collectors as shared infrastructure, cardinality and cost control, zero-effort…   |

### 💰 Economics and Operating Model

| Topic                                                                                  | Questions | 🟢  | 🟡  | 🔴  | What it covers                                                                                  |
| -------------------------------------------------------------------------------------- | --------- | --- | --- | --- | ----------------------------------------------------------------------------------------------- |
| **[Platform FinOps](./platform-finops/README.md)**                                     | 6         | 1   | 2   | 3   | cost attribution for shared infrastructure, showback versus chargeback, unit economics,…        |
| **[Platform Team and Operating Model](./platform-team-and-operating-model/README.md)** | 7         | 1   | 3   | 3   | Team Topologies, staffing, adoption metrics, migration without a mandate, deprecation, the RFC… |

### 🎤 Interview Prep

| Topic                                                                              | Questions | 🟢  | 🟡  | 🔴  | What it covers                                                                     |
| ---------------------------------------------------------------------------------- | --------- | --- | --- | --- | ---------------------------------------------------------------------------------- |
| **[Platform Engineering Interviews](./platform-engineering-interviews/README.md)** | 7         | 2   | 3   | 2   | the loop structure, the platform design round, presenting your own platform work,… |

<!-- STATS:END -->

---

## 📋 All questions

Every question in the repository, collapsed by topic - open only the ones you are studying.

<!-- TOC:START -->

### 🧱 Platform Foundations

_15 questions_

<details>
<summary><b>Platform Engineering Fundamentals</b> · 8 questions · 🟢 3 🟡 3 🔴 2</summary>

[Open the Platform Engineering Fundamentals index →](./platform-engineering-fundamentals/README.md)

| No. | Question                                                                                                                                                                       | Difficulty      |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------- |
| 1   | [What is platform engineering?](./platform-engineering-fundamentals/what-is-platform-engineering.md)                                                                           | 🟢 Beginner     |
| 2   | [What is an internal developer platform?](./platform-engineering-fundamentals/what-is-an-internal-developer-platform.md)                                                       | 🟢 Beginner     |
| 3   | [How is platform engineering different from DevOps and SRE?](./platform-engineering-fundamentals/how-is-platform-engineering-different-from-devops-and-sre.md)                 | 🟢 Beginner     |
| 4   | [What is a golden path and how does it differ from a mandate?](./platform-engineering-fundamentals/what-is-a-golden-path-and-how-does-it-differ-from-a-mandate.md)             | 🟡 Intermediate |
| 5   | [What is the thinnest viable platform?](./platform-engineering-fundamentals/what-is-the-thinnest-viable-platform.md)                                                           | 🟡 Intermediate |
| 6   | [How do you decide whether your organisation needs a platform team?](./platform-engineering-fundamentals/how-do-you-decide-whether-your-organisation-needs-a-platform-team.md) | 🟡 Intermediate |
| 7   | [What does it mean to run a platform as a product?](./platform-engineering-fundamentals/what-does-it-mean-to-run-a-platform-as-a-product.md)                                   | 🔴 Advanced     |
| 8   | [What are the most common ways platform initiatives fail?](./platform-engineering-fundamentals/what-are-the-most-common-ways-platform-initiatives-fail.md)                     | 🔴 Advanced     |

</details>

<details>
<summary><b>Developer Experience</b> · 7 questions · 🟢 1 🟡 5 🔴 1</summary>

[Open the Developer Experience index →](./developer-experience/README.md)

| No. | Question                                                                                                                                                                        | Difficulty      |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 9   | [What is developer experience and how do you measure it?](./developer-experience/what-is-developer-experience-and-how-do-you-measure-it.md)                                     | 🟡 Intermediate |
| 10  | [What is cognitive load and why does it drive platform design?](./developer-experience/what-is-cognitive-load-and-why-does-it-drive-platform-design.md)                         | 🟡 Intermediate |
| 11  | [What is a service catalogue and why does a platform need one?](./developer-experience/what-is-a-service-catalogue-and-why-does-a-platform-need-one.md)                         | 🟡 Intermediate |
| 12  | [What is Backstage and when is it the wrong choice?](./developer-experience/what-is-backstage-and-when-is-it-the-wrong-choice.md)                                               | 🟡 Intermediate |
| 13  | [How do you reduce the time it takes a new engineer to ship to production?](./developer-experience/how-do-you-reduce-the-time-it-takes-a-new-engineer-to-ship-to-production.md) | 🟡 Intermediate |
| 14  | [How do you design service scorecards that teams do not resent?](./developer-experience/how-do-you-design-service-scorecards-that-teams-do-not-resent.md)                       | 🔴 Advanced     |
| 15  | [How do you run documentation as a platform capability?](./developer-experience/how-do-you-run-documentation-as-a-platform-capability.md)                                       | 🟢 Beginner     |

</details>

### 🏗️ Platform Architecture

_14 questions_

<details>
<summary><b>Platform Architecture</b> · 8 questions · 🟢 1 🟡 3 🔴 4</summary>

[Open the Platform Architecture index →](./platform-architecture/README.md)

| No. | Question                                                                                                                                                                                   | Difficulty      |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------- |
| 16  | [What is the difference between a control plane and a data plane in a platform?](./platform-architecture/what-is-the-difference-between-a-control-plane-and-a-data-plane-in-a-platform.md) | 🟡 Intermediate |
| 17  | [How do you design the developer-facing API of a platform?](./platform-architecture/how-do-you-design-the-developer-facing-api-of-a-platform.md)                                           | 🔴 Advanced     |
| 18  | [How do you keep a platform abstraction escapable?](./platform-architecture/how-do-you-keep-a-platform-abstraction-escapable.md)                                                           | 🔴 Advanced     |
| 19  | [How do you version a platform interface and migrate consumers?](./platform-architecture/how-do-you-version-a-platform-interface-and-migrate-consumers.md)                                 | 🔴 Advanced     |
| 20  | [When should a platform capability be a service, a library, or a template?](./platform-architecture/when-should-a-platform-capability-be-a-service-a-library-or-a-template.md)             | 🟡 Intermediate |
| 21  | [How do you write an architecture decision record for a platform choice?](./platform-architecture/how-do-you-write-an-architecture-decision-record-for-a-platform-choice.md)               | 🟢 Beginner     |
| 22  | [How do you choose a datastore for a platform service?](./platform-architecture/how-do-you-choose-a-datastore-for-a-platform-service.md)                                                   | 🟡 Intermediate |
| 23  | [How do you decide whether to build or buy a platform capability?](./platform-architecture/how-do-you-decide-whether-to-build-or-buy-a-platform-capability.md)                             | 🔴 Advanced     |

</details>

<details>
<summary><b>Multi-Tenancy and Isolation</b> · 6 questions · 🟢 0 🟡 2 🔴 4</summary>

[Open the Multi-Tenancy and Isolation index →](./multi-tenancy-and-isolation/README.md)

| No. | Question                                                                                                                                                               | Difficulty      |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 24  | [What tenancy models can a platform offer?](./multi-tenancy-and-isolation/what-tenancy-models-can-a-platform-offer.md)                                                 | 🟡 Intermediate |
| 25  | [When do you give a tenant its own cluster instead of a namespace?](./multi-tenancy-and-isolation/when-do-you-give-a-tenant-its-own-cluster-instead-of-a-namespace.md) | 🔴 Advanced     |
| 26  | [How do you stop one tenant degrading another?](./multi-tenancy-and-isolation/how-do-you-stop-one-tenant-degrading-another.md)                                         | 🔴 Advanced     |
| 27  | [How do you isolate tenants at the network layer?](./multi-tenancy-and-isolation/how-do-you-isolate-tenants-at-the-network-layer.md)                                   | 🟡 Intermediate |
| 28  | [How do you isolate tenant identity and data?](./multi-tenancy-and-isolation/how-do-you-isolate-tenant-identity-and-data.md)                                           | 🔴 Advanced     |
| 29  | [How do you design tenant onboarding and offboarding?](./multi-tenancy-and-isolation/how-do-you-design-tenant-onboarding-and-offboarding.md)                           | 🔴 Advanced     |

</details>

### ☸️ Kubernetes and Control Planes

_14 questions_

<details>
<summary><b>Kubernetes Platform</b> · 8 questions · 🟢 1 🟡 2 🔴 5</summary>

[Open the Kubernetes Platform index →](./kubernetes-platform/README.md)

| No. | Question                                                                                                                                                             | Difficulty      |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 30  | [Why does Kubernetes end up as the substrate for most platforms?](./kubernetes-platform/why-does-kubernetes-end-up-as-the-substrate-for-most-platforms.md)           | 🟢 Beginner     |
| 31  | [How do you design cluster topology for a platform?](./kubernetes-platform/how-do-you-design-cluster-topology-for-a-platform.md)                                     | 🔴 Advanced     |
| 32  | [How do you design node pools and scheduling for mixed workloads?](./kubernetes-platform/how-do-you-design-node-pools-and-scheduling-for-mixed-workloads.md)         | 🟡 Intermediate |
| 33  | [How do you upgrade a fleet of clusters without breaking tenants?](./kubernetes-platform/how-do-you-upgrade-a-fleet-of-clusters-without-breaking-tenants.md)         | 🔴 Advanced     |
| 34  | [What is admission control and how do you use it as a platform lever?](./kubernetes-platform/what-is-admission-control-and-how-do-you-use-it-as-a-platform-lever.md) | 🟡 Intermediate |
| 35  | [When should you write a Kubernetes operator?](./kubernetes-platform/when-should-you-write-a-kubernetes-operator.md)                                                 | 🔴 Advanced     |
| 36  | [How do you run a service mesh as a platform capability?](./kubernetes-platform/how-do-you-run-a-service-mesh-as-a-platform-capability.md)                           | 🔴 Advanced     |
| 37  | [How do you keep platform components consistent across many clusters?](./kubernetes-platform/how-do-you-keep-platform-components-consistent-across-many-clusters.md) | 🔴 Advanced     |

</details>

<details>
<summary><b>Control Planes and Abstractions</b> · 6 questions · 🟢 0 🟡 1 🔴 5</summary>

[Open the Control Planes and Abstractions index →](./control-planes-and-abstractions/README.md)

| No. | Question                                                                                                                                                                                                           | Difficulty      |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------- |
| 38  | [What is Crossplane and how does it differ from Terraform?](./control-planes-and-abstractions/what-is-crossplane-and-how-does-it-differ-from-terraform.md)                                                         | 🔴 Advanced     |
| 39  | [How do you model a platform API with Kubernetes custom resources?](./control-planes-and-abstractions/how-do-you-model-a-platform-api-with-kubernetes-custom-resources.md)                                         | 🔴 Advanced     |
| 40  | [What problem does a workload specification like Score solve?](./control-planes-and-abstractions/what-problem-does-a-workload-specification-like-score-solve.md)                                                   | 🟡 Intermediate |
| 41  | [How do you manage Terraform at platform scale?](./control-planes-and-abstractions/how-do-you-manage-terraform-at-platform-scale.md)                                                                               | 🔴 Advanced     |
| 42  | [How do you handle resource deletion safely in a control plane?](./control-planes-and-abstractions/how-do-you-handle-resource-deletion-safely-in-a-control-plane.md)                                               | 🔴 Advanced     |
| 43  | [How do you provide self-service infrastructure without handing out cloud credentials?](./control-planes-and-abstractions/how-do-you-provide-self-service-infrastructure-without-handing-out-cloud-credentials.md) | 🔴 Advanced     |

</details>

### 🔁 Delivery and Progressive Rollout

_22 questions_

<details>
<summary><b>GitOps and Continuous Delivery</b> · 8 questions · 🟢 1 🟡 4 🔴 3</summary>

[Open the GitOps and Continuous Delivery index →](./gitops-and-continuous-delivery/README.md)

| No. | Question                                                                                                                                                                                          | Difficulty      |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 44  | [What is GitOps and what does it actually guarantee?](./gitops-and-continuous-delivery/what-is-gitops-and-what-does-it-actually-guarantee.md)                                                     | 🟢 Beginner     |
| 45  | [How do Argo CD and Flux differ, and how do you choose?](./gitops-and-continuous-delivery/how-do-argo-cd-and-flux-differ-and-how-do-you-choose.md)                                                | 🟡 Intermediate |
| 46  | [How do you structure repositories for GitOps at scale?](./gitops-and-continuous-delivery/how-do-you-structure-repositories-for-gitops-at-scale.md)                                               | 🔴 Advanced     |
| 47  | [How do you promote a change from staging to production in GitOps?](./gitops-and-continuous-delivery/how-do-you-promote-a-change-from-staging-to-production-in-gitops.md)                         | 🔴 Advanced     |
| 48  | [How do you handle secrets in a GitOps workflow?](./gitops-and-continuous-delivery/how-do-you-handle-secrets-in-a-gitops-workflow.md)                                                             | 🟡 Intermediate |
| 49  | [What is configuration drift and how does a platform detect it?](./gitops-and-continuous-delivery/what-is-configuration-drift-and-how-does-a-platform-detect-it.md)                               | 🟡 Intermediate |
| 50  | [How do you keep templated manifests reviewable?](./gitops-and-continuous-delivery/how-do-you-keep-templated-manifests-reviewable.md)                                                             | 🟡 Intermediate |
| 51  | [How do you give teams self-service pipelines without maintaining 200 of them?](./gitops-and-continuous-delivery/how-do-you-give-teams-self-service-pipelines-without-maintaining-200-of-them.md) | 🔴 Advanced     |

</details>

<details>
<summary><b>Progressive Delivery and Feature Flags</b> · 8 questions · 🟢 0 🟡 2 🔴 6</summary>

[Open the Progressive Delivery and Feature Flags index →](./progressive-delivery-and-feature-flags/README.md)

| No. | Question                                                                                                                                                                      | Difficulty      |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 52  | [How do you run feature flags as a platform capability?](./progressive-delivery-and-feature-flags/how-do-you-run-feature-flags-as-a-platform-capability.md)                   | 🔴 Advanced     |
| 53  | [How do you manage feature flag debt?](./progressive-delivery-and-feature-flags/how-do-you-manage-feature-flag-debt.md)                                                       | 🔴 Advanced     |
| 54  | [How do you design a progressive rollout and its abort criteria?](./progressive-delivery-and-feature-flags/how-do-you-design-a-progressive-rollout-and-its-abort-criteria.md) | 🔴 Advanced     |
| 55  | [How do you design a kill switch you can trust?](./progressive-delivery-and-feature-flags/how-do-you-design-a-kill-switch-you-can-trust.md)                                   | 🔴 Advanced     |
| 56  | [When do you use a feature flag instead of a canary deployment?](./progressive-delivery-and-feature-flags/when-do-you-use-a-feature-flag-instead-of-a-canary-deployment.md)   | 🟡 Intermediate |
| 57  | [How do you keep percentage rollouts consistent across services?](./progressive-delivery-and-feature-flags/how-do-you-keep-percentage-rollouts-consistent-across-services.md) | 🔴 Advanced     |
| 58  | [What can a feature flag not roll back?](./progressive-delivery-and-feature-flags/what-can-a-feature-flag-not-roll-back.md)                                                   | 🔴 Advanced     |
| 59  | [How do you test code that sits behind feature flags?](./progressive-delivery-and-feature-flags/how-do-you-test-code-that-sits-behind-feature-flags.md)                       | 🟡 Intermediate |

</details>

<details>
<summary><b>Environments and Ephemeral Infrastructure</b> · 6 questions · 🟢 0 🟡 4 🔴 2</summary>

[Open the Environments and Ephemeral Infrastructure index →](./environments-and-ephemeral-infrastructure/README.md)

| No. | Question                                                                                                                                                                         | Difficulty      |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 60  | [What is an ephemeral environment and when is it worth it?](./environments-and-ephemeral-infrastructure/what-is-an-ephemeral-environment-and-when-is-it-worth-it.md)             | 🟡 Intermediate |
| 61  | [How do you build preview environments for every pull request?](./environments-and-ephemeral-infrastructure/how-do-you-build-preview-environments-for-every-pull-request.md)     | 🔴 Advanced     |
| 62  | [How do you seed realistic test data without copying production?](./environments-and-ephemeral-infrastructure/how-do-you-seed-realistic-test-data-without-copying-production.md) | 🔴 Advanced     |
| 63  | [What does environment parity actually require?](./environments-and-ephemeral-infrastructure/what-does-environment-parity-actually-require.md)                                   | 🟡 Intermediate |
| 64  | [How do you stop ephemeral environments becoming a cost problem?](./environments-and-ephemeral-infrastructure/how-do-you-stop-ephemeral-environments-becoming-a-cost-problem.md) | 🟡 Intermediate |
| 65  | [How do you give developers a fast inner development loop?](./environments-and-ephemeral-infrastructure/how-do-you-give-developers-a-fast-inner-development-loop.md)             | 🟡 Intermediate |

</details>

### 🔐 Security and Governance

_14 questions_

<details>
<summary><b>Platform Security</b> · 8 questions · 🟢 0 🟡 2 🔴 6</summary>

[Open the Platform Security index →](./platform-security/README.md)

| No. | Question                                                                                                                                                                                   | Difficulty      |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------- |
| 66  | [How does a platform provide workload identity without long-lived credentials?](./platform-security/how-does-a-platform-provide-workload-identity-without-long-lived-credentials.md)       | 🔴 Advanced     |
| 67  | [How do you run a secretless CI/CD pipeline?](./platform-security/how-do-you-run-a-secretless-ci-cd-pipeline.md)                                                                           | 🔴 Advanced     |
| 68  | [How do you manage secrets as a platform capability?](./platform-security/how-do-you-manage-secrets-as-a-platform-capability.md)                                                           | 🟡 Intermediate |
| 69  | [How do you secure the software supply chain for everything the platform builds?](./platform-security/how-do-you-secure-the-software-supply-chain-for-everything-the-platform-builds.md)   | 🔴 Advanced     |
| 70  | [How do you keep base images patched across every team?](./platform-security/how-do-you-keep-base-images-patched-across-every-team.md)                                                     | 🟡 Intermediate |
| 71  | [How do you respond to a critical CVE that affects every service on the platform?](./platform-security/how-do-you-respond-to-a-critical-cve-that-affects-every-service-on-the-platform.md) | 🔴 Advanced     |
| 72  | [How do you design break-glass access to production?](./platform-security/how-do-you-design-break-glass-access-to-production.md)                                                           | 🔴 Advanced     |
| 73  | [How do you threat model a platform?](./platform-security/how-do-you-threat-model-a-platform.md)                                                                                           | 🔴 Advanced     |

</details>

<details>
<summary><b>Policy as Code and Governance</b> · 6 questions · 🟢 0 🟡 4 🔴 2</summary>

[Open the Policy as Code and Governance index →](./policy-as-code-and-governance/README.md)

| No. | Question                                                                                                                                                                               | Difficulty      |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 74  | [What is policy as code and where does it belong in a platform?](./policy-as-code-and-governance/what-is-policy-as-code-and-where-does-it-belong-in-a-platform.md)                     | 🟡 Intermediate |
| 75  | [How do Gatekeeper and Kyverno differ, and how do you choose?](./policy-as-code-and-governance/how-do-gatekeeper-and-kyverno-differ-and-how-do-you-choose.md)                          | 🟡 Intermediate |
| 76  | [How do you roll out a new policy without breaking every team?](./policy-as-code-and-governance/how-do-you-roll-out-a-new-policy-without-breaking-every-team.md)                       | 🔴 Advanced     |
| 77  | [How do you turn a compliance framework into automated platform controls?](./policy-as-code-and-governance/how-do-you-turn-a-compliance-framework-into-automated-platform-controls.md) | 🔴 Advanced     |
| 78  | [How do you handle policy exceptions without eroding the guardrails?](./policy-as-code-and-governance/how-do-you-handle-policy-exceptions-without-eroding-the-guardrails.md)           | 🟡 Intermediate |
| 79  | [What audit trail does a platform owe its auditors?](./policy-as-code-and-governance/what-audit-trail-does-a-platform-owe-its-auditors.md)                                             | 🟡 Intermediate |

</details>

### ☁️ Cloud Platforms

_24 questions_

<details>
<summary><b>AWS Platform Engineering</b> · 7 questions · 🟢 0 🟡 3 🔴 4</summary>

[Open the AWS Platform Engineering index →](./aws-platform-engineering/README.md)

| No. | Question                                                                                                                                                                                           | Difficulty      |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 80  | [How do you structure a multi-account AWS platform?](./aws-platform-engineering/how-do-you-structure-a-multi-account-aws-platform.md)                                                              | 🔴 Advanced     |
| 81  | [What is account vending and how do you automate it?](./aws-platform-engineering/what-is-account-vending-and-how-do-you-automate-it.md)                                                            | 🔴 Advanced     |
| 82  | [How do you give pods on EKS access to AWS resources safely?](./aws-platform-engineering/how-do-you-give-pods-on-eks-access-to-aws-resources-safely.md)                                            | 🟡 Intermediate |
| 83  | [How do you choose between ECS, EKS, Lambda, and App Runner for a platform runtime?](./aws-platform-engineering/how-do-you-choose-between-ecs-eks-lambda-and-app-runner-for-a-platform-runtime.md) | 🟡 Intermediate |
| 84  | [How do you manage EKS node capacity with Karpenter?](./aws-platform-engineering/how-do-you-manage-eks-node-capacity-with-karpenter.md)                                                            | 🔴 Advanced     |
| 85  | [How do you build a paved road for AWS infrastructure self-service?](./aws-platform-engineering/how-do-you-build-a-paved-road-for-aws-infrastructure-self-service.md)                              | 🔴 Advanced     |
| 86  | [How do you allocate AWS cost back to teams?](./aws-platform-engineering/how-do-you-allocate-aws-cost-back-to-teams.md)                                                                            | 🟡 Intermediate |

</details>

<details>
<summary><b>Azure Platform Engineering</b> · 6 questions · 🟢 0 🟡 3 🔴 3</summary>

[Open the Azure Platform Engineering index →](./azure-platform-engineering/README.md)

| No. | Question                                                                                                                                                                                            | Difficulty      |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 87  | [How do you structure an Azure platform with management groups and landing zones?](./azure-platform-engineering/how-do-you-structure-an-azure-platform-with-management-groups-and-landing-zones.md) | 🔴 Advanced     |
| 88  | [How do you use Azure Policy as a platform guardrail?](./azure-platform-engineering/how-do-you-use-azure-policy-as-a-platform-guardrail.md)                                                         | 🟡 Intermediate |
| 89  | [How do workload identities work on AKS?](./azure-platform-engineering/how-do-workload-identities-work-on-aks.md)                                                                                   | 🟡 Intermediate |
| 90  | [How do you choose between AKS, Container Apps, App Service, and Functions?](./azure-platform-engineering/how-do-you-choose-between-aks-container-apps-app-service-and-functions.md)                | 🟡 Intermediate |
| 91  | [How do you use Bicep for platform modules and subscription vending?](./azure-platform-engineering/how-do-you-use-bicep-for-platform-modules-and-subscription-vending.md)                           | 🔴 Advanced     |
| 92  | [How do you design private networking for Azure PaaS services?](./azure-platform-engineering/how-do-you-design-private-networking-for-azure-paas-services.md)                                       | 🔴 Advanced     |

</details>

<details>
<summary><b>GCP Platform Engineering</b> · 6 questions · 🟢 0 🟡 3 🔴 3</summary>

[Open the GCP Platform Engineering index →](./gcp-platform-engineering/README.md)

| No. | Question                                                                                                                                                                                                    | Difficulty      |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 93  | [How do you structure a GCP platform with folders, projects, and organisation policies?](./gcp-platform-engineering/how-do-you-structure-a-gcp-platform-with-folders-projects-and-organisation-policies.md) | 🔴 Advanced     |
| 94  | [How does Workload Identity Federation remove service account keys?](./gcp-platform-engineering/how-does-workload-identity-federation-remove-service-account-keys.md)                                       | 🟡 Intermediate |
| 95  | [How do you choose between GKE, GKE Autopilot, and Cloud Run?](./gcp-platform-engineering/how-do-you-choose-between-gke-gke-autopilot-and-cloud-run.md)                                                     | 🟡 Intermediate |
| 96  | [How do you design Shared VPC for a multi-team GCP platform?](./gcp-platform-engineering/how-do-you-design-shared-vpc-for-a-multi-team-gcp-platform.md)                                                     | 🔴 Advanced     |
| 97  | [How do you use Config Connector and Config Sync as a GCP control plane?](./gcp-platform-engineering/how-do-you-use-config-connector-and-config-sync-as-a-gcp-control-plane.md)                             | 🔴 Advanced     |
| 98  | [How do you automate project vending on GCP?](./gcp-platform-engineering/how-do-you-automate-project-vending-on-gcp.md)                                                                                     | 🟡 Intermediate |

</details>

<details>
<summary><b>Multi-Cloud and Hybrid Platforms</b> · 5 questions · 🟢 0 🟡 2 🔴 3</summary>

[Open the Multi-Cloud and Hybrid Platforms index →](./multi-cloud-and-hybrid-platforms/README.md)

| No. | Question                                                                                                                                                                        | Difficulty      |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 99  | [When is multi-cloud a real requirement rather than a slogan?](./multi-cloud-and-hybrid-platforms/when-is-multi-cloud-a-real-requirement-rather-than-a-slogan.md)               | 🟡 Intermediate |
| 100 | [What does a genuinely portable platform abstraction cost you?](./multi-cloud-and-hybrid-platforms/what-does-a-genuinely-portable-platform-abstraction-cost-you.md)             | 🔴 Advanced     |
| 101 | [How do you map equivalent primitives across AWS, Azure, and GCP?](./multi-cloud-and-hybrid-platforms/how-do-you-map-equivalent-primitives-across-aws-azure-and-gcp.md)         | 🟡 Intermediate |
| 102 | [How do you design a hybrid platform spanning on-premises and cloud?](./multi-cloud-and-hybrid-platforms/how-do-you-design-a-hybrid-platform-spanning-on-premises-and-cloud.md) | 🔴 Advanced     |
| 103 | [How does data gravity constrain platform design?](./multi-cloud-and-hybrid-platforms/how-does-data-gravity-constrain-platform-design.md)                                       | 🔴 Advanced     |

</details>

### 📈 Reliability and Observability

_13 questions_

<details>
<summary><b>Platform Reliability</b> · 7 questions · 🟢 0 🟡 2 🔴 5</summary>

[Open the Platform Reliability index →](./platform-reliability/README.md)

| No. | Question                                                                                                                                                                      | Difficulty      |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 104 | [How do you define SLOs for a platform rather than an application?](./platform-reliability/how-do-you-define-slos-for-a-platform-rather-than-an-application.md)               | 🔴 Advanced     |
| 105 | [What does an error budget policy look like for a platform team?](./platform-reliability/what-does-an-error-budget-policy-look-like-for-a-platform-team.md)                   | 🔴 Advanced     |
| 106 | [How do you run on-call for a platform team?](./platform-reliability/how-do-you-run-on-call-for-a-platform-team.md)                                                           | 🟡 Intermediate |
| 107 | [How do you run an incident when the platform itself is the incident?](./platform-reliability/how-do-you-run-an-incident-when-the-platform-itself-is-the-incident.md)         | 🔴 Advanced     |
| 108 | [How do you make a platform degrade gracefully instead of failing closed?](./platform-reliability/how-do-you-make-a-platform-degrade-gracefully-instead-of-failing-closed.md) | 🔴 Advanced     |
| 109 | [How do you plan disaster recovery for the platform itself?](./platform-reliability/how-do-you-plan-disaster-recovery-for-the-platform-itself.md)                             | 🔴 Advanced     |
| 110 | [How do you use chaos engineering to test platform guarantees?](./platform-reliability/how-do-you-use-chaos-engineering-to-test-platform-guarantees.md)                       | 🟡 Intermediate |

</details>

<details>
<summary><b>Platform Observability</b> · 6 questions · 🟢 0 🟡 3 🔴 3</summary>

[Open the Platform Observability index →](./platform-observability/README.md)

| No. | Question                                                                                                                                                                      | Difficulty      |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 111 | [How do you provide observability as a platform capability?](./platform-observability/how-do-you-provide-observability-as-a-platform-capability.md)                           | 🟡 Intermediate |
| 112 | [How do you run an OpenTelemetry collector as a platform service?](./platform-observability/how-do-you-run-an-opentelemetry-collector-as-a-platform-service.md)               | 🔴 Advanced     |
| 113 | [How do you control metric cardinality and observability cost?](./platform-observability/how-do-you-control-metric-cardinality-and-observability-cost.md)                     | 🔴 Advanced     |
| 114 | [What telemetry should every service get without writing code?](./platform-observability/what-telemetry-should-every-service-get-without-writing-code.md)                     | 🟡 Intermediate |
| 115 | [How do you make traces useful across team boundaries?](./platform-observability/how-do-you-make-traces-useful-across-team-boundaries.md)                                     | 🔴 Advanced     |
| 116 | [How do you give teams visibility into platform state that affects them?](./platform-observability/how-do-you-give-teams-visibility-into-platform-state-that-affects-them.md) | 🟡 Intermediate |

</details>

### 💰 Economics and Operating Model

_13 questions_

<details>
<summary><b>Platform FinOps</b> · 6 questions · 🟢 1 🟡 2 🔴 3</summary>

[Open the Platform FinOps index →](./platform-finops/README.md)

| No. | Question                                                                                                                                                                | Difficulty      |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 117 | [What is FinOps and what part of it does a platform team own?](./platform-finops/what-is-finops-and-what-part-of-it-does-a-platform-team-own.md)                        | 🟢 Beginner     |
| 118 | [How do you attribute shared platform cost to teams?](./platform-finops/how-do-you-attribute-shared-platform-cost-to-teams.md)                                          | 🔴 Advanced     |
| 119 | [What is the difference between showback and chargeback, and which works?](./platform-finops/what-is-the-difference-between-showback-and-chargeback-and-which-works.md) | 🟡 Intermediate |
| 120 | [How do you build unit economics for a platform?](./platform-finops/how-do-you-build-unit-economics-for-a-platform.md)                                                  | 🔴 Advanced     |
| 121 | [How do you use commitments and spot capacity on behalf of every team?](./platform-finops/how-do-you-use-commitments-and-spot-capacity-on-behalf-of-every-team.md)      | 🔴 Advanced     |
| 122 | [How do you find and remove idle platform cost?](./platform-finops/how-do-you-find-and-remove-idle-platform-cost.md)                                                    | 🟡 Intermediate |

</details>

<details>
<summary><b>Platform Team and Operating Model</b> · 7 questions · 🟢 1 🟡 3 🔴 3</summary>

[Open the Platform Team and Operating Model index →](./platform-team-and-operating-model/README.md)

| No. | Question                                                                                                                                                             | Difficulty      |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 123 | [What does Team Topologies say about platform teams?](./platform-team-and-operating-model/what-does-team-topologies-say-about-platform-teams.md)                     | 🟢 Beginner     |
| 124 | [How do you size and staff a platform team?](./platform-team-and-operating-model/how-do-you-size-and-staff-a-platform-team.md)                                       | 🟡 Intermediate |
| 125 | [How do you measure platform adoption and success?](./platform-team-and-operating-model/how-do-you-measure-platform-adoption-and-success.md)                         | 🟡 Intermediate |
| 126 | [How do you migrate teams onto the platform without a mandate?](./platform-team-and-operating-model/how-do-you-migrate-teams-onto-the-platform-without-a-mandate.md) | 🔴 Advanced     |
| 127 | [How do you deprecate a platform capability?](./platform-team-and-operating-model/how-do-you-deprecate-a-platform-capability.md)                                     | 🔴 Advanced     |
| 128 | [How do you run an RFC process for platform decisions?](./platform-team-and-operating-model/how-do-you-run-an-rfc-process-for-platform-decisions.md)                 | 🟡 Intermediate |
| 129 | [How do you build a platform roadmap and say no?](./platform-team-and-operating-model/how-do-you-build-a-platform-roadmap-and-say-no.md)                             | 🔴 Advanced     |

</details>

### 🎤 Interview Prep

_7 questions_

<details>
<summary><b>Platform Engineering Interviews</b> · 7 questions · 🟢 2 🟡 3 🔴 2</summary>

[Open the Platform Engineering Interviews index →](./platform-engineering-interviews/README.md)

| No. | Question                                                                                                                                                               | Difficulty      |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 130 | [What does a platform engineering interview loop look like?](./platform-engineering-interviews/what-does-a-platform-engineering-interview-loop-look-like.md)           | 🟢 Beginner     |
| 131 | [How do you answer a platform design interview question?](./platform-engineering-interviews/how-do-you-answer-a-platform-design-interview-question.md)                 | 🔴 Advanced     |
| 132 | [How do you present platform work you have done?](./platform-engineering-interviews/how-do-you-present-platform-work-you-have-done.md)                                 | 🟡 Intermediate |
| 133 | [How do you answer 'how would you build a platform from scratch'?](./platform-engineering-interviews/how-do-you-answer-how-would-you-build-a-platform-from-scratch.md) | 🔴 Advanced     |
| 134 | [How do you handle a troubleshooting round?](./platform-engineering-interviews/how-do-you-handle-a-troubleshooting-round.md)                                           | 🟡 Intermediate |
| 135 | [What behavioural questions do platform interviews ask, and why?](./platform-engineering-interviews/what-behavioural-questions-do-platform-interviews-ask-and-why.md)  | 🟡 Intermediate |
| 136 | [What should you ask your interviewer about their platform?](./platform-engineering-interviews/what-should-you-ask-your-interviewer-about-their-platform.md)           | 🟢 Beginner     |

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

Difficulty is marked 🟢 Beginner · 🟡 Intermediate · 🔴 Advanced. The distribution skews senior, because the field does: most platform roles are filled at senior and above, and the interesting questions are about judgement rather than recall.

**Three ways to work through it:**

- **Preparing for a specific role** - take the track from [Pick your role](#-pick-your-role), and read each topic README's "What interviewers probe here" before its questions.
- **Broad revision** - read the short answers across a topic, then go deep only where you hesitate.
- **Obsidian / note vault** - every file carries YAML frontmatter (`title`, `id`, `category`, `difficulty`, `tags`), so the whole repository can be dropped into a vault and browsed by tag.

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
│   └── topic_meta.json                  # topic registry: order, group, description, study notes
└── .github/workflows/
    └── validate-and-format.yml          # runs validation + Prettier on every PR
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
python3 scripts/generate_indexes.py     # rewrite all indexes
python3 scripts/validate_content.py     # verify frontmatter, naming, links, index freshness
```

Both are stdlib-only Python 3.11+ - no dependencies to install. CI runs the same commands and fails the pull request on drift.

---

## 🤝 Contributing

New questions, better answers, and corrections are all welcome. [CONTRIBUTING.md](./CONTRIBUTING.md) covers the file format, naming rules, and the local checks to run before opening a pull request.

Not sure where to start? Open an issue - there are templates for [a new question](https://github.com/mchittineni/ultimate-platform-engineering-guide/issues/new?template=1-new-question.yml), [a correction to an existing answer](https://github.com/mchittineni/ultimate-platform-engineering-guide/issues/new?template=2-improve-answer.yml), [a new topic](https://github.com/mchittineni/ultimate-platform-engineering-guide/issues/new?template=3-new-topic.yml), and [broken links or tooling](https://github.com/mchittineni/ultimate-platform-engineering-guide/issues/new?template=4-bug-or-tooling.yml).

Two documents set the ground rules: the [Code of Conduct](./CODE_OF_CONDUCT.md) - including the rules on interviewer privacy, NDAs, and plagiarism - and the [Security Policy](./SECURITY.md), which covers how to report a committed credential, a workflow vulnerability, or a dangerously over-permissive example policy privately.

## 🧭 Related

- **[Ultimate DevOps Guide](https://github.com/mchittineni/ultimate-devops-guide)** - the sibling repository, covering DevOps, SRE, DevSecOps, and cloud engineering interview questions with the same structure and tooling. Start there for container, CI/CD, Linux, and networking fundamentals; this guide assumes them.

## 🙏 Acknowledgements

The vocabulary this guide uses is not invented here. It leans on the work of the platform engineering community:

- **[Team Topologies](https://teamtopologies.com/)** by Matthew Skelton and Manuel Pais - platform teams as enabling teams, cognitive load as the design constraint, and the thinnest viable platform.
- **[CNCF Platforms Working Group](https://tag-app-delivery.cncf.io/whitepapers/platforms/)** - the platform maturity model and the capability-plane vocabulary.
- **[Google SRE](https://sre.google/books/)** - SLOs, error budgets, and the toil framing that platform reliability builds on.
- **[OpenFeature](https://openfeature.dev/)**, **[OpenTelemetry](https://opentelemetry.io/)**, **[Crossplane](https://www.crossplane.io/)**, **[Backstage](https://backstage.io/)**, and **[Argo CD](https://argo-cd.readthedocs.io/)** - the open standards and projects most of these answers reference.
- **[DORA](https://dora.dev/)** - the delivery metrics used throughout to argue about outcomes rather than output.

## 📄 License

Released under the [MIT License](./LICENSE).
