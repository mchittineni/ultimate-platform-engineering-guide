---
title: "Platform Security"
category: "Platform Security"
tags:
  - platform-engineering
  - platform-security
  - index
---

# Platform Security

Security as a platform default: workload identity without long-lived keys, secretless pipelines, secrets management, supply-chain provenance, base image currency, and break-glass access.

**14 questions** · 🟢 Beginner: 5 · 🟡 Intermediate: 3 · 🔴 Advanced: 6

## Questions

| #   | Question                                                                                                                                                                 | Difficulty      |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------- |
| 119 | [What is least privilege and how does a platform enforce it by default?](./what-is-least-privilege-and-how-does-a-platform-enforce-it-by-default.md)                     | 🟢 Beginner     |
| 120 | [What is an SBOM and why do platforms generate one?](./what-is-an-sbom-and-why-do-platforms-generate-one.md)                                                             | 🟢 Beginner     |
| 121 | [What is container image signing?](./what-is-container-image-signing.md)                                                                                                 | 🟢 Beginner     |
| 122 | [What is the shared responsibility model for a platform?](./what-is-the-shared-responsibility-model-for-a-platform.md)                                                   | 🟢 Beginner     |
| 123 | [What is shift-left security and where does it go wrong?](./what-is-shift-left-security-and-where-does-it-go-wrong.md)                                                   | 🟢 Beginner     |
| 124 | [How do you manage secrets as a platform capability?](./how-do-you-manage-secrets-as-a-platform-capability.md)                                                           | 🟡 Intermediate |
| 125 | [How do you keep base images patched across every team?](./how-do-you-keep-base-images-patched-across-every-team.md)                                                     | 🟡 Intermediate |
| 126 | [What does the EU Cyber Resilience Act mean for a platform team?](./what-does-the-eu-cyber-resilience-act-mean-for-a-platform-team.md)                                   | 🟡 Intermediate |
| 127 | [How does a platform provide workload identity without long-lived credentials?](./how-does-a-platform-provide-workload-identity-without-long-lived-credentials.md)       | 🔴 Advanced     |
| 128 | [How do you run a secretless CI/CD pipeline?](./how-do-you-run-a-secretless-ci-cd-pipeline.md)                                                                           | 🔴 Advanced     |
| 129 | [How do you secure the software supply chain for everything the platform builds?](./how-do-you-secure-the-software-supply-chain-for-everything-the-platform-builds.md)   | 🔴 Advanced     |
| 130 | [How do you respond to a critical CVE that affects every service on the platform?](./how-do-you-respond-to-a-critical-cve-that-affects-every-service-on-the-platform.md) | 🔴 Advanced     |
| 131 | [How do you design break-glass access to production?](./how-do-you-design-break-glass-access-to-production.md)                                                           | 🔴 Advanced     |
| 132 | [How do you threat model a platform?](./how-do-you-threat-model-a-platform.md)                                                                                           | 🔴 Advanced     |

## What interviewers probe here

- How a workload proves who it is without a stored credential.
- The supply-chain chain of custody from commit to running container.
- How you patch every service at once when a critical CVE lands.

---

[⬅ Back to all topics](../README.md)
