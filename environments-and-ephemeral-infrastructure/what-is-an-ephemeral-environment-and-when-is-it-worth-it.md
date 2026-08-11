---
title: "What is an ephemeral environment and when is it worth it?"
id: 60
category: "Environments and Ephemeral Infrastructure"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - environments-and-ephemeral-infrastructure
  - interview-questions
---

# What is an ephemeral environment and when is it worth it?

**Short answer:** An ephemeral environment is a complete, isolated instance of a system created on demand - usually per pull request - and destroyed when it is no longer needed. It is worth it when contention for shared environments is genuinely slowing delivery, or when a change needs to be seen and exercised before merge. It is not worth it when your services cannot be created quickly, when realistic data is the blocker, or when the actual problem is that your shared staging environment is permanently broken.

## Detail

**The problem it solves is contention and confidence.** A single shared staging environment is a queue: two teams cannot test conflicting changes, a broken deploy blocks everyone, and nobody can tell whose change caused a failure. Ephemeral environments remove the queue by giving each change its own instance, and they let a reviewer or a product owner actually use the change rather than reading a diff.

**What "complete" needs to mean, and this is where most implementations fall short.** An environment that runs only the changed service against shared dependencies is useful but limited. A genuinely useful preview needs the service, its datastore with plausible data, its dependencies either deployed or reliably stubbed, working ingress with a URL, and its own credentials. Anything missing becomes the thing you cannot test, and if the missing piece is the one under change, the environment is theatre.

**The dependency problem determines feasibility.** For a handful of services you can deploy the whole system per pull request. At fifty services that is neither fast nor affordable, and the practical answer is a hybrid: deploy the changed services, and route everything else to a shared baseline instance with request-level routing so a preview's traffic reaches its own versions where they exist and the baseline otherwise. That is more work but it is what makes previews viable at scale.

**When it is genuinely worth it:**

- Shared environment contention is measurably slowing merges.
- Changes benefit from being seen - user-facing work, especially with non-engineering reviewers.
- Integration issues are a recurring source of escaped defects.
- Creating your infrastructure is fast and scripted already.

**When it is not:**

- Provisioning takes longer than the review. A twenty-minute environment for a five-minute review is friction, not help.
- The blocker is realistic data, not environment availability. Solve data first.
- Your services cannot be created from scratch - manual setup steps mean previews will be permanently broken.
- The real problem is that staging is unreliable. Fix that; it is cheaper and it helps everyone.

**Time to ready is the metric that decides adoption.** Under about five minutes and people use previews naturally. Beyond fifteen, they merge without waiting and the investment is wasted. Optimising this - pre-warmed capacity, cached images, database templates rather than migrations from empty - is usually the difference between a used and an unused capability.

**They must be genuinely destroyed.** A time-to-live plus reaping on pull-request close is not optional. Without it, ephemeral environments become long-lived environments nobody owns, which is worse than the shared staging you were trying to escape - more surface, no ownership, and real spend.

## Example

```text
Where ephemeral environments help, and where they are the wrong investment.

CASE A - 8 services, monorepo, 25 engineers
  symptom: staging booked out; two teams' changes collide weekly
  provisioning: services created from manifests, DB from a template snapshot
  time to ready: ~3 minutes
  -> WORTH IT. Full-stack preview per PR. Reviewers get a URL in the PR body.

CASE B - 60 services, 12 teams
  symptom: same contention
  provisioning: deploying all 60 per PR is ~25 min and expensive
  -> WORTH IT, BUT HYBRID. Deploy only the changed services; route everything
     else to a shared baseline with header-based routing. Time to ready ~4 min.

CASE C - 15 services, but 3 require manual configuration after deploy
  symptom: contention
  -> NOT YET. Previews would be broken 3 ways out of 15 and teams would stop
     trusting them. Fix reproducibility first; that work is valuable regardless.

CASE D - contention, and staging's database is a 6-month-old anonymised dump
  that no longer matches the schema
  -> NOT YET. Data is the blocker. An empty preview database tests less than the
     stale shared one. Solve seeding first.

CASE E - staging breaks twice a week and nobody owns it
  -> FIX STAGING. It is cheaper, it unblocks everyone immediately, and previews
     built on the same unreliable foundations will inherit the problem.
```

```yaml
# The declaration. TTL and the owning pull request are part of the object, so
# reaping is a property of the design rather than a cleanup job someone adds later.
apiVersion: platform.example.com/v1
kind: Environment
metadata: { name: pr-4821, namespace: previews }
spec:
  type: ephemeral
  ttl: 72h # hard stop regardless of activity
  reapOn: [pull-request-closed, pull-request-merged, ttl-expired]
  owner: group:team-payments
  pullRequest: { repo: example/checkout, number: 4821 }
  services:
    - name: checkout # under change - built from this PR
      image: ghcr.io/example/checkout@sha256:9f2c8b1d...
    - name: pricing # also changed in this PR
      image: ghcr.io/example/pricing@sha256:3c7ab2e0...
  baseline: shared-preview-baseline # everything else routes here
  data:
    source: template # a prepared snapshot, not migrations from empty
    template: checkout-seed-v14
  ingress:
    host: pr-4821.preview.example.internal
    auth: sso-required # never publicly reachable
```

## Interview tips

- Define it precisely - complete, isolated, on demand, destroyed - and stress that "complete" is where implementations usually fall short.
- Time to ready is the metric that decides whether the capability is used. Under five minutes it gets used; beyond fifteen people merge without waiting.
- The hybrid pattern - deploy changed services, route the rest to a shared baseline - is the answer to "how does this work with sixty services", and it is what separates a real answer from a demo.
- Say clearly when it is the wrong investment, especially the case where the real problem is an unreliable shared staging environment. Interviewers value the candidate who fixes the cheaper thing first.
- Mandatory TTL and reaping is the operational discipline. Ephemeral environments that are not destroyed are worse than the shared environment they replaced.

---

[⬅ Back to Environments and Ephemeral Infrastructure](./README.md) · [All topics](../README.md)
