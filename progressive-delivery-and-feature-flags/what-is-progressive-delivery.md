---
title: "What is progressive delivery?"
id: 92
category: "Progressive Delivery and Feature Flags"
difficulty: "Beginner"
tags:
  - platform-engineering
  - progressive-delivery-and-feature-flags
  - interview-questions
---

# What is progressive delivery?

**Short answer:** Progressive delivery is releasing a change to a small, controlled slice of real traffic or users first, measuring its effect, and widening exposure step by step - with an automatic way to stop and reverse if the numbers go wrong. It builds on continuous delivery: CD makes every change deployable, progressive delivery controls how quickly each change reaches everyone. The goal is to shrink the blast radius of a bad change from "all users" to "a few percent, for a few minutes".

## Detail

**The problem it solves.** Testing before production catches many defects, but not the ones that only appear under real traffic, real data, and real user behaviour. A traditional "big bang" release discovers those defects with 100% of users at once. Progressive delivery accepts that some failures will reach production and designs the release so that when they do, they reach as few people as possible and are reversed quickly.

**The three ingredients.** Every progressive delivery technique combines the same three things:

- **Controlled exposure** - a mechanism for sending a fraction of traffic or a chosen group of users to the new version or behaviour. That mechanism is either routing (a load balancer or service mesh splits requests between two deployed versions) or a feature flag (one deployed version decides per user which code path to run).
- **Measurement** - metrics compared between the new and old paths while both are running: error rate, latency, saturation, and business signals such as conversion.
- **An automated decision** - rules, written before the rollout starts, that either promote to the next step or abort and roll back. Without this third part you have a slow rollout, not progressive delivery.

**The common techniques.** These are the names you will hear, and each gets its own question in this topic:

| Technique          | What is split                     | Typical tooling                             |
| ------------------ | --------------------------------- | ------------------------------------------- |
| Canary deployment  | Requests between two versions     | Argo Rollouts, Flagger, service mesh        |
| Blue-green         | All traffic, switched in one step | Two environments plus a router              |
| Feature flag ramp  | Users, within one version         | OpenFeature with a flag provider            |
| Ring deployment    | Groups of users or regions        | Internal staff, then beta, then everyone    |
| Shadow / dark load | Copied traffic, responses ignored | Mesh traffic mirroring, application shadows |

**It separates deploying from releasing.** Putting new code on servers (deploy) and letting users experience it (release) become two different events you control independently. That separation is the core idea, and it is covered in [What is the difference between deploying and releasing?](./what-is-the-difference-between-deploying-and-releasing.md).

**The trade-offs.** Progressive delivery is not free. Running two versions at once means they must be compatible with the same database schema and the same message formats. Small canary slices need enough traffic to produce a statistically meaningful signal; a service with ten requests a minute cannot be judged on 1% of them. Feature flags add code branches that must be tested and later removed. And none of these techniques reverses state: a bad version that has already sent emails or written malformed rows leaves that damage behind, which is why [What can a feature flag not roll back?](./what-can-a-feature-flag-not-roll-back.md) matters.

**Who uses it, and what the platform provides.** The users are product and service teams shipping changes. Without a platform, each team hand-builds traffic splitting, picks its own metrics, and watches dashboards manually - so most teams simply do not do it. A platform team makes progressive delivery the default: a rollout controller installed in every cluster, a flag SDK wrapper, standard metric queries wired to the team's service-level objectives, and a template that gives a new service a canary strategy on day one. The team's remaining decision is the ramp speed and any feature-specific checks, not how to build the machinery.

## Example

```yaml
# A canary with Argo Rollouts: 10% -> 50% -> 100%, with an automated analysis
# that aborts and returns all traffic to the stable version if success rate drops.
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: checkout
  namespace: team-payments
spec:
  replicas: 10
  selector:
    matchLabels: { app: checkout }
  template:
    metadata:
      labels: { app: checkout }
    spec:
      containers:
        - name: checkout
          image: registry.example.com/checkout:1.4.3
  strategy:
    canary:
      analysis:
        templates:
          - templateName: success-rate # runs in the background for every step
        args:
          - name: service
            value: checkout
      steps:
        - setWeight: 10
        - pause: { duration: 15m }
        - setWeight: 50
        - pause: { duration: 30m }
        # after the last step the Rollout promotes to 100% automatically
```

```text
What the team sees when the change is bad:

  10:02  rollout started      checkout 1.4.3   weight 10%
  10:09  analysis success-rate  measured 0.962  (requires >= 0.99)  FAILED
  10:09  rollout aborted      weight 0%, stable 1.4.2 serving 100%

  Exposure: 10% of requests for 7 minutes, instead of 100% until someone noticed.
```

## Interview tips

- Define it with the three ingredients - controlled exposure, measurement, automated decision. Candidates who only say "rolling out gradually" miss the part that makes it safe.
- Say it builds on continuous delivery rather than replacing it, and that the core idea is separating deploy from release.
- Name at least two mechanisms (routing-based canary and flag-based ramp) and the difference between them: requests between versions versus users within one version.
- Offer a limitation unprompted: low-traffic services struggle to get a signal, and no technique undoes state changes.
- Name the user: product teams get safe releases without building the machinery, because the platform ships the rollout controller and metric templates as defaults.

---

[⬅ Back to Progressive Delivery and Feature Flags](./README.md) · [All topics](../README.md)
