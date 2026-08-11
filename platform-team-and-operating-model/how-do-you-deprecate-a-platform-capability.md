---
title: "How do you deprecate a platform capability?"
id: 127
category: "Platform Team and Operating Model"
difficulty: "Advanced"
tags:
  - platform-engineering
  - platform-team-and-operating-model
  - interview-questions
---

# How do you deprecate a platform capability?

**Short answer:** Provide the replacement first, migrate the consumers yourself, escalate the deprecation signal on a published timeline, and remove only when verified usage reaches zero - not when the deadline passes. Deprecation is harder for an internal platform than for a public API because your users cannot switch to a competitor, so the migration is unambiguously your work rather than theirs.

## Detail

**Nothing can be deprecated until the replacement exists and is better.** Announcing removal before there is somewhere to go generates anxiety and no migration. The order is: build the replacement, prove it with a few consumers, then start the deprecation.

**Know your consumers exactly.** Query actual usage rather than relying on a wiki page - which services, which teams, how often, and which are on a version that will break. Deprecating something with an unknown consumer set is how you cause an outage in a service nobody remembered depended on you.

**Escalate the signal rather than sending one email.** A deprecation notice that appears once is missed. The pattern that works is progressive noise: documentation marked deprecated, then a warning emitted on every use, then a comment on pull requests that touch it, then a scorecard finding, then a build warning, then removal. Each step is louder and each gives a further chance to act.

**Migrate for people.** Codemod, bot-raised pull requests, and an offer to merge. Batch them - ten repositories, watch, continue - because the first batch will find defects in your migration script. Asking forty teams to each spend an afternoon means half will not, and you will maintain both indefinitely.

**Publish a timeline and hold it, with one exception.** Dates create the necessary pressure. The exception is that you do not remove on the date if consumers remain - you remove when verified usage is zero. Removing on schedule with three consumers still connected is choosing to cause an outage to keep a commitment, which is the wrong trade.

**Verify by querying, not by asking.** "Has everyone migrated?" produces optimistic answers. Usage telemetry produces facts. And note the distinction between a merged migration and a deployed one: a pull request merged but not released has not removed the dependency.

**Handle the stragglers individually.** When you are down to two or three, the conversation is direct rather than broadcast - find out what is blocking them, and either fix it or grant a time-boxed exemption with the maintenance cost stated. Most long tails are one specific blocker, not indifference.

**Decide what happens to the remaining consumers if you must remove anyway.** Occasionally a security or cost reason forces removal before everyone has moved. That needs an explicit decision, leadership awareness, and support for the affected teams during the transition - it should be a considered exception, not the routine end of every deprecation.

**Remove it properly.** Delete the code, the infrastructure, the documentation, the dashboards, and the alerts. A capability left running because removing it feels risky is exactly the accumulated cost deprecation was meant to shed - and unremoved deprecated capabilities are the reason platform teams end up spending most of their time operating.

**Write down the reason.** Six months later someone will ask why the old thing was removed. A short record - why, what replaced it, what the trade-offs were - prevents the decision being relitigated and helps the next deprecation.

## Example

