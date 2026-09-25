---
title: "GitOps and Continuous Delivery"
category: "GitOps and Continuous Delivery"
tags:
  - platform-engineering
  - gitops-and-continuous-delivery
  - index
---

# GitOps and Continuous Delivery

Git as the source of truth: Argo CD and Flux, repository structure at scale, environment promotion, secrets, drift detection, and self-service pipelines that do not multiply.

**13 questions** · 🟢 Beginner: 5 · 🟡 Intermediate: 5 · 🔴 Advanced: 3

## Questions

| #   | Question                                                                                                                                                                                                           | Difficulty      |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------- |
| 79  | [What is GitOps and what does it actually guarantee?](./what-is-gitops-and-what-does-it-actually-guarantee.md)                                                                                                     | 🟢 Beginner     |
| 80  | [What is the difference between continuous integration, continuous delivery, and continuous deployment?](./what-is-the-difference-between-continuous-integration-continuous-delivery-and-continuous-deployment.md) | 🟢 Beginner     |
| 81  | [What is Helm and what problem does it solve?](./what-is-helm-and-what-problem-does-it-solve.md)                                                                                                                   | 🟢 Beginner     |
| 82  | [What is Kustomize and how does it differ from Helm?](./what-is-kustomize-and-how-does-it-differ-from-helm.md)                                                                                                     | 🟢 Beginner     |
| 83  | [What is the difference between push-based and pull-based deployment?](./what-is-the-difference-between-push-based-and-pull-based-deployment.md)                                                                   | 🟢 Beginner     |
| 84  | [How do Argo CD and Flux differ, and how do you choose?](./how-do-argo-cd-and-flux-differ-and-how-do-you-choose.md)                                                                                                | 🟡 Intermediate |
| 85  | [How do you handle secrets in a GitOps workflow?](./how-do-you-handle-secrets-in-a-gitops-workflow.md)                                                                                                             | 🟡 Intermediate |
| 86  | [What is configuration drift and how does a platform detect it?](./what-is-configuration-drift-and-how-does-a-platform-detect-it.md)                                                                               | 🟡 Intermediate |
| 87  | [How do you keep templated manifests reviewable?](./how-do-you-keep-templated-manifests-reviewable.md)                                                                                                             | 🟡 Intermediate |
| 88  | [How do you use Argo CD ApplicationSets to manage many clusters?](./how-do-you-use-argo-cd-applicationsets-to-manage-many-clusters.md)                                                                             | 🟡 Intermediate |
| 89  | [How do you structure repositories for GitOps at scale?](./how-do-you-structure-repositories-for-gitops-at-scale.md)                                                                                               | 🔴 Advanced     |
| 90  | [How do you promote a change from staging to production in GitOps?](./how-do-you-promote-a-change-from-staging-to-production-in-gitops.md)                                                                         | 🔴 Advanced     |
| 91  | [How do you give teams self-service pipelines without maintaining 200 of them?](./how-do-you-give-teams-self-service-pipelines-without-maintaining-200-of-them.md)                                                 | 🔴 Advanced     |

## What interviewers probe here

- What GitOps actually guarantees, and what it does not.
- How a change is promoted between environments without copy-paste.
- Where secrets live when the desired state is in a public-ish repo.

---

[⬅ Back to all topics](../README.md)
