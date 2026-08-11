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

**8 questions** · 🟢 Beginner: 0 · 🟡 Intermediate: 2 · 🔴 Advanced: 6

## Questions

| #   | Question                                                                                                                               | Difficulty      |
| --- | -------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 52  | [How do you run feature flags as a platform capability?](./how-do-you-run-feature-flags-as-a-platform-capability.md)                   | 🔴 Advanced     |
| 53  | [How do you manage feature flag debt?](./how-do-you-manage-feature-flag-debt.md)                                                       | 🔴 Advanced     |
| 54  | [How do you design a progressive rollout and its abort criteria?](./how-do-you-design-a-progressive-rollout-and-its-abort-criteria.md) | 🔴 Advanced     |
| 55  | [How do you design a kill switch you can trust?](./how-do-you-design-a-kill-switch-you-can-trust.md)                                   | 🔴 Advanced     |
| 56  | [When do you use a feature flag instead of a canary deployment?](./when-do-you-use-a-feature-flag-instead-of-a-canary-deployment.md)   | 🟡 Intermediate |
| 57  | [How do you keep percentage rollouts consistent across services?](./how-do-you-keep-percentage-rollouts-consistent-across-services.md) | 🔴 Advanced     |
| 58  | [What can a feature flag not roll back?](./what-can-a-feature-flag-not-roll-back.md)                                                   | 🔴 Advanced     |
| 59  | [How do you test code that sits behind feature flags?](./how-do-you-test-code-that-sits-behind-feature-flags.md)                       | 🟡 Intermediate |

## What interviewers probe here

- Deploy versus release, and which risk each one controls.
- The abort threshold and hold time for every rollout phase, set before it starts.
- What a flag flip cannot undo - state, not behaviour.

---

[⬅ Back to all topics](../README.md)
