---
title: "How do you build a platform roadmap and say no?"
id: 248
category: "Platform Team and Operating Model"
difficulty: "Advanced"
tags:
  - platform-engineering
  - platform-team-and-operating-model
  - interview-questions
---

# How do you build a platform roadmap and say no?

**Short answer:** Build it from evidence you already collect - support question categories, escape hatch usage, exception registers, break-glass activations, and onboarding measurements - rather than from requests, then reserve explicit capacity for operational load and reliability so the plan survives contact with reality. Saying no works when it is a published prioritisation rule and a visible constraint rather than a judgement, which is exactly what an error budget policy and a capacity split give you.

## Detail

**Requests are the weakest input.** They come from whoever asks loudest, are shaped by what people imagine you can do, and systematically miss the problems nobody has thought to complain about. Every measurement the platform already produces is a stronger signal.

**The evidence sources, all of which you have if you have built the rest well:**

| Source                           | Tells you                                    |
| -------------------------------- | -------------------------------------------- |
| Support questions by category    | State you have not exposed, or docs you lack |
| Escape hatch usage               | Where the golden path does not fit           |
| Policy exception patterns        | Where a rule or a default is wrong           |
| Break-glass activations          | Missing supported operations                 |
| Recurring pages                  | Missing automation                           |
| Onboarding measurements          | Where the journey is slow                    |
| Adoption plateaus per capability | Which capability is not worth using          |
| Retention departures             | What was tried and abandoned                 |
| Cost reports                     | Which defaults are wrong                     |

Eleven activations to restart a stuck workload, or eleven services overriding the same probe, is a roadmap item with proven demand and no persuasion required.

**Reserve capacity explicitly.** A plan that assumes all capacity is available for new work fails in week three. A defensible split is roughly half for new capabilities, a quarter for operational load and support, and a quarter for reliability, migration, and paying down the platform's own debt - stated up front, so the operational quarter is not silently taken from the build quarter every time.

**Prioritise by how many future teams a capability unblocks.** Not by who asked. A capability that unblocks four teams beats one that unblocks one, and a capability that removes a recurring class of support load beats one that adds a feature - because the support load compounds while the feature does not.

**Sequence to keep the platform coherent.** Some work is prerequisite: attribution before cost accountability, catalogue before scorecards, provisioning before a portal. Shipping the visible thing first is tempting and produces a portal over a ticket queue.

**Publish the roadmap, including what you declined and why.** A team that can see its request was considered, ranked, and declined for a stated reason engages differently from one that heard nothing. The refusals are as important as the plan.

**Saying no needs a mechanism, not courage.** Three that work: the error budget policy, signed by the leadership that requests capabilities, which converts "we are too fragile to build that" into a pre-agreed rule; the published capacity split, which makes the trade-off visible - this item displaces that one, which do you want; and the evidence ranking, which turns a refusal into a comparison rather than an opinion.

**Offer the alternative.** "No, and here is the documented escape hatch, and here is where it sits on the roadmap" is a very different conversation from "no". Often the request can be satisfied by an existing capability, a small extension, or an exception with a review date.

**Say no to your own ideas too.** The temptation is a portal, a service mesh, or a rewrite that no evidence supports. Applying the same evidence test to internally generated work as to requests is the discipline that keeps a roadmap honest, and it is the failure mode interviewers are most likely to be probing for.

**Review against outcomes, not delivery.** At the end of a period, ask which shipped items moved adoption, lead time, support load, or cost - and which did not. That is how the next roadmap gets better, and it is more useful than a completion percentage.

## Example

