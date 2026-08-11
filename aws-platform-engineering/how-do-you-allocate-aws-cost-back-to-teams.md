---
title: "How do you allocate AWS cost back to teams?"
id: 86
category: "AWS Platform Engineering"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - aws-platform-engineering
  - interview-questions
---

# How do you allocate AWS cost back to teams?

**Short answer:** Use the account as the primary allocation boundary, apply and activate cost allocation tags for everything sharing an account, define cost categories to group accounts and tags into the teams your organisation actually recognises, and use split charge rules to distribute genuinely shared costs. Then accept that some cost cannot be attributed precisely, and choose a defensible split rather than pretending to precision you do not have.

## Detail

**Account-level allocation is the reliable part.** If you run one account per workload per environment, most cost attributes itself with no tagging at all - which is one of the strongest practical arguments for the multi-account model. Anything inside a shared account depends on tags, and tags depend on enforcement.

**Tags must be applied at creation and activated for billing.** Two separate steps, and the second is the one people miss - a tag that exists on resources but has not been activated as a cost allocation tag does not appear in billing data at all, and activation is not retroactive in a useful way. The platform should apply the tag set at provisioning and the organisation should activate them once.

**Enforce tagging rather than requesting it.** Tag policies in Organizations constrain permitted values, service control policies can deny creation of resources without required tags, and the platform's provisioning path should apply them unconditionally so no team has to remember. Untagged resources in a shared account are unattributable, and the fraction of untagged spend is the honest measure of whether your enforcement works.

**Cost categories are the tool that maps AWS billing to your organisation.** They let you define groupings from accounts, tags, and services - so "team-payments" can mean two accounts plus tagged resources in a shared account, expressed once and applied to all reporting. Without them, every report is a bespoke query and nobody agrees on the numbers.

**Split charge rules handle shared cost, and this is where judgement is required.** Shared platform infrastructure - the management cluster, the observability pipeline, transit gateway, central egress - is real spend that belongs to no single team. Split it proportionally by usage where a usage metric exists, evenly where none does, or leave it as a platform cost centre. Any of these is defensible; what is not defensible is leaving a large unallocated bucket that makes every team's number wrong.

**Kubernetes cost needs its own layer.** A shared cluster appears in billing as EC2 or Fargate spend, not as per-namespace cost. Attributing it requires usage data from the cluster - OpenCost or a commercial equivalent - allocating node cost across namespaces by resource requests or usage, plus a share of the cluster's idle capacity and control plane. Node cost divided by requests is the standard approach and it must be explicit about how idle capacity is handled, or teams will dispute the numbers.

**Know the costs that are structurally hard to attribute.** Data transfer between availability zones, NAT gateway processing, load balancer capacity units, and support charges frequently cannot be traced to a workload from billing data alone. Name them, choose a split rule, and document it - a documented approximation is trusted, an unexplained line item is not.

**Publish the unallocated percentage.** It is the credibility metric for the whole exercise. If 30% of spend is unattributed, no team's figure means much, and the target is to drive it down rather than to hide it.

## Example

```text
Allocation layers, from most to least reliable.

  1. ACCOUNT              ~78% of spend, attributes itself
     one account per workload per environment; no tags required

  2. TAGS in shared accounts   ~14% of spend
     applied by the platform at provisioning, values constrained by tag policy,
     ACTIVATED as cost allocation tags (the step people miss)
       tenant, cost-centre, workload, environment, data-classification

  3. KUBERNETES usage      ~6% of spend
     shared clusters appear as EC2/Fargate; split by namespace using cluster
     usage data (OpenCost), node cost allocated by resource requests, with idle
     capacity handled explicitly - see below

  4. SPLIT CHARGE RULES    ~2% of spend
     genuinely shared platform infrastructure, distributed by rule

  UNALLOCATED              target < 2%
     the credibility metric for everything above
```

```json
// Cost category: makes "team-payments" mean the same thing in every report.
{
  "Name": "Team",
  "RuleVersion": "CostCategoryExpression.v1",
  "Rules": [
    {
      "Value": "team-payments",
      "Rule": {
        "Or": [
          { "Dimensions": { "Key": "LINKED_ACCOUNT", "Values": ["<checkout-prod>", "<checkout-staging>"] } },
          { "Tags": { "Key": "tenant", "Values": ["team-payments"] } }
        ]
      }
    },
    {
      "Value": "platform-shared",
      "Rule": { "Dimensions": { "Key": "LINKED_ACCOUNT", "Values": ["<network-prod>", "<shared-services>"] } }
    }
  ],
  "SplitChargeRules": [
    {
      "Source": "platform-shared",
      "Targets": ["team-payments", "team-search", "team-data", "team-web"],
      // PROPORTIONAL where a usage metric exists; EVEN where none does.
      // Either is defensible; an unallocated bucket is not.
      "Method": "PROPORTIONAL",
      "Parameters": [{ "Type": "ALLOCATION_PERCENTAGES", "Values": ["41", "22", "24", "13"] }]
    }
  ]
}
```

```text
The Kubernetes layer, and the dispute it always generates:

  cluster prod-eu-1, monthly node + control plane cost = C

  allocation by resource REQUESTS (the standard approach):
    team-payments   requests 38% of allocatable    -> 38% of C
    team-search     requests 24%                   -> 24% of C
    team-data       requests 19%                   -> 19% of C
    platform        requests  9%                   ->  9% of C
    UNREQUESTED (idle headroom)  10%               -> ??? <-- the argument

  Three defensible answers for the idle 10%, and you must pick one publicly:
    a) charge it to the platform  - platform owns capacity planning; simplest,
                                    and gives the platform an incentive to
                                    right-size. Usually the best choice.
    b) split it proportionally    - teams pay for headroom they benefit from
    c) split it evenly            - crude, but easy to explain

  Whichever you choose, document it. Teams accept a rule they understand and
  reject a number they cannot reproduce.

  $ platform cost report --month 2026-07

  TEAM             ACCOUNTS   TAGGED    K8S     SPLIT    TOTAL
  team-payments    $41,200    $2,100  $8,400   $1,180   $52,880
  team-search      $18,900    $1,400  $5,300   $  630   $26,230
  team-data        $22,400    $  900  $4,200   $  690   $28,190
  team-web         $ 9,100    $  600  $2,900   $  370   $12,970
  platform          $6,800    $    0  $2,000  -$2,870   $ 5,930
  ------------------------------------------------------------------
  UNALLOCATED                                            $ 1,240  (1.0%)
    inter-AZ data transfer $780 · LCU $310 · support $150
    -> named, and small enough that nobody disputes the rest
```

## Interview tips

- Lead with the account as the primary allocation boundary. It is the most reliable layer and it is a genuine argument for the multi-account model.
- The two-step tag point - applied on resources and activated for billing - is a specific detail that shows you have actually set this up.
- Enforcement over request: tag policies, service control policies denying untagged creation, and platform-applied tags. "We ask teams to tag" is the answer that does not work.
- Cost categories as the mapping to your organisation is the tool most candidates do not name, and it is what makes every report agree.
- On shared cost, take a position and defend it. Any consistent split rule beats a large unallocated bucket, and saying that is a maturity signal.
- The Kubernetes idle-capacity question is where this gets contested. Recommending that the platform absorbs idle cost, because it owns capacity planning and gains a right-sizing incentive, is a strong, defensible answer.
- Publishing the unallocated percentage as the credibility metric is the best close - it shows you know the exercise fails if the numbers are not trusted.

---

[⬅ Back to AWS Platform Engineering](./README.md) · [All topics](../README.md)
