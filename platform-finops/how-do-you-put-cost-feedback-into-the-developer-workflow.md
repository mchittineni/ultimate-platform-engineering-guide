---
title: "How do you put cost feedback into the developer workflow?"
id: 232
category: "Platform FinOps"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-finops
  - interview-questions
---

# How do you put cost feedback into the developer workflow?

**Short answer:** Show the cost consequence of a change at the moment the change is made - an estimate on the pull request that alters infrastructure or resource requests, a cost field next to the size choice in the portal or service template, and an alert to the owning team within a day when actual spend deviates. A monthly report arrives too late to change the decision it describes. The design constraints are that the number must be roughly right, attributable to a specific change, quiet when nothing matters, and never a gate on its own except for guardrails the organisation has agreed.

## Detail

**Why timing is the whole game.** An engineer choosing between a large and an extra-large instance, or setting a memory request, is making a cost decision. If the consequence shows up a month later in an aggregate report, nobody can connect it to the choice, and the report starts an argument rather than changing behaviour. The same number shown in the review of the pull request is a design input, and is acted on at almost zero cost.

**The feedback points, from earliest to latest:**

| Point in the workflow         | What the developer sees                                      | Mechanism                                             |
| ----------------------------- | ------------------------------------------------------------ | ----------------------------------------------------- |
| Template or portal choice     | Estimated monthly cost next to each size or tier option      | Price table in the scaffolder or service spec schema  |
| Pull request (infrastructure) | Cost diff of the Terraform or OpenTofu plan                  | Infracost or equivalent in CI, posted as a PR comment |
| Pull request (Kubernetes)     | Cost delta of changed replicas and requests                  | Platform check: requests x replicas x effective rate  |
| After deploy (hours to days)  | Anomaly alert when a service's spend deviates from its trend | Daily cost data per service, alert to owning team     |
| Service page                  | Cost trend, unit cost, top findings with the fix attached    | Portal plugin reading the platform's cost dataset     |
| Periodic                      | Showback per team                                            | The same dataset, aggregated                          |

The earliest points change decisions; the later ones catch what the earlier ones missed.

**Make the estimate use the right rate.** A pull request comment based on list price will overstate cost for anything covered by commitments and understate nothing, and engineers learn to ignore it. Use the organisation's effective rates where you can, show a range where usage-based components are uncertain, and label estimates as estimates.

**Keep it quiet.** A comment on every pull request, including the ones that change nothing, is noise that trains people to scroll past. Post only when the delta crosses a threshold, and say in one line what changed and why. Anomaly alerts need the same discipline: route to the owning team's channel, include the likely cause (which resource, which change, which deploy), and do not page anyone for cost.

**Attribute to the change, not just the service.** "team-search's spend is up" is weak. "Spend on search-indexer rose after the deploy that set `replicas: 24`, commit abc123" is actionable. That requires the cost data to be joined with deployment events, which the platform already has.

**Gates only for agreed guardrails.** Blocking a merge because it costs more is usually wrong - spending more is often the right decision, and a gate turns a design input into an obstacle to route around. Reserve blocking for limits the organisation has agreed in advance: a GPU instance type in a sandbox account, a non-production environment without a TTL, a change that exceeds the team's quota. Everything else is information, with an optional required approval above a large threshold.

**AI agents are now part of the workflow.** Coding assistants and agents write a growing share of infrastructure changes. The same cost check runs on their pull requests, and exposing the cost dataset through an internal API or a Model Context Protocol server lets an agent ask "what would this change cost?" before proposing it - the same feedback, earlier.

**Who it serves.** The product engineer, who gets the consequence of a decision while they can still change it, without learning the pricing model. The platform team owns the pipeline, the rate table, the thresholds, and the guardrails. Finance gets fewer surprises.

**The trade-offs.** Estimates are approximate, and usage-driven costs (data transfer, requests, tokens) are hard to predict from code. Over-emphasising cost can make engineers under-provision reliability. And the feedback is only as good as attribution - without owners on resources, alerts go nowhere.

## Example

```yaml
# .github/workflows/cost-diff.yml - post a cost diff on infrastructure PRs
name: cost-diff
on:
  pull_request:
    paths: ["infra/**"]
permissions:
  contents: read
  pull-requests: write
jobs:
  infracost:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v7
        with: { ref: "${{ github.base_ref }}", path: base }
      - uses: actions/checkout@v7
        with: { path: head }
      - name: Install Infracost
        run: curl -fsSL https://raw.githubusercontent.com/infracost/infracost/master/scripts/install.sh | sh
      - name: Baseline from the target branch
        env: { INFRACOST_API_KEY: "${{ secrets.INFRACOST_API_KEY }}" }
        run: infracost breakdown --path base/infra --format json --out-file /tmp/base.json
      - name: Diff against the PR
        env: { INFRACOST_API_KEY: "${{ secrets.INFRACOST_API_KEY }}" }
        run: infracost diff --path head/infra --compare-to /tmp/base.json --format json --out-file /tmp/diff.json
      - name: Comment only when it changes something
        env: { INFRACOST_API_KEY: "${{ secrets.INFRACOST_API_KEY }}" }
        run: >
          infracost comment github --path /tmp/diff.json
          --repo "${{ github.repository }}"
          --pull-request "${{ github.event.pull_request.number }}"
          --github-token "${{ github.token }}"
          --behavior update
```

```text
The platform's own check for Kubernetes changes, posted on the service repo PR:

  Cost impact: search-indexer (team-search)          estimate, effective rates
    replicas        12  -> 24
    cpu request     1   -> 1
    memory request  4Gi -> 6Gi
    monthly delta   roughly +2.3x current service cost
    unit cost       cost per 1k documents indexed: +60% at current volume

  Not blocking. Owner approval is required above this threshold:
    /approve-cost  (recorded against the change)

  Next day, if actual spend deviates from the estimate by >25%, team-search's
  channel gets an alert linking this PR and the deploy that shipped it.
```

## Interview tips

- Lead with timing: cost shown at the point of decision changes behaviour; a monthly report only informs an argument.
- Walk the feedback points from earliest (template, PR) to latest (anomaly, showback) and explain what each one catches.
- Stress noise control - threshold-based comments, owning-team routing, never paging for cost. It shows you have seen these tools ignored.
- Argue against blocking on cost except for pre-agreed guardrails. Spending more is often correct.
- Use effective rates, not list prices, or the numbers lose credibility.
- Mention that AI agents are now authors of infrastructure changes and consumers of cost data, via the same checks or an MCP server.
- Name the user and link the experience to the rest of the platform: [How do you design service scorecards that teams do not resent?](../developer-experience/how-do-you-design-service-scorecards-that-teams-do-not-resent.md) covers the same "inform, don't nag" balance.

---

[⬅ Back to Platform FinOps](./README.md) · [All topics](../README.md)
