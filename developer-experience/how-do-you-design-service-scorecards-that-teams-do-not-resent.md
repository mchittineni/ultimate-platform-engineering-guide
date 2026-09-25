---
title: "How do you design service scorecards that teams do not resent?"
id: 25
category: "Developer Experience"
difficulty: "Advanced"
tags:
  - platform-engineering
  - developer-experience
  - interview-questions
---

# How do you design service scorecards that teams do not resent?

**Short answer:** Score only things the team can fix, make every check explain why it exists and how to satisfy it, provide the fix rather than just the finding, and never use the scores to compare teams in public or in performance conversations. A scorecard is a tool for making invisible risk visible to its owner; the moment it becomes a leaderboard, teams optimise the score instead of the property it was measuring.

## Detail

**What a scorecard is for.** Tier-1 services should have an SLO, a runbook, a current base image, a tested backup, and a named owner. Nobody disputes that. What breaks down is that nobody knows which services fall short, because the information lives across six systems. A scorecard aggregates it against the catalogue and shows each owner their own gaps.

**The design rules that determine whether it is accepted:**

- **Only check what the team controls.** Scoring a team on a shared cluster's patch level, or on a platform-managed component, produces failures they cannot act on. Two of those and the whole scorecard is dismissed as noise.
- **Every check carries a reason and a remedy.** Not "missing PodDisruptionBudget" but "no PodDisruptionBudget, so a node drain during a cluster upgrade can take all replicas at once - here is the four-line patch." A check that only reports is a chore; a check that fixes is a service.
- **Weight by consequence, and vary by tier.** A tier-1 payments service without a tested restore is a serious finding. A tier-3 internal dashboard without one is fine. A flat checklist applied uniformly is the fastest route to resentment.
- **Ship the fix.** For anything mechanical, the platform should raise the pull request. Adoption of a scorecard is roughly proportional to how much of the work it does for you.
- **Grandfather deliberately.** Introducing a check that instantly fails 200 services teaches everyone the score is meaningless. Apply new checks to new services first, then existing ones with a deadline and migration help.
- **No public league table.** Aggregate trends are legitimate - "60% of tier-1 services have a tested restore, up from 35%". Ranking teams against each other converts an engineering tool into a political one.
- **Let teams dispute a check.** If a check is wrong for a legitimate case, there must be a reviewed exemption with an owner and an expiry. Checks that cannot be challenged get gamed instead.

**The failure mode to name.** Goodhart's law applies directly: once the score is a target, teams satisfy the letter of each check. A `runbook.md` containing "TODO" satisfies "has a runbook". This is not dishonesty, it is a predictable response to a measure used as a goal. The defence is checking properties rather than artefacts where you can - a restore that was actually executed and verified, not a backup configuration that exists.

**How to know it is working.** Not by average score - that rises through gaming and through grandfathering. Watch whether the underlying incidents decline: fewer pages to the wrong team, fewer incidents where the runbook was absent, fewer surprises during cluster upgrades.

## Example

```yaml
# One check definition. Every field beyond `rule` exists to make the check
# actionable rather than merely accusatory.
- id: tier1-tested-restore
  title: Backup restore verified in the last 90 days
  applies_to: { tier: [1, 2], has_dependency: [postgres, mysql] }
  # Property, not artefact: a restore that ran, not a backup that is configured.
  rule: restore_test.last_success_at > now() - 90d
  severity: critical
  why: >
    A backup that has never been restored is an untested assumption. Three of our
    last five data incidents involved a backup that existed and could not be used.
  remedy: >
    Run `platform db restore-test <service> --to scratch`. It restores to a scratch
    instance, verifies row counts against the source, and records the result. ~8 min,
    no production impact.
  auto_fix: false # cannot be automated safely; it needs a human to read the result
  grace_period: 30d # new services get 30 days before this counts
```

```text
What a team sees - their own services only, remedy attached, PRs already open:

  team-payments                                          3 services

  checkout            tier 1     ●●●●●●●○○○   7/10
    ✗ critical   restore not verified in 90d   -> platform db restore-test checkout
    ✗ warning    base image 41 days stale      -> PR #482 open (auto-raised)
    ✗ info       no runbook link in catalogue  -> add `runbook` annotation

  pricing             tier 2     ●●●●●●●●●○   9/10
    ✗ info       SLO has no burn-rate alert    -> PR #483 open (auto-raised)

  refunds-worker      tier 3     ●●●●●●●●●●  10/10

  Two of the four findings already have a pull request waiting for review.
  That ratio - work done for the team versus work assigned to it - is what
  determines whether this gets used or ignored.
```

## Interview tips

- The one-line thesis: score only what the team controls, explain every check, and ship the fix. Scorecards that only report get ignored.
- Name Goodhart's law and give the concrete example - a `runbook.md` containing "TODO". It shows you have watched this happen.
- Checking properties rather than artefacts (a restore that ran, not a backup that is configured) is the sharpest single idea in this answer.
- Refusing to publish a league table, while accepting aggregate trends, is the answer to the follow-up about leadership wanting team comparisons. Have that distinction ready.
- Measuring success by declining incidents rather than rising average score is the senior close.

---

[⬅ Back to Developer Experience](./README.md) · [All topics](../README.md)
