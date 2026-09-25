---
title: "Progressive Delivery and Feature Flags"
category: "Progressive Delivery and Feature Flags"
tags:
  - platform-engineering
  - progressive-delivery-and-feature-flags
  - index
---

# Progressive Delivery and Feature Flags

Separating deploy from release: flags as a platform capability, flag debt and its SLAs, rollout curves with abort criteria, trustworthy kill switches, and consistent bucketing.

**14 questions** · 🟢 Beginner: 5 · 🟡 Intermediate: 3 · 🔴 Advanced: 6

## Questions

| #   | Question                                                                                                                                     | Difficulty      |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 92  | [What is progressive delivery?](./what-is-progressive-delivery.md)                                                                           | 🟢 Beginner     |
| 93  | [What is a feature flag?](./what-is-a-feature-flag.md)                                                                                       | 🟢 Beginner     |
| 94  | [What is a canary deployment?](./what-is-a-canary-deployment.md)                                                                             | 🟢 Beginner     |
| 95  | [What is a blue-green deployment?](./what-is-a-blue-green-deployment.md)                                                                     | 🟢 Beginner     |
| 96  | [What is the difference between deploying and releasing?](./what-is-the-difference-between-deploying-and-releasing.md)                       | 🟢 Beginner     |
| 97  | [When do you use a feature flag instead of a canary deployment?](./when-do-you-use-a-feature-flag-instead-of-a-canary-deployment.md)         | 🟡 Intermediate |
| 98  | [How do you test code that sits behind feature flags?](./how-do-you-test-code-that-sits-behind-feature-flags.md)                             | 🟡 Intermediate |
| 99  | [What is OpenFeature and why does a vendor-neutral flag API matter?](./what-is-openfeature-and-why-does-a-vendor-neutral-flag-api-matter.md) | 🟡 Intermediate |
| 100 | [How do you run feature flags as a platform capability?](./how-do-you-run-feature-flags-as-a-platform-capability.md)                         | 🔴 Advanced     |
| 101 | [How do you manage feature flag debt?](./how-do-you-manage-feature-flag-debt.md)                                                             | 🔴 Advanced     |
| 102 | [How do you design a progressive rollout and its abort criteria?](./how-do-you-design-a-progressive-rollout-and-its-abort-criteria.md)       | 🔴 Advanced     |
| 103 | [How do you design a kill switch you can trust?](./how-do-you-design-a-kill-switch-you-can-trust.md)                                         | 🔴 Advanced     |
| 104 | [How do you keep percentage rollouts consistent across services?](./how-do-you-keep-percentage-rollouts-consistent-across-services.md)       | 🔴 Advanced     |
| 105 | [What can a feature flag not roll back?](./what-can-a-feature-flag-not-roll-back.md)                                                         | 🔴 Advanced     |

## What interviewers probe here

- Deploy versus release, and which risk each one controls.
- The abort threshold and hold time for every rollout phase, set before it starts.
- What a flag flip cannot undo - state, not behaviour.

---

[⬅ Back to all topics](../README.md)