```text
Deprecating the v1 pipeline in favour of the shared reusable workflow.
41 consumers. Twelve weeks, zero broken teams.

  WEEK 0 - REPLACEMENT EXISTS AND IS PROVEN
    shared workflow live for 4 months, 12 teams on it voluntarily, measurably
    better (deploy 38m -> 6m). NOTHING was announced before this was true.

  WEEK 1 - KNOW THE CONSUMERS EXACTLY
    $ platform usage --capability pipeline-v1
      41 repositories, 8 teams
      of which: 6 use a v1-only feature (custom deploy step) -> needs a
                replacement feature FIRST
                3 are inactive repos (no commit in 12 months) -> may just be
                deleted
    -> the 6 blocked repos changed the plan: build the missing feature in week 2
       rather than discovering it in week 8.

  WEEK 2 - MISSING FEATURE SHIPPED, THEN ANNOUNCE
    timeline published: deprecated now, removal no earlier than week 12
    docs marked deprecated with the migration guide

  WEEK 3-4 - ESCALATING SIGNAL, not one email
    every pipeline run emits a deprecation warning in its log
    a bot comments on any PR touching a v1 pipeline file

  WEEK 3-9 - MIGRATE FOR PEOPLE, IN BATCHES
    codemod written and tested against a corpus of real consumer repos
    batch 1 (8 repos): 2 codemod defects found and fixed. THIS IS WHY YOU BATCH.
    batches 2-5 (30 repos): PRs opened, offer to merge
    3 inactive repos: confirmed unused, archived rather than migrated

  WEEK 8 - LOUDER
    scorecard finding for any service still on v1
    a warning banner in the portal for the owning teams

  WEEK 10 - VERIFY BY QUERYING, NOT ASKING
    $ platform usage --capability pipeline-v1
      2 repositories remain
        team-legacy/reporting-etl   PR open but NOT MERGED
        team-data/warehouse-sync    PR merged but NOT DEPLOYED  <-- merged is
                                                                   not migrated
    -> direct conversations with two teams, not a deadline email to eight.

  WEEK 12 - the published date arrives with 1 consumer left. DO NOT REMOVE.
    team-legacy blocked by a genuine issue in their test suite.
    -> 3-week time-boxed exemption, blocker fixed jointly.
    Removing on the date to keep the commitment would have been choosing to cause
    an outage. The date creates pressure; zero usage authorises removal.

  WEEK 15 - VERIFIED ZERO
    $ platform usage --capability pipeline-v1
      (no consumers)
    -> remove: code, the runner infrastructure, docs, dashboards, alerts.
       A capability left running "just in case" is the accumulated cost this
       whole exercise existed to shed.

  WEEK 15 - RECORD THE DECISION
    ADR: what was removed, why, what replaced it, what the trade-offs were.
    Six months later, someone will ask. This stops it being relitigated.
```

```yaml
# The escalating signal as configuration, so the noise increases on schedule
# rather than depending on someone remembering to send another email.
apiVersion: platform.example.com/v1
kind: Deprecation
metadata: { name: pipeline-v1 }
spec:
  replacement: { capability: shared-workflow, docs: "go/platform-pipelines" }
  announced: 2026-05-04
  earliestRemoval: 2026-07-27 # a floor, NOT a commitment to remove on this date
  removeWhen: verified-zero-usage # the actual authorisation to remove
  signals:
    - { from: 2026-05-04, type: docs-banner }
    - { from: 2026-05-11, type: runtime-warning, channel: pipeline-log }
    - { from: 2026-05-18, type: pr-comment, on: touches-deprecated-file }
    - { from: 2026-06-29, type: scorecard-finding, severity: warning }
    - { from: 2026-07-13, type: portal-banner, audience: owning-teams }
  migration:
    automated: true
    codemod: scripts/migrate-pipeline-v1.py
    raisePullRequests: true
    batchSize: 10 # the first batch finds the codemod's defects
    offerToMerge: true
```

## Interview tips

- The ordering is the answer: replacement first, proven, then deprecate. Announcing removal before there is somewhere to go produces anxiety and no migration.
- Querying actual usage rather than trusting a list is essential, and finding consumers blocked by a missing feature in week 1 rather than week 8 is a concrete benefit of doing it.
- The escalating signal - docs, runtime warning, pull-request comment, scorecard, portal banner - is far better than a single announcement, and expressing it as configuration shows you have automated it.
- "Migrate for people" with batched, tested codemods, and the observation that the first batch finds your defects, is the practical core.
- The date-versus-zero-usage distinction is the most important judgement in the answer: the date creates pressure, verified zero usage authorises removal. Removing on schedule with consumers left is choosing an outage.
- "Merged is not migrated" is a precise detail that shows you have verified rather than assumed.
- Actually removing everything, and recording the decision so it is not relitigated, closes the loop - unremoved deprecated capabilities are why platform teams end up only operating.

---

[⬅ Back to Platform Team and Operating Model](./README.md) · [All topics](../README.md)
