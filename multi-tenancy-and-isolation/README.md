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

**6 questions** · 🟢 Beginner: 0 · 🟡 Intermediate: 2 · 🔴 Advanced: 4

## Questions

| #   | Question                                                                                                                                   | Difficulty      |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------ | --------------- |
| 24  | [What tenancy models can a platform offer?](./what-tenancy-models-can-a-platform-offer.md)                                                 | 🟡 Intermediate |
| 25  | [When do you give a tenant its own cluster instead of a namespace?](./when-do-you-give-a-tenant-its-own-cluster-instead-of-a-namespace.md) | 🔴 Advanced     |
| 26  | [How do you stop one tenant degrading another?](./how-do-you-stop-one-tenant-degrading-another.md)                                         | 🔴 Advanced     |
| 27  | [How do you isolate tenants at the network layer?](./how-do-you-isolate-tenants-at-the-network-layer.md)                                   | 🟡 Intermediate |
| 28  | [How do you isolate tenant identity and data?](./how-do-you-isolate-tenant-identity-and-data.md)                                           | 🔴 Advanced     |
| 29  | [How do you design tenant onboarding and offboarding?](./how-do-you-design-tenant-onboarding-and-offboarding.md)                           | 🔴 Advanced     |

## What interviewers probe here

- Which isolation boundary a given threat model actually requires.
- Why a Kubernetes namespace is a soft boundary, and what hardens it.
- How you offboard a tenant completely, including its data and cost trail.

---

[⬅ Back to all topics](../README.md)
