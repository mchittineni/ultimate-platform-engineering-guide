---
title: "What are the main cloud pricing models?"
id: 225
category: "Platform FinOps"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-finops
  - interview-questions
---

# What are the main cloud pricing models?

**Short answer:** Almost every cloud charge is one of four shapes: on-demand (pay per unit of time or usage, no commitment), committed (a discount in exchange for promising a level of usage or spend for one or three years), spot (a deep discount on spare capacity the provider can reclaim at short notice), and consumption-based serverless and managed services (pay per request, per gigabyte, per token). On top of these sit the charges people forget - data transfer, storage tiers, and licensing. A platform team's job is to put each workload on the right model by default so that product teams do not have to understand all of them.

## Detail

**On-demand is the baseline everything else is discounted from.** You pay per second or per hour for a virtual machine while it runs, with no commitment, and you can stop at any time. It is the most flexible and the most expensive per unit. It is the right model for anything whose usage you cannot predict yet - new services, short experiments, the burst above your steady baseline.

**Commitments trade flexibility for a discount.** The provider gives you a lower rate because you promise to pay for a level of usage whether you use it or not. The names differ by provider but the mechanism is the same:

| Provider | Resource-based commitment              | Spend-based / flexible commitment              |
| -------- | -------------------------------------- | ---------------------------------------------- |
| AWS      | Reserved Instances                     | Savings Plans (Compute, EC2 Instance, others)  |
| Azure    | Azure Reservations                     | Azure savings plan for compute                 |
| GCP      | Resource-based committed use discounts | Spend-based (flexible) committed use discounts |

The trade-off is lock-in to a term. Resource-based commitments give a bigger discount but tie you to a machine family or region; spend-based ones apply across families, sizes, and often services, for a slightly smaller discount. GCP also applies sustained use discounts automatically to some machine types that run for a large part of the month, with no commitment at all.

**Spot capacity is cheap because it can disappear.** AWS Spot Instances, Azure Spot Virtual Machines, and GCP Spot VMs sell the provider's unused capacity at a large discount, but the provider can reclaim it with a short warning - roughly two minutes on AWS, and less on the others. It is excellent for work that can be interrupted and retried: CI runners, batch jobs, stateless services with several replicas. It is wrong for a single-replica database.

**Consumption pricing charges for what you actually do.** Functions are billed per invocation and per unit of memory-time; object storage per gigabyte-month plus per request; managed queues per message; AI model APIs per input and output token. There is nothing idle to pay for, which is why it looks cheap at low volume - and it can become the most expensive option at high, steady volume, where a provisioned resource on a commitment would cost less.

**The hidden lines are often the surprising ones.** Data transfer between zones, between regions, and out to the internet is charged separately and is easy to generate by accident - a chatty service calling a database in another zone pays on every request. Storage has tiers (hot, infrequent access, archive) where the cheaper tiers charge more to read. Some software carries a licence charge on top of the compute, and marketplace or SaaS purchases add their own pricing units such as credits.

**Who this matters to on a platform.** Product engineers should not need to know which commitment covers their pod. The platform team buys commitments centrally against the estate's steady baseline, runs interruptible workloads on spot node pools, sets sensible storage tiers and retention by default, and keeps traffic zone-local where it can. The user of the platform - a product team - sees one simple choice, such as "this workload is interruptible", and gets the right pricing model underneath.

**The trade-off in one sentence:** the more you commit and the more interruption you tolerate, the less you pay per unit, and the more a wrong forecast or a wrong workload placement costs you.

## Example

```text
One service, priced four ways - the shape of the decision, not the numbers.

  WORKLOAD: orders-api, 12 replicas, steady 24x7 traffic, +40% at peak

  PORTION                  MODEL CHOSEN              WHY
  steady 8 replicas        commitment (spend-based)  runs every hour of the year;
                                                     the platform's central
                                                     commitment covers it
  peak +4 replicas         on-demand                 exists a few hours a day;
                                                     committing to it would mean
                                                     paying for idle capacity
  nightly reindex job      spot                      interruptible, retried on
                                                     failure, no user waiting
  receipt PDF generation   functions (per request)   bursty, low volume, nothing
                                                     to keep warm

  HIDDEN LINES CHECKED
    cross-zone calls to the database ....... pinned to zone-aware routing
    receipts in object storage ............. moved to infrequent-access tier
                                              after 30 days
    egress to the payment provider ......... unavoidable, measured and reported

  What the product team declared in the service spec:
    replicas: { min: 8, max: 12 }
    jobs.reindex.interruptible: true
  Everything in the MODEL CHOSEN column was a platform default.
```

## Interview tips

- Group the models by mechanism - on-demand, committed, spot, consumption - before naming any product. Interviewers want to see that you know Savings Plans and committed use discounts are the same idea.
- Always state the trade-off for each: commitments trade flexibility, spot trades reliability, consumption trades cost at scale.
- Mention data transfer early. It is the line most candidates forget and the one most likely to cause a surprise bill.
- Say that serverless is not automatically cheaper: cheap at low or spiky volume, often more expensive at high steady volume.
- Name the user: the platform chooses the pricing model by default so product teams make one simple declaration. See [How do you use commitments and spot capacity on behalf of every team?](./how-do-you-use-commitments-and-spot-capacity-on-behalf-of-every-team.md) for the follow-up.
- Avoid quoting discount percentages or prices - they change often and vary by term, region, and instance family.

---

[⬅ Back to Platform FinOps](./README.md) · [All topics](../README.md)
