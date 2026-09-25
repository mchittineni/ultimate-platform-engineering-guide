---
title: "What is toil and how does a platform team reduce it?"
id: 202
category: "Platform Reliability"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-reliability
  - interview-questions
---

# What is toil and how does a platform team reduce it?

**Short answer:** Toil is operational work that is manual, repetitive, automatable, reactive, and produces no lasting improvement - and, crucially, grows in proportion to the size of what you run. Creating a database by hand from a ticket, rotating a certificate, or restarting the same stuck job every week are toil. A platform team reduces it by measuring where it goes, eliminating the work that should not exist, and turning the rest into self-service or automation, both for itself and for the engineering teams that use the platform.

## Detail

**The defining test is how it scales.** The Google SRE definition lists the properties: manual, repetitive, automatable, tactical (interrupt-driven rather than planned), no enduring value, and growing linearly with the service. The last is the one that matters most. If onboarding twice as many teams means twice as many provisioning tickets, the team's capacity is consumed by growth itself and nothing ever improves.

**Not all operational work is toil.** Designing an SLO, debugging a novel incident, writing a postmortem, or planning a migration are operational but not toil, because each needs judgement and leaves the system better. Overhead such as meetings is not toil either. Keeping these separate matters because "reduce operational work" is a vague goal, whereas "reduce toil" points at specific, repeatable tasks.

**Why it matters.** Toil crowds out engineering work, which is the only thing that reduces future toil - a vicious cycle. It also causes burnout and mistakes, since repetitive manual steps are exactly where humans err. The SRE book suggests keeping toil below half of a team's time; the exact number matters less than measuring it at all.

**Step one is to measure.** Tag tickets and interrupts by type, and log time spent on recurring tasks for a few weeks. The results are almost always concentrated: a handful of request types make up most of the volume. That gives you a ranked list of what to fix, rather than automating whatever is most annoying this week.

**Step two is to eliminate before automating.** Ask whether the task needs to exist. A weekly manual restart usually means a memory leak or a missing liveness probe; the fix is the bug, not a cron job. An approval step that is always granted can often be replaced by a policy that encodes what the approver checks.

**Step three is to turn requests into self-service.** Most platform toil is requests from other teams: a new namespace, a database, DNS records, access to a cluster. Each ticket makes the requesting engineer wait and makes a platform engineer do the same steps again. Replacing the ticket with an API, a template, or a declarative resource the team creates itself removes the wait and the toil at the same time. This is why [self-service is the defining property of a platform](../platform-engineering-fundamentals/what-is-self-service-and-why-is-it-the-defining-property-of-a-platform.md).

**Remember toil the platform pushes onto its users.** A platform can have low toil for its own team while every product team spends hours a month on manual upgrades, copy-pasted pipeline changes, or chasing certificate expiry. That is still toil in the organisation; it has just moved. Measuring consumer toil - through surveys or by looking at the recurring changes teams make - is part of the platform's job, and removing it is often the platform's biggest source of value.

**Trade-offs.** Automation has costs: it must be built, tested, and maintained, and a broken automation can fail faster and more widely than a person would. Automating a task that happens twice a year is rarely worth it; automating one that happens forty times a week almost always is. Automate the most frequent, best-understood tasks first, keep a manual fallback for rare ones, and make sure automated actions are logged and reversible.

## Example

```text
Platform team interrupt log, 6 weeks, tagged by type.

  REQUEST TYPE                        COUNT   AVG TIME   TOTAL    ACTION
  new namespace + RBAC for a team       64      25 min    27h     self-service template
  new Postgres database                 38      50 min    32h     declarative resource
  "why is my deploy stuck?"             51      20 min    17h     status in the deploy
                                                                  UI + runbook link
  certificate renewal, legacy ingress   12      40 min     8h     move to cert-manager
  weekly restart of report exporter      6      15 min     2h     fix the leak (eliminate)
  other (one-off)                       29      35 min    17h     leave manual
  ---------------------------------------------------------------------------
  TOTAL                                200               102h    ~17h a week

  The top two request types are 57% of the time. Fixing them first returns
  more than a day a week to engineering work.
```

```yaml
# After: a team requests its own database. No ticket, no waiting - the
# platform's composition creates the instance, credentials, and monitoring.
apiVersion: platform.example.com/v1alpha1
kind: PostgresInstance
metadata:
  name: orders-db
  namespace: team-orders # a namespaced composite resource (Crossplane v2 style)
spec:
  size: small
  version: "17"
  backupTier: standard
  connectionSecretName: orders-db-credentials # the composition writes it
```

## Interview tips

- Give the definition with its properties, then single out the one that matters most: toil grows linearly with the size of what you run.
- Distinguish toil from other operational work - incident debugging and postmortems are not toil because they need judgement and leave lasting value.
- Describe the order of operations: measure, eliminate, then automate or make self-service. "Eliminate first" is the step candidates usually skip.
- Name the user: most platform toil is requests from other teams, and replacing the ticket with self-service removes their waiting and your toil together.
- Mention consumer toil - work the platform pushes onto product teams - as a distinct, often larger problem.
- Acknowledge the cost of automation, and that frequency decides what is worth automating.

---

[⬅ Back to Platform Reliability](./README.md) · [All topics](../README.md)
