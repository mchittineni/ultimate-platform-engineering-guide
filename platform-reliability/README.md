---
title: "Platform Reliability"
category: "Platform Reliability"
tags:
  - platform-engineering
  - platform-reliability
  - index
---

# Platform Reliability

Keeping the platform up: SLOs for a platform rather than an app, error budget policy, platform on-call, incidents where the platform is the incident, graceful degradation, and DR.

**13 questions** · 🟢 Beginner: 5 · 🟡 Intermediate: 3 · 🔴 Advanced: 5

## Questions

| #   | Question                                                                                                                                                 | Difficulty      |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 198 | [What are SLIs, SLOs, and SLAs?](./what-are-slis-slos-and-slas.md)                                                                                       | 🟢 Beginner     |
| 199 | [What is an error budget?](./what-is-an-error-budget.md)                                                                                                 | 🟢 Beginner     |
| 200 | [What is a blameless postmortem?](./what-is-a-blameless-postmortem.md)                                                                                   | 🟢 Beginner     |
| 201 | [What are RTO and RPO, and how do they differ from high availability?](./what-are-rto-and-rpo-and-how-do-they-differ-from-high-availability.md)          | 🟢 Beginner     |
| 202 | [What is toil and how does a platform team reduce it?](./what-is-toil-and-how-does-a-platform-team-reduce-it.md)                                         | 🟢 Beginner     |
| 203 | [How do you run on-call for a platform team?](./how-do-you-run-on-call-for-a-platform-team.md)                                                           | 🟡 Intermediate |
| 204 | [How do you use chaos engineering to test platform guarantees?](./how-do-you-use-chaos-engineering-to-test-platform-guarantees.md)                       | 🟡 Intermediate |
| 205 | [How do you run a production readiness review?](./how-do-you-run-a-production-readiness-review.md)                                                       | 🟡 Intermediate |
| 206 | [How do you define SLOs for a platform rather than an application?](./how-do-you-define-slos-for-a-platform-rather-than-an-application.md)               | 🔴 Advanced     |
| 207 | [What does an error budget policy look like for a platform team?](./what-does-an-error-budget-policy-look-like-for-a-platform-team.md)                   | 🔴 Advanced     |
| 208 | [How do you run an incident when the platform itself is the incident?](./how-do-you-run-an-incident-when-the-platform-itself-is-the-incident.md)         | 🔴 Advanced     |
| 209 | [How do you make a platform degrade gracefully instead of failing closed?](./how-do-you-make-a-platform-degrade-gracefully-instead-of-failing-closed.md) | 🔴 Advanced     |
| 210 | [How do you plan disaster recovery for the platform itself?](./how-do-you-plan-disaster-recovery-for-the-platform-itself.md)                             | 🔴 Advanced     |

## What interviewers probe here

- What you can promise when your users are other engineers.
- How the platform keeps serving traffic while its control plane is down.
- Recovering the platform when the tooling you would use is also gone.

---

[⬅ Back to all topics](../README.md)