```text
A quarter's roadmap, every item with its evidence and the source it came from.

  CAPACITY SPLIT, stated up front so it is not silently reallocated
    new capabilities ................. 50%
    operational load and support ..... 25%
    reliability, migration, own debt . 25%

  NEW CAPABILITIES (50%)
    1. GPU scheduling support
       evidence: 6 teams on escape hatches for this; 4 declined migration because
                 of it. Unblocks 6 teams and removes 4 exceptions.
       source: escape hatch register + migration decline tracking
    2. `interruptible` placement (spot)
       evidence: 3 teams implemented it independently, 2 got PDBs wrong and had
                 outages. Cost saving material across batch and preview.
       source: incident review + cost report
    3. Expose in-flight deploy status to teams
       evidence: 41 support questions/month in that single category
       source: support categorisation. Highest support-load reduction available.

  OPERATIONAL LOAD AND SUPPORT (25%)
    4. Automate the top 3 recurring pages
       evidence: 25 of last quarter's 32 pages were 3 fixable causes
       source: on-call report. Takes out-of-hours pages 4.1/wk -> ~1.
    5. Six most-requested how-to pages
       evidence: support categorisation

  RELIABILITY, MIGRATION, DEBT (25%)
    6. Shard reconciliation on prod-eu-1
       evidence: deploy SLO breached twice; 11 recurring pages
    7. Complete the pipeline-v1 deprecation
       evidence: 2 consumers remain; maintaining both costs us every release

  DECLINED, PUBLISHED WITH REASONS - as important as the plan
    ✗ Developer portal (requested by leadership)
      reason: we already expose catalogue, status, and cost via CLI and PR
      comments. The support-question categories a portal would address are the
      3 we are fixing directly in item 3, at a fraction of the cost. Revisit when
      discovery is a measured problem - it is not: 0 support questions about
      finding services.
    ✗ Service mesh (requested by two engineers, including me)
      reason: no requirement named. Network policy plus CNI encryption covers the
      isolation need. This is OUR idea and it fails the same evidence test we
      apply to requests. Recorded so it is not relitigated.
    ✗ Second cloud provider (requested by leadership, for resilience)
      reason: we are not multi-region within our current provider yet. That
      addresses most of the risk at a fraction of the cost, and is item 6's
      neighbour next quarter.
    ✗ Custom secret management service (requested by one team)
      reason: the managed store plus CSI driver covers it. The team's actual
      problem was rotation without a deploy - a 2-day extension, not a service.
      OFFERED AND ACCEPTED as an alternative.
```

```text
The three mechanisms for saying no - none of them require courage.

  1. ERROR BUDGET POLICY (signed by the leadership that requests capabilities)
     "the deploy capability has consumed 91% of its budget; the policy we agreed
      pauses new feature work on it until burn stops."
     -> a pre-agreed rule, not a judgement. Nobody argues with their own signature.

  2. PUBLISHED CAPACITY SPLIT
     "we can build the portal this quarter. It displaces GPU scheduling, which
      unblocks 6 teams and removes 4 exceptions. Which would you prefer?"
     -> converts a refusal into a visible trade-off with a decision-maker.

  3. EVIDENCE RANKING
     "the portal would address 0 measured support questions. Exposing deploy
      status addresses 41 a month. Both are discovery-adjacent; one has evidence."
     -> a comparison, not an opinion.

  And always: OFFER THE ALTERNATIVE. The secret-management request above was
  satisfied by a 2-day extension because the team's real problem was rotation,
  not the store. Most "no" answers have a smaller "yes" inside them.
```

## Interview tips

- Lead with the reframe: requests are the weakest input, and the platform's own measurements are stronger. Then name the evidence sources you already have.
- The connection to earlier practices is what makes this answer strong - escape hatches, exceptions, break-glass activations, and support categories are all roadmap inputs, which shows the whole operating model hangs together.
- The explicit capacity split is the practical mechanism that stops the plan failing in week three, and stating it up front is what stops operational load silently consuming build capacity.
- Prioritising by how many future teams a capability unblocks, and preferring support-load reduction over new features because it compounds, is the ranking rule to state.
- Publishing declined items with reasons is what changes how teams engage, and it is a distinctive practice.
- The three no-mechanisms - error budget policy, capacity split, evidence ranking - are the substance of the second half. Emphasise that they replace courage with a rule.
- Saying no to your own ideas, with a concrete example, is the most credible thing you can offer here. Interviewers are specifically probing for whether you build what is interesting or what is needed.

---

[⬅ Back to Platform Team and Operating Model](./README.md) · [All topics](../README.md)
