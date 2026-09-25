---
title: "How do you measure the impact of AI coding tools on developer productivity?"
id: 26
category: "Developer Experience"
difficulty: "Advanced"
tags:
  - platform-engineering
  - developer-experience
  - interview-questions
---

# How do you measure the impact of AI coding tools on developer productivity?

**Short answer:** Measure three layers separately (utilisation, impact, and cost) and do not trust any of them on their own. Utilisation tells you who uses the tools and how deeply. Impact has to be measured on outcomes you already track, such as PR throughput, lead time, change fail rate, rework, and developer-reported time savings, and it has to compare like with like: the same engineers before and after, or a staggered rollout, not enthusiasts against sceptics. Cost covers licences, token spend, and the extra review load AI output creates. The two traps are vendor metrics like suggestion acceptance rate, which measure activity rather than value, and self-reported speed-ups, which controlled studies have shown can point in the wrong direction.

## Detail

**Why this is harder than it looks.** Three pieces of evidence set the tone for a serious answer:

- **Perception is unreliable.** METR's 2025 randomised controlled trial with experienced open-source developers working in their own repositories found they took about 19% _longer_ on tasks when allowed AI tools, while believing afterwards that the tools had made them about 20% faster. That does not generalise to every setting, but it shows that "developers say it saves time" is not evidence on its own.
- **Speed and stability can diverge.** DORA's 2024 report found higher AI adoption associated with slightly lower delivery throughput and stability. The 2025 report, focused entirely on AI-assisted development, found throughput now improving with adoption but instability (change failures and rework) still rising. More code arrives faster; more of it needs fixing.
- **AI amplifies the system it lands in.** DORA's 2025 AI capabilities model names the conditions under which AI helps: a clear and communicated AI stance, healthy data ecosystems, AI-accessible internal data, strong version control practices, working in small batches, user-centric focus, and quality internal platforms. Organisations with weak tests and slow review get larger volumes of risky change, not productivity.

**Layer 1: utilisation.** Measure depth, not seats. Licences assigned and weekly active users are a starting point. More useful are the share of merged PRs with meaningful AI involvement, the split between autocomplete, chat, and autonomous agents, and which tasks developers use them for. Attribution is the hard part. Two practical sources: the AI gateway or proxy that the platform team runs in front of model providers (which also gives you cost and usage per team), and commit or PR metadata. Many agents add a co-author trailer to commits, and you can require one by convention.

**Layer 2: impact.** Use metrics you were already tracking before the rollout, so there is a baseline:

| Signal                         | Measures                        | Watch out for                                     |
| ------------------------------ | ------------------------------- | ------------------------------------------------- |
| PR throughput (org level)      | Flow of work                    | Smaller PRs inflate it; never read per individual |
| Lead time, split by stage      | Where time moved                | Coding time falls, review wait often rises        |
| Change fail rate, rework rate  | Whether faster change is safe   | The DORA finding: instability rises first         |
| Review time per PR, PR size    | Load moved onto reviewers       | The "verification tax" hides here                 |
| Survey: time saved, confidence | Perceived value, where it helps | Inflated; use it for direction, not magnitude     |
| Defects, security findings     | Longer-term quality             | Lags by months; needs a long enough window        |

The design of the comparison matters more than the choice of metric. Early adopters are usually stronger or more motivated engineers, so "AI users ship 30% more" mostly measures who adopts. Better designs, in order of strength: a staggered rollout by team with a difference-in-differences comparison; within-person before and after comparisons over at least a quarter; and matched cohorts controlling for tenure, team, and codebase. Report ranges, not single numbers, and keep the time window long enough to include the quality lag.

**Layer 3: cost.** Licences are the visible part. Token-based pricing for agents makes spend variable and potentially large per engineer, so it needs the same showback treatment as cloud cost: attributed per team through the gateway, with budgets and alerts. Include the hidden costs too: senior engineers' review time, incidents traced to generated code, and the platform team's time running the gateway, the MCP servers, and the policy around them.

**Agents change the unit of measurement.** When an agent opens a PR on its own, the agent becomes a platform consumer with its own measures: merge rate of agent PRs, time and review effort to merge, rework or revert rate afterwards, and the share of agent tasks that needed a human to take over. Track these separately from human-authored work, or the averages hide both the successes and the failures.

**What a platform team does with the results.** The findings usually point back at the platform. If review wait is the new bottleneck, invest in automated checks that reduce what a human must verify. If rework rises, invest in tests, preview environments, and progressive delivery. If agents fail on internal context, expose the catalogue, docs, and platform actions through MCP servers so they stop guessing. The AI rollout becomes a stress test of the golden path.

**The ethical line.** Never use AI usage data to rank or performance-manage individuals, and say so publicly before collecting it. The moment developers suspect usage is being scored, they inflate usage and hide failures, and you lose the signal you were trying to collect.

## Example

```text
Measurement plan and first readout: staggered rollout of an AI coding agent,
180 engineers, cohort A enabled in Q1, cohort B in Q2. Org-level only.

UTILISATION (from the AI gateway + PR trailers)
  weekly active users                     A: 81%        B (after enable): 74%
  merged PRs with agent involvement       A: 34%
  agent-opened PRs merged without rework  A: 61%

IMPACT - difference-in-differences, Q1 (A enabled, B not yet)
                                   A change   B change   estimated effect
  PRs merged / eng / week          +14%       +3%        ~ +11%  (range 6-16%)
  lead time p50                    -9%        -2%        ~ -7%
    of which: coding stage         -31%       -1%
    of which: waiting for review   +22%       +4%        <- bottleneck moved
  change fail rate                 +1.8 pts   +0.2 pts   ~ +1.6 pts  <- watch
  rework rate                      +2.1 pts   +0.3 pts   ~ +1.8 pts  <- watch
  survey "time saved per week"     median 3h             (direction, not magnitude)

COST
  token spend: attributed per team via the gateway; 3 teams above budget
  review load: +18% reviewer hours per PR for agent-involved PRs

DECISIONS
  1. Keep rollout, but add required contract tests and preview environments
     for agent PRs before widening agent autonomy.
  2. Review is the constraint: invest in automated pre-review checks.
  3. Re-measure change fail and rework rates after one more quarter.
```

## Interview tips

- Structure the answer as utilisation, impact, and cost, and say that acceptance rate and lines generated are activity metrics, not impact.
- Cite the evidence that perception misleads (the METR trial) and that instability can rise with throughput (DORA 2024 and 2025). It shows you know the research, not just the vendor pitch.
- Spend time on comparison design: selection bias in early adopters, staggered rollouts, difference-in-differences. That is what makes this an Advanced answer.
- Name the bottleneck shift from writing to reviewing and verifying code. It is the most common real-world finding.
- Link it back to the platform: AI amplifies the system, so tests, small batches, fast review, and a good internal platform are what turn adoption into productivity. See [DORA metrics](./what-are-the-dora-metrics-and-what-do-they-measure.md) and [measurement frameworks](./how-do-space-devex-and-dx-core-4-differ-as-measurement-frameworks.md).

---

[⬅ Back to Developer Experience](./README.md) · [All topics](../README.md)
