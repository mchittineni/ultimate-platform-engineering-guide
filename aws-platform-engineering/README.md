---
title: "AWS Platform Engineering"
category: "AWS Platform Engineering"
tags:
  - platform-engineering
  - aws-platform-engineering
  - index
---

# AWS Platform Engineering

Building a platform on AWS: multi-account organisation design, account vending, EKS pod identity, runtime selection, Karpenter capacity, paved-road self-service, and cost allocation.

**7 questions** · 🟢 Beginner: 0 · 🟡 Intermediate: 3 · 🔴 Advanced: 4

## Questions

| #   | Question                                                                                                                                                                  | Difficulty      |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 80  | [How do you structure a multi-account AWS platform?](./how-do-you-structure-a-multi-account-aws-platform.md)                                                              | 🔴 Advanced     |
| 81  | [What is account vending and how do you automate it?](./what-is-account-vending-and-how-do-you-automate-it.md)                                                            | 🔴 Advanced     |
| 82  | [How do you give pods on EKS access to AWS resources safely?](./how-do-you-give-pods-on-eks-access-to-aws-resources-safely.md)                                            | 🟡 Intermediate |
| 83  | [How do you choose between ECS, EKS, Lambda, and App Runner for a platform runtime?](./how-do-you-choose-between-ecs-eks-lambda-and-app-runner-for-a-platform-runtime.md) | 🟡 Intermediate |
| 84  | [How do you manage EKS node capacity with Karpenter?](./how-do-you-manage-eks-node-capacity-with-karpenter.md)                                                            | 🔴 Advanced     |
| 85  | [How do you build a paved road for AWS infrastructure self-service?](./how-do-you-build-a-paved-road-for-aws-infrastructure-self-service.md)                              | 🔴 Advanced     |
| 86  | [How do you allocate AWS cost back to teams?](./how-do-you-allocate-aws-cost-back-to-teams.md)                                                                            | 🟡 Intermediate |

## What interviewers probe here

- Why the account is the primary isolation boundary on AWS.
- How a pod gets AWS permissions without an access key.
- The runtime decision between ECS, EKS, Lambda, and App Runner.

---

[⬅ Back to all topics](../README.md)
