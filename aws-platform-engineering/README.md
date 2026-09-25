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

**13 questions** · 🟢 Beginner: 5 · 🟡 Intermediate: 4 · 🔴 Advanced: 4

## Questions

| #   | Question                                                                                                                                                                  | Difficulty      |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 146 | [What are AWS Organizations and service control policies?](./what-are-aws-organizations-and-service-control-policies.md)                                                  | 🟢 Beginner     |
| 147 | [What does AWS Control Tower set up for a platform?](./what-does-aws-control-tower-set-up-for-a-platform.md)                                                              | 🟢 Beginner     |
| 148 | [What is the difference between an IAM user and an IAM role?](./what-is-the-difference-between-an-iam-user-and-an-iam-role.md)                                            | 🟢 Beginner     |
| 149 | [What is a VPC and how should a platform design one on AWS?](./what-is-a-vpc-and-how-should-a-platform-design-one-on-aws.md)                                              | 🟢 Beginner     |
| 150 | [What does Amazon EKS manage for you, and what is left to the platform?](./what-does-amazon-eks-manage-for-you-and-what-is-left-to-the-platform.md)                       | 🟢 Beginner     |
| 151 | [How do you give pods on EKS access to AWS resources safely?](./how-do-you-give-pods-on-eks-access-to-aws-resources-safely.md)                                            | 🟡 Intermediate |
| 152 | [How do you choose between ECS, EKS, Lambda, and App Runner for a platform runtime?](./how-do-you-choose-between-ecs-eks-lambda-and-app-runner-for-a-platform-runtime.md) | 🟡 Intermediate |
| 153 | [How do you allocate AWS cost back to teams?](./how-do-you-allocate-aws-cost-back-to-teams.md)                                                                            | 🟡 Intermediate |
| 154 | [What is EKS Auto Mode and when would a platform use it?](./what-is-eks-auto-mode-and-when-would-a-platform-use-it.md)                                                    | 🟡 Intermediate |
| 155 | [How do you structure a multi-account AWS platform?](./how-do-you-structure-a-multi-account-aws-platform.md)                                                              | 🔴 Advanced     |
| 156 | [What is account vending and how do you automate it?](./what-is-account-vending-and-how-do-you-automate-it.md)                                                            | 🔴 Advanced     |
| 157 | [How do you manage EKS node capacity with Karpenter?](./how-do-you-manage-eks-node-capacity-with-karpenter.md)                                                            | 🔴 Advanced     |
| 158 | [How do you build a paved road for AWS infrastructure self-service?](./how-do-you-build-a-paved-road-for-aws-infrastructure-self-service.md)                              | 🔴 Advanced     |

## What interviewers probe here

- Why the account is the primary isolation boundary on AWS.
- How a pod gets AWS permissions without an access key.
- The runtime decision between ECS, EKS, Lambda, and App Runner.

---

[⬅ Back to all topics](../README.md)
