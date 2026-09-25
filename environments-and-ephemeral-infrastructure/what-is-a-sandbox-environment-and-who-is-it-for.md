---
title: "What is a sandbox environment and who is it for?"
id: 110
category: "Environments and Ephemeral Infrastructure"
difficulty: "Beginner"
tags:
  - platform-engineering
  - environments-and-ephemeral-infrastructure
  - interview-questions
---

# What is a sandbox environment and who is it for?

**Short answer:** A sandbox is an isolated place to experiment where mistakes cannot reach anything that matters - no production access, no real data, a spending limit, and an expiry date. Its main users are engineers learning a technology or prototyping an idea, but the same pattern serves data scientists, security teams testing tools, and external developers trying an API. Unlike development or staging, a sandbox is not part of the release path: nothing is promoted out of it.

## Detail

**What makes it a sandbox rather than just another environment.** The defining property is containment. A sandbox gives broad freedom _inside_ a hard boundary, and the boundary is enforced by the platform rather than by people remembering to be careful.

- **Isolated.** Its own cloud account, project, or subscription - or a virtual cluster for Kubernetes experiments - with no network path to production and no shared credentials.
- **No real data.** Only synthetic or public data. A sandbox with a copy of the customer table is a data leak waiting for a date.
- **Budget-limited.** A spending cap with alerts and, ideally, an automatic stop when it is reached. Sandboxes are where someone accidentally launches the largest GPU instance available.
- **Time-limited.** A lease with an expiry, after which everything inside is deleted. Without this, sandboxes quietly turn into unowned production.
- **Broad permissions inside.** Engineers can create almost anything, because the point is to try things without filing a ticket.

**Who it is for:**

| User                          | What they use it for                                           |
| ----------------------------- | -------------------------------------------------------------- |
| Engineers learning or spiking | Trying a new managed service, testing an architecture idea     |
| Platform team                 | Evaluating a new tool or a Kubernetes upgrade before rollout   |
| Data scientists               | Experiments that need compute but not production data          |
| Security teams                | Running offensive or scanning tools in a contained space       |
| External developers           | An API provider's sandbox with test credentials and fake money |

The last row is a different flavour of the same idea: payment providers and other APIs offer sandboxes so integrators can build against realistic behaviour without moving real money. It is worth knowing that these sandboxes often differ from production in latency and error behaviour.

**How a platform provides one.** Self-service is the whole point. An engineer requests a sandbox through the portal or CLI, the platform creates a fresh account or project from a template, applies guardrails, grants the requester access, and records the owner and the expiry. In AWS this is usually account vending into a dedicated sandbox organisational unit with service control policies; Azure and Google Cloud use a sandbox management group or folder with policies attached. Cleanup at the end of the lease deletes the whole account or project, which is far more reliable than trying to delete resources one by one. See [what account vending is and how to automate it](../aws-platform-engineering/what-is-account-vending-and-how-do-you-automate-it.md).

**Trade-offs.** Too many restrictions and the sandbox is useless for experiments, so people go back to trying things in the shared development account. Too few and it becomes a cost or security problem. The balance that usually works: deny a short list of dangerous or very expensive things, allow almost everything else, and rely on the budget and the lease for the rest. Recycling accounts rather than creating new ones each time is faster, but then the cleanup has to be thorough - leftover resources or IAM roles from the previous user are a real risk.

**What a sandbox is not.** It is not a place to run anything others depend on. If a prototype turns out to be useful, it is rebuilt properly through the golden path, not promoted out of the sandbox.

## Example

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyOutsideApprovedRegions",
      "Effect": "Deny",
      "NotAction": ["iam:*", "organizations:*", "sts:*", "support:*", "budgets:*", "cloudfront:*", "route53:*"],
      "Resource": "*",
      "Condition": {
        "StringNotEquals": { "aws:RequestedRegion": ["eu-west-1", "eu-west-2"] }
      }
    },
    {
      "Sid": "DenyLongTermCommitments",
      "Effect": "Deny",
      "Action": [
        "ec2:PurchaseReservedInstancesOffering",
        "savingsplans:CreateSavingsPlan",
        "route53domains:RegisterDomain"
      ],
      "Resource": "*"
    },
    {
      "Sid": "DenyLeavingTheOrganisation",
      "Effect": "Deny",
      "Action": "organizations:LeaveOrganization",
      "Resource": "*"
    }
  ]
}
```

```text
A sandbox lease as the engineer sees it:

  $ platform sandbox create --purpose "try managed Kafka" --days 14
  created   sandbox-alice-0412 (aws account 1111-2222-3333)
  owner     alice (team-search)
  budget    capped, alert at 50% and 80%, resources stopped at 100%
  network   no route to production or shared VPCs
  expires   in 14 days - everything in the account is deleted then
  extend    platform sandbox extend sandbox-alice-0412 --days 7 (max 2 extensions)
```

## Interview tips

- Define a sandbox by its boundary: isolated, no real data, budget-capped, time-limited - and broad freedom inside that boundary.
- Say clearly that nothing is promoted out of a sandbox. That separates it from development and staging.
- Name several users, not just engineers - platform evaluation, data science, security tooling, and external API sandboxes all show breadth.
- Explain the self-service mechanism: vend a whole account or project and delete it at lease end, rather than cleaning resources individually.
- Expect "how do you stop sandboxes getting expensive?" - budgets with automatic stop, leases, and a short deny list rather than a long allow list.

---

[⬅ Back to Environments and Ephemeral Infrastructure](./README.md) · [All topics](../README.md)
