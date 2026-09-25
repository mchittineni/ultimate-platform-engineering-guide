---
title: "Multi-Tenancy and Isolation"
category: "Multi-Tenancy and Isolation"
tags:
  - platform-engineering
  - multi-tenancy-and-isolation
  - index
---

# Multi-Tenancy and Isolation

Sharing infrastructure without sharing blast radius: tenancy models, namespace versus cluster boundaries, noisy neighbours, quotas, network isolation, and per-tenant accounting.

**13 questions** · 🟢 Beginner: 5 · 🟡 Intermediate: 4 · 🔴 Advanced: 4

## Questions

| #   | Question                                                                                                                                   | Difficulty      |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------ | --------------- |
| 40  | [What is multi-tenancy and why do platforms need it?](./what-is-multi-tenancy-and-why-do-platforms-need-it.md)                             | 🟢 Beginner     |
| 41  | [What is a tenant, and how do you define one in a platform?](./what-is-a-tenant-and-how-do-you-define-one-in-a-platform.md)                | 🟢 Beginner     |
| 42  | [What does a Kubernetes namespace isolate, and what does it not?](./what-does-a-kubernetes-namespace-isolate-and-what-does-it-not.md)      | 🟢 Beginner     |
| 43  | [What are resource quotas and limit ranges?](./what-are-resource-quotas-and-limit-ranges.md)                                               | 🟢 Beginner     |
| 44  | [How does role-based access control scope what a tenant can do?](./how-does-role-based-access-control-scope-what-a-tenant-can-do.md)       | 🟢 Beginner     |
| 45  | [What tenancy models can a platform offer?](./what-tenancy-models-can-a-platform-offer.md)                                                 | 🟡 Intermediate |
| 46  | [How do you isolate tenants at the network layer?](./how-do-you-isolate-tenants-at-the-network-layer.md)                                   | 🟡 Intermediate |
| 47  | [How do virtual clusters change the tenancy trade-off?](./how-do-virtual-clusters-change-the-tenancy-trade-off.md)                         | 🟡 Intermediate |
| 48  | [How do Pod Security Standards harden a shared cluster?](./how-do-pod-security-standards-harden-a-shared-cluster.md)                       | 🟡 Intermediate |
| 49  | [When do you give a tenant its own cluster instead of a namespace?](./when-do-you-give-a-tenant-its-own-cluster-instead-of-a-namespace.md) | 🔴 Advanced     |
| 50  | [How do you stop one tenant degrading another?](./how-do-you-stop-one-tenant-degrading-another.md)                                         | 🔴 Advanced     |
| 51  | [How do you isolate tenant identity and data?](./how-do-you-isolate-tenant-identity-and-data.md)                                           | 🔴 Advanced     |
| 52  | [How do you design tenant onboarding and offboarding?](./how-do-you-design-tenant-onboarding-and-offboarding.md)                           | 🔴 Advanced     |

## What interviewers probe here

- Which isolation boundary a given threat model actually requires.
- Why a Kubernetes namespace is a soft boundary, and what hardens it.
- How you offboard a tenant completely, including its data and cost trail.

---

[⬅ Back to all topics](../README.md)
