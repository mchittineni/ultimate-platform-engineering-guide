---
title: "What is the difference between deploying and releasing?"
id: 96
category: "Progressive Delivery and Feature Flags"
difficulty: "Beginner"
tags:
  - platform-engineering
  - progressive-delivery-and-feature-flags
  - interview-questions
---

# What is the difference between deploying and releasing?

**Short answer:** Deploying is a technical event - a new version of the code is installed and running in production. Releasing is a business event - users start experiencing the new behaviour. Traditionally they happened at the same moment; modern delivery separates them, usually with feature flags, so code can be deployed many times a day with new features switched off, then released later, gradually, and to chosen users, by changing configuration rather than shipping code.

## Detail

**When they are coupled.** If the only way to expose a feature is to deploy the code that contains it, every deploy carries release risk. Teams respond by deploying less often and bundling more changes together, which makes each deploy larger and riskier, and makes it harder to tell which change caused a problem. Release dates also start to dictate engineering schedules: the code must merge and deploy exactly when marketing wants the launch.

**How they are separated.** There are two main mechanisms:

- **Feature flags** keep new code dormant after it is deployed. The code path exists in production but runs for nobody until the flag is turned on. Release then becomes a configuration change that can be targeted (staff first, then beta customers) and ramped (1%, 10%, 100%).
- **Traffic routing** - canary and blue-green - keeps a new version deployed but receiving no or little traffic until it is promoted. This separates deploying the binary from exposing it, though at the level of the whole version rather than an individual feature.

**What the separation buys you.**

- **Smaller, more frequent deploys.** Unfinished work can merge to the main branch behind a flag that is off, which enables trunk-based development and keeps each deploy small.
- **Two independent risks, handled independently.** "Does the new binary run?" is checked at deploy time, on all traffic, with the feature off. "Do users like, and does the system cope with, the new behaviour?" is checked at release time, with a ramp. When something goes wrong you know which one to roll back.
- **Release decisions move to the people who own them.** A product manager can launch at 09:00 on a Tuesday without an engineer running a pipeline, and support can check a customer's experience by looking at which variant they were served.
- **Faster recovery.** Turning a flag off takes seconds and needs no build; rolling back a deploy takes as long as your pipeline.

**The trade-offs.**

- Dormant code in production is still code in production. It must not break anything while off, and it must be tested in both states.
- Every flag is a branch that has to be removed later, or it becomes debt - see [How do you manage feature flag debt?](./how-do-you-manage-feature-flag-debt.md).
- A flag flip is a production change without a deploy. If your change tracking, dashboards, and DORA metrics only count deploys, they miss your riskiest class of change. Flag changes need audit logs and annotations just like deploys.
- Some changes cannot be hidden behind a flag: a database migration, a runtime upgrade, or a dependency bump takes effect when deployed. Those are the cases for canary and blue-green.

**Who uses it, and the platform's part.** Product engineers get to merge and deploy continuously without coordinating launch dates; product managers and on-call engineers get a release control they can use directly. The platform makes the separation practical by providing a flag SDK wrapper, a rollout controller for deploy-time safety, and a change feed that records both deploys and flag changes in the same timeline, so an alert can be correlated with whichever caused it.

## Example

```text
The same feature, deploy and release on different days.

  Mon 11:20  DEPLOY  checkout 1.8.0 (contains new saved-cards UI, flag OFF)
             canary 10% -> 50% -> 100%, analysis clean
             user-visible change: none

  Mon-Wed    six more deploys of unrelated fixes, all with saved-cards OFF

  Thu 09:00  RELEASE saved-cards -> internal staff
  Fri 09:00  RELEASE saved-cards -> 5% of users
  Mon 09:00  RELEASE saved-cards -> 25%, then 100% on Wednesday

  Wed 14:12  alert: card-token errors at 100%
  Wed 14:13  saved-cards -> 0%   (no deploy, no pipeline run)
             checkout 1.8.x keeps running; the deploy was never the problem
```

```yaml
# The change feed entry the platform records for a flag change, next to deploys.
# Without this, the Wed 14:13 recovery - and the release that caused the alert -
# are invisible to anyone reading the deploy history.
kind: ChangeEvent
type: flag-change
service: checkout
flag: saved-cards
from: "25%"
to: "100%"
actor: priya@example.com
timestamp: "2026-09-16T09:00:04Z"
approval: change-4418
```

## Interview tips

- Open with the definitions: deploy is technical (code running), release is a business event (users see it).
- Explain the cost of coupling them - bigger, rarer, riskier deploys - because that is why separation matters.
- Name both mechanisms: flags separate at the feature level, canary and blue-green at the version level.
- Point out that a flag flip is a production change and needs the same audit and observability as a deploy; that is the detail interviewers use to separate practitioners from readers.
- Name the users: engineers deploy without launch coordination, product owners control release, and the platform provides the flags, rollout tooling, and a unified change feed.

---

[⬅ Back to Progressive Delivery and Feature Flags](./README.md) · [All topics](../README.md)
