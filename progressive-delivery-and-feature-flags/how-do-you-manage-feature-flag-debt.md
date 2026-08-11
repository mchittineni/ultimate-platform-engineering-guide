---
title: "How do you manage feature flag debt?"
id: 53
category: "Progressive Delivery and Feature Flags"
difficulty: "Advanced"
tags:
  - platform-engineering
  - progressive-delivery-and-feature-flags
  - interview-questions
---

# How do you manage feature flag debt?

**Short answer:** Classify every flag at creation so its expected lifespan is known, then automate the removal rather than asking teams to remember - a scanner that finds flags past their deadline, and a bot that opens the pull request deleting the conditional and keeping the shipped branch. Flag debt is not a discipline problem, it is a missing mechanism: the work of cleanup arrives long after the work of shipping, so it never wins a prioritisation conversation.

## Detail

**What the debt actually costs.** Every stale flag is a code path that still exists and is no longer tested in the configuration it will run in. It doubles the reasoning burden on the next person to touch that code, and it leaves a switch someone can flip. The classic cautionary tale is Knight Capital in 2012, where a deployment that missed one server combined with a repurposed dormant flag re-activated years-old code and lost hundreds of millions of dollars in under an hour. Reusing a flag key that was never cleaned up is a genuinely dangerous act.

**Classification determines whether cleanup is even expected.** These are the four types and the only two that carry deadlines:

| Type                      | Lifespan              | Cleanup trigger             | On the debt list?                |
| ------------------------- | --------------------- | --------------------------- | -------------------------------- |
| Release                   | Weeks to a few months | 100% for a sustained period | Yes                              |
| Experiment                | Weeks                 | A winner is chosen          | Yes                              |
| Operational (kill switch) | Permanent by design   | The feature is retired      | No - annual review               |
| Permission (entitlement)  | Indefinite            | The plan or role is retired | No - and it should not be a flag |

Campaigns that chase every flag fail because they generate false positives on permanent flags, and teams learn to ignore the report. The type is what makes the signal trustworthy.

**Scan in both directions.** Code referencing a flag with no provider configuration silently evaluates the default forever - so the branch is dead but present. Provider configuration with no code reference is an orphaned switch someone can flip with no effect, or worse, an effect nobody expects. Tooling that only looks outward from code misses the second class entirely.

**Date the flag from the code, not from a spreadsheet.** `git log --diff-filter=A -S <flag-key>` finds when a flag identifier first appeared, which is a reliable age even when the registry is incomplete. Combining age with usage - old and rarely referenced - is a much better debt signal than age alone.

**Automate the removal pull request.** The mechanical part - delete the conditional, keep the winning branch, remove the registry entry, mark it archived with a date and a link - is scriptable for the common shapes. A bot that opens that pull request converts cleanup from a task someone must schedule into a review someone must approve, which is a completely different success rate.

**The code-level pattern that makes removal safe.** A single evaluation at a module boundary is easy to remove; a flag checked in fifteen places through a function body is not, because removing it means understanding all fifteen. Insisting on one decision point at creation review is the cheapest possible investment in future cleanup.

**Make the debt visible per team, with the fix attached.** A dashboard showing each team its own stale flags, with the removal pull request already open, is what gets acted on. An organisation-wide count is a statistic; a link to a waiting pull request is a request.

**Publish the deadlines as policy, not as industry fact.** A ninety-day release-flag SLA and a thirty-day window from full rollout to removal are defensible policies you set, and framing them that way is more honest and more persuasive than presenting them as standards.

## Example

```text
Debt report - age from git, usage from static analysis, filtered by type so the
signal is trustworthy.

  $ platform flags debt --max-age-days 90

  DEBT (release/experiment flags past policy)
    checkout-new-pricing-engine     age 147d   at 100% for 51d   refs 1
        -> cleanup PR #1841 OPEN (auto-raised, awaiting review)
    search-rerank-v2                age 203d   at 100% for 132d  refs 3
        -> NOT auto-removable: 3 evaluation sites inside one function.
           Manual removal required. This is the cost of the scattered pattern.
    cart-experiment-b               age  94d   experiment ENDED 40d ago  refs 1
        -> cleanup PR #1842 OPEN

  DEAD BRANCHES (code references a flag with no provider config)
    legacy-tax-calc                 age 411d   no provider config
        -> has been evaluating the default for over a year. The branch is dead
           code; delete it.

  ORPHANED CONFIG (provider config with no code reference)
    old-cart-flow                   config exists, 0 code references
        -> a switch someone can still flip. Delete the config.
           This is the Knight Capital shape: a dormant flag with no code today,
           available for someone to reuse the key tomorrow.

  EXEMPT (correctly excluded - not debt)
    payments-kill-switch            type: operational   permanent by design
    tier-premium-features           type: permission    -> but flagged separately:
                                     should move to the entitlements service
```

```python
# Why the code-level pattern decides whether cleanup can be automated.

# HARD to remove - 3 sites, interleaved with logic. A bot cannot safely do this,
# and a human has to understand all three before touching any.
def checkout(cart, user):
    if flags.enabled("new-pricing", ctx=user.flag_ctx):
        subtotal = new_pricing.subtotal(cart)
    else:
        subtotal = legacy.subtotal(cart)
    tax = new_pricing.tax(subtotal) if flags.enabled("new-pricing", ctx=user.flag_ctx) \
          else legacy.tax(subtotal)
    audit.record(cart, pricing="new" if flags.enabled("new-pricing", ctx=user.flag_ctx)
                 else "legacy")
    return subtotal + tax

# EASY to remove - one decision at a module boundary. Cleanup is deleting the
# branch and inlining the winner; a bot can raise that PR correctly.
def checkout(cart, user):
    engine = new_pricing if flags.enabled("new-pricing", ctx=user.flag_ctx) else legacy
    return engine.total(cart)
```

## Interview tips

- Lead with the reframe: flag debt is a missing mechanism, not a discipline failure, because the cleanup work arrives long after the shipping work.
- Classification is what makes the debt report trustworthy. Explain that chasing permanent operational flags alongside release flags is why cleanup campaigns get ignored.
- Bidirectional scanning - dead branches and orphaned configuration - is the detail most candidates miss and it is genuinely important.
- Knight Capital is the right story to close on, and the specific lesson is about reusing a stale flag key rather than about flags in general.
- The single-decision-point-at-a-module-boundary requirement is the highest-leverage code review rule, because it is what makes automated removal possible.
- Present your SLAs as policy you chose, not as industry standards. It is more accurate and it invites the interviewer to discuss trade-offs rather than dispute a number.

---

[⬅ Back to Progressive Delivery and Feature Flags](./README.md) · [All topics](../README.md)
