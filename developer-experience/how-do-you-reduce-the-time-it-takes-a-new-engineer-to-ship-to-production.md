---
title: "How do you reduce the time it takes a new engineer to ship to production?"
id: 23
category: "Developer Experience"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - developer-experience
  - interview-questions
---

# How do you reduce the time it takes a new engineer to ship to production?

**Short answer:** Measure the whole path first, then attack whatever dominates it - which is almost never the part platform teams assume. In most organisations the biggest blocks are access provisioning that waits on humans, a local environment that takes days to assemble, and documentation that is wrong in ways only a newcomer discovers. Time to first production change is the single best summary metric a platform team can own, because it exercises nearly every capability at once.

## Detail

**Why this metric is so useful.** A new engineer shipping a change touches access management, repository setup, local tooling, the build, the test suite, code review, the pipeline, the deploy mechanism, and the observability needed to confirm it worked. If that takes nine days, you have a list of nine things to fix, and every one of them also costs your existing engineers - they have just stopped noticing.

**Instrument the path before optimising it.** Record the timestamps: account created, repository cloned, dependencies installed, tests passing locally, first pull request opened, first merge, first production deploy. The gaps between them are your backlog, and they are usually distributed nothing like the team expects.

**Where the time actually goes, in rough order of frequency:**

- **Access requests handled by humans.** Cloud roles, repository permissions, VPN, database read access, the observability tool, the secret store - each a separate request with its own approver and queue. This is often half the total and is the cheapest to fix.
- **Local environment assembly.** Language runtime, tool versions, a database, mock services, seed data, credentials. Reproducible from a single command or it will consume days.
- **Documentation that is wrong.** Not missing - wrong. Steps that assume a tool already installed, a command renamed two releases ago, an environment variable no longer read.
- **Waiting for review.** Frequently the largest single block once the mechanics work, and not solvable with tooling alone.
- **A first change with no safe target.** If there is nowhere to deploy without risk, the first change becomes an event rather than a routine.

**The interventions that work, ordered by return:**

1. **Role-based access on day one, granted automatically from the team assignment.** Joining `team-payments` should provision the standard set without a request. This is identity and platform work, and it is the highest-return change available.
2. **One command to a working environment**, whether that is a devcontainer, a Nix or Docker Compose setup, or a cloud development environment. The measure is a working test suite, not a running container.
3. **A deliberate first task**, small, real, and shipped to production - by convention a documentation or logging fix. The goal is completing the whole loop, not the change itself.
4. **Documentation validated by the next newcomer.** Every new joiner fixes the onboarding guide as their first pull request. Self-repairing, and the only mechanism that reliably works.
5. **A safe target for the first deploy** - a preview environment or a low-tier service - so the first production change is unremarkable.

**Measure the tenth commit too.** The first can be gamed with hand-holding. Time to tenth commit in production tells you whether the engineer is actually independent, which is the outcome you want.

## Example

```text
Instrumented onboarding for one cohort, before and after. The numbers show why
measuring first mattered: the team had planned to invest in documentation.

STAGE                                   before    after    what changed
  offer accepted -> laptop ready         2.0d      2.0d     unchanged (not ours)
  laptop -> repo cloned                  0.5d      0.1d     SSO on the git org
  repo -> tests passing locally          3.5d      0.3d     devcontainer, one command
  -> cloud + secrets + observability     4.0d      0.0d     ROLE-BASED ACCESS from team
                                                            membership; no requests
  -> first PR opened                     1.0d      0.5d     "good first issue" queue
  -> first PR merged                     1.5d      1.0d     review SLA, not tooling
  -> first production deploy             1.0d      0.2d     preview env + auto promote
                                        ------    ------
  TOTAL to first production change       13.5d     4.1d
  TOTAL to 10th commit in production     26d       9d       the honest independence
                                                            measure

The single biggest win - 4 days to 0 - was access provisioning, which is an
identity integration, not a developer-tooling project. That is why you measure
before you build: the planned documentation work would have saved half a day.
```

## Interview tips

- Start with "I would measure the whole path first" and name the timestamps. Jumping straight to solutions is the common weak answer.
- Access provisioning is the answer interviewers most want to hear, because it is where the time usually is and it is invisible to teams who already have access.
- The self-repairing documentation loop - each newcomer fixes the guide - is a memorable, cheap, and genuinely effective idea.
- Distinguish first commit from tenth commit and explain why. It shows you know the first can be stage-managed.
- Be honest that review latency is a social problem tooling cannot fully solve; claiming a platform fixes everything undermines the rest of the answer.

---

[⬅ Back to Developer Experience](./README.md) · [All topics](../README.md)
