---
title: "Control Planes and Abstractions"
category: "Control Planes and Abstractions"
tags:
  - platform-engineering
  - control-planes-and-abstractions
  - index
---

# Control Planes and Abstractions

Turning infrastructure into a self-service API: Crossplane, custom resources as platform contracts, workload specifications, Terraform at scale, and safe resource lifecycle.

**13 questions** · 🟢 Beginner: 5 · 🟡 Intermediate: 3 · 🔴 Advanced: 5

## Questions

| #   | Question                                                                                                                                                                           | Difficulty      |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 66  | [What is infrastructure as code?](./what-is-infrastructure-as-code.md)                                                                                                             | 🟢 Beginner     |
| 67  | [What is a reconciliation loop?](./what-is-a-reconciliation-loop.md)                                                                                                               | 🟢 Beginner     |
| 68  | [What is a custom resource definition?](./what-is-a-custom-resource-definition.md)                                                                                                 | 🟢 Beginner     |
| 69  | [What is the difference between Terraform and OpenTofu?](./what-is-the-difference-between-terraform-and-opentofu.md)                                                               | 🟢 Beginner     |
| 70  | [What is Terraform state and why does it need protecting?](./what-is-terraform-state-and-why-does-it-need-protecting.md)                                                           | 🟢 Beginner     |
| 71  | [What problem does a workload specification like Score solve?](./what-problem-does-a-workload-specification-like-score-solve.md)                                                   | 🟡 Intermediate |
| 72  | [What changed in Crossplane v2 and why does it matter?](./what-changed-in-crossplane-v2-and-why-does-it-matter.md)                                                                 | 🟡 Intermediate |
| 73  | [How do kro, Crossplane compositions, and Helm charts differ for composing resources?](./how-do-kro-crossplane-compositions-and-helm-charts-differ-for-composing-resources.md)     | 🟡 Intermediate |
| 74  | [What is Crossplane and how does it differ from Terraform?](./what-is-crossplane-and-how-does-it-differ-from-terraform.md)                                                         | 🔴 Advanced     |
| 75  | [How do you model a platform API with Kubernetes custom resources?](./how-do-you-model-a-platform-api-with-kubernetes-custom-resources.md)                                         | 🔴 Advanced     |
| 76  | [How do you manage Terraform at platform scale?](./how-do-you-manage-terraform-at-platform-scale.md)                                                                               | 🔴 Advanced     |
| 77  | [How do you handle resource deletion safely in a control plane?](./how-do-you-handle-resource-deletion-safely-in-a-control-plane.md)                                               | 🔴 Advanced     |
| 78  | [How do you provide self-service infrastructure without handing out cloud credentials?](./how-do-you-provide-self-service-infrastructure-without-handing-out-cloud-credentials.md) | 🔴 Advanced     |

## What interviewers probe here

- Control-plane reconciliation versus run-to-completion IaC.
- How you expose infrastructure without handing out cloud credentials.
- What protects a stateful resource from an accidental delete.

---

[⬅ Back to all topics](../README.md)
