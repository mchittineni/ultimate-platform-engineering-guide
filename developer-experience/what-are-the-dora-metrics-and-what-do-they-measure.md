---
title: "What are the DORA metrics and what do they measure?"
id: 16
category: "Developer Experience"
difficulty: "Beginner"
tags:
  - platform-engineering
  - developer-experience
  - interview-questions
---

# What are the DORA metrics and what do they measure?

**Short answer:** The DORA metrics are the software delivery performance measures from Google's DevOps Research and Assessment programme. They measure how quickly and how safely a team gets changes into production. There were originally four: deployment frequency, change lead time, change fail rate, and time to restore service. The current model has five, grouped into **throughput** (change lead time, deployment frequency, failed deployment recovery time) and **instability** (change fail rate, deployment rework rate). They measure the delivery system, not individual people, and they are most useful as trends for one team or service over time.

## Detail

**The five metrics, defined:**

| Metric                          | Group       | What it measures                                                                    |
| ------------------------------- | ----------- | ----------------------------------------------------------------------------------- |
| Change lead time                | Throughput  | Time from a change being committed to it running in production                      |
| Deployment frequency            | Throughput  | How often changes are deployed to production                                        |
| Failed deployment recovery time | Throughput  | How long it takes to recover when a deployment fails and needs intervention         |
| Change fail rate                | Instability | Share of deployments that need immediate intervention (rollback, hotfix)            |
| Deployment rework rate          | Instability | Share of deployments that are unplanned and happen because of a production incident |

Two changes from the original "four keys" are worth knowing. "Time to restore service" (often called MTTR) was narrowed to _failed deployment recovery time_, so that it measures recovery from the team's own changes rather than from every outage, including a cloud provider's. And _rework rate_ was added in 2024 because change fail rate alone missed the pattern of shipping a fix, then a fix for the fix.

**Why throughput and stability go together.** The central finding of DORA's research, repeated over roughly a decade of surveys, is that speed and stability are not a trade-off. Teams that deploy small changes often also tend to fail less and recover faster, because small changes are easier to review, test, and roll back. That is why the metrics are presented as a set. Improving deployment frequency while change fail rate rises is not an improvement.

**Who uses them and why a platform team cares.** Engineering leaders use DORA metrics to see whether delivery is getting better. Platform teams care because most of the levers are platform capabilities: pipeline speed drives lead time, safe automated deploys drive frequency, progressive delivery and fast rollback drive recovery time, and good test infrastructure drives fail rate. A platform team can use the metrics to show that its golden path actually helps. A team that moves onto it should see its numbers improve.

**How you collect them.** Mostly from systems you already have. Lead time comes from joining commit timestamps with deployment events. Deployment frequency comes from your CD tool. Failures and recovery come from linking deployments to rollbacks, incidents, or hotfixes. The hard part is the definitions, not the tooling. You need to decide what counts as a deployment, what counts as a failure, and which environment is "production", then apply that the same way to every team.

**What they do not measure.** DORA metrics describe the path from commit to production. They say nothing about the time before the first commit (waiting for requirements, access, or an environment), about developer satisfaction, or about whether the thing shipped was valuable. They also do not tell you _why_ a number is bad. That is why they are usually paired with a developer experience survey. See [What is developer experience and how do you measure it?](./what-is-developer-experience-and-how-do-you-measure-it.md).

**The traps.** Do not use DORA metrics to rank teams or assess individuals. A team that owns a payments ledger and a team that owns a marketing site should not have the same deployment frequency target. Once the numbers are used for judgement, they get gamed: deploys get split to raise frequency, and incidents get reclassified to lower fail rate. Use percentiles rather than averages for time metrics, because a few very slow changes hide inside an average. Treat the published performance clusters (elite, high, medium, low) as context rather than targets.

**The current direction.** DORA's 2025 report focused on AI-assisted development. It found that AI adoption now correlates with higher throughput but still with higher instability. More code is shipped faster, and more of it fails or needs rework. That makes the instability metrics more important, not less, for any organisation rolling out AI coding tools.

## Example

```sql
-- Change lead time (p50 and p95) and deployment frequency per service,
-- from a warehouse table of production deployments joined to their commits.
-- Definitions agreed up front: a deployment = a successful rollout to prod;
-- lead time = first commit in the change -> that rollout.
SELECT
  d.service,
  COUNT(DISTINCT d.deploy_id) / 4.0                          AS deploys_per_week,
  PERCENTILE_CONT(0.5)  WITHIN GROUP (ORDER BY d.deployed_at - c.first_commit_at) AS lead_time_p50,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY d.deployed_at - c.first_commit_at) AS lead_time_p95,
  AVG(CASE WHEN d.required_intervention THEN 1.0 ELSE 0 END) AS change_fail_rate
FROM deployments d
JOIN changes c ON c.change_id = d.change_id
WHERE d.environment = 'production'
  AND d.deployed_at >= CURRENT_DATE - INTERVAL '28 days'
GROUP BY d.service;
```

```text
Reading the result as a trend, not a league table:

  service    deploys/wk  lead p50  lead p95  fail rate   note
  checkout   11.5        3.1h      2.8d      6%          p95 dominated by review wait
  pricing    4.0         9.4h      6.0d      14%         moved to golden path last month
  ledger     1.2         1.5d      4.1d      3%          deliberately slow, regulated

  The useful question is "is pricing improving since it moved to the golden path?",
  not "why is ledger slower than checkout?".
```

## Interview tips

- Name all five metrics and the throughput and instability grouping. Knowing about rework rate and the change from MTTR to failed deployment recovery time shows your knowledge is current.
- Make the key point: speed and stability improve together. Small, frequent changes are the mechanism.
- Say what the metrics miss (pre-commit time, satisfaction, value) and that you would pair them with a survey.
- Refuse to rank teams with them. Expect the follow-up "leadership wants a team leaderboard" and answer with trends per team instead.
- Mention the 2025 AI finding (more throughput, still more instability) if the conversation turns to AI tools. It is a strong, current detail.

---

[⬅ Back to Developer Experience](./README.md) · [All topics](../README.md)
