---
title: "What is the FOCUS specification and why does it matter?"
id: 231
category: "Platform FinOps"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-finops
  - interview-questions
---

# What is the FOCUS specification and why does it matter?

**Short answer:** FOCUS - the FinOps Open Cost and Usage Specification - is an open standard, run by the FinOps Foundation under the Linux Foundation, that defines one schema for billing data: the same column names, meanings, and rules whichever provider produced the bill. AWS, Azure, Google Cloud, Oracle, and a growing list of SaaS and AI providers now export it natively. It matters to a platform team because the most expensive part of cost tooling has always been normalising each provider's export, and FOCUS turns that from bespoke engineering into a query against a known schema.

## Detail

**The problem it solves.** Each provider's native billing export has its own shape. AWS's Cost and Usage Report, Azure's cost details export, and Google Cloud's BigQuery billing export disagree on column names, on what "cost" means (list, discounted, amortised), on how commitments and credits appear, and on how a refund or a tax line is represented. A multi-cloud organisation - or one with significant SaaS spend - ends up maintaining a translation layer per source, and every report is only as right as that layer. Two teams building the same dashboard from different exports get different totals.

**What the specification actually defines.** A set of datasets with named columns, each with a data type, allowed values, and normative requirements (MUST, SHOULD) on the data generator. The core Cost and Usage dataset includes columns such as:

| Column group  | Examples                                                              | Why it matters                                              |
| ------------- | --------------------------------------------------------------------- | ----------------------------------------------------------- |
| Cost measures | `BilledCost`, `EffectiveCost`, `ListCost`, `ContractedCost`           | Separates what was invoiced from amortised, discounted cost |
| Time          | `ChargePeriodStart`, `BillingPeriodStart`                             | Consistent period semantics across providers                |
| Who and what  | `ServiceProviderName`, `ServiceCategory`, `ServiceName`, `ResourceId` | Comparable service taxonomy                                 |
| Account scope | `BillingAccountId`, `SubAccountId`, `SubAccountName`                  | Maps to accounts, subscriptions, projects                   |
| Charge type   | `ChargeCategory`, `ChargeClass`, `CommitmentDiscountId`               | Usage vs purchase vs tax vs credit; corrections flagged     |
| Metadata      | `Tags`, `PricingCurrency`, `ConsumedQuantity`, `PricingUnit`          | Allocation and unit economics                               |

`EffectiveCost` is the column most platform reports should use: it is the cost after discounts with commitment purchases amortised across the usage they covered, so a team's number does not spike in the month someone bought a reservation. Provider-specific extras are allowed as custom columns with an `x_` prefix, so nothing is lost.

**How it has evolved.** FOCUS 1.0 was released in June 2024 and focused on cloud infrastructure billing. 1.2 (May 2025) added the columns that make SaaS and PaaS billing fit - `InvoiceId` for reconciliation and `PricingCurrency` columns so that virtual currencies such as credits and tokens sit alongside national currencies. 1.3 (December 2025) added a supplemental Contract Commitment dataset, allocation columns so a provider can say how it split a shared resource's cost, and data recency and completeness metadata. 1.4, ratified in June 2026, added Invoice Detail and Billing Period datasets and expanded commitment and eligibility data, with no breaking changes. AI model and token-level detail is on the roadmap for a later release rather than in 1.4. The trajectory is the point: FOCUS is becoming the common language for all technology spend, not just cloud, which matches the FinOps Framework's widening scope to SaaS, licensing, and AI.

**Why it matters specifically to a platform team.**

- **The cost data pipeline gets simpler.** Instead of an ingestion and translation job per provider, the platform lands each provider's FOCUS export in the warehouse and unions them. The allocation, showback, and unit-economics logic is written once against one schema.
- **Portability of tooling.** Commercial and open-source FinOps tools increasingly consume FOCUS directly, so the choice of tool is less of a lock-in decision.
- **Shared vocabulary with finance.** "Effective cost" and "billed cost" have defined meanings, which removes a whole class of arguments about why the platform's number differs from the invoice.
- **SaaS and AI spend in the same view.** Observability vendors, data platforms, and model APIs publishing FOCUS means the platform's showback can include the SaaS lines teams actually drive, not only compute.

**The limitations to be honest about.**

- **It standardises the shape, not the content.** Tags are still whatever your teams applied. If tagging is poor, FOCUS gives you consistently formatted unallocated cost.
- **Conformance varies.** Providers adopt versions at different speeds and some columns are conditional. Check each provider's conformance, pin the version you consume, and test for nulls in the columns you rely on.
- **It does not allocate shared cost for you.** Kubernetes clusters, shared networking, and platform overhead still need your allocation rules; FOCUS gives you a clean input to apply them to.
- **Native exports sit alongside the old ones.** Some provider-specific detail is richer in the native export, so you may keep both for a while.

## Example

```sql
-- One query across every provider that exports FOCUS: monthly effective cost
-- per team, using the same columns for AWS, Azure, GCP, and SaaS sources.
SELECT
  DATE_TRUNC('month', ChargePeriodStart)        AS month,
  ServiceProviderName                           AS provider,
  COALESCE(Tags['team'], 'unallocated')         AS team,
  ServiceCategory,
  SUM(EffectiveCost)                            AS effective_cost,
  SUM(BilledCost)                               AS billed_cost
FROM focus_cost_and_usage          -- a view unioning each provider's FOCUS export
WHERE ChargePeriodStart >= DATE '2026-06-01'
  AND ChargeCategory IN ('Usage', 'Purchase')
GROUP BY 1, 2, 3, 4
ORDER BY effective_cost DESC;
```

```text
What changed in the platform's cost pipeline after moving to FOCUS exports:

  BEFORE                                      AFTER
  3 ingestion jobs, 3 schemas                 3 exports landed, 1 schema, 1 view
  bespoke amortisation logic per provider     EffectiveCost from the provider
  observability vendor bill: a spreadsheet    vendor FOCUS export in the same view
  "why doesn't this match the invoice?"       BilledCost reconciles to InvoiceId
  allocation rules implemented 3 times        implemented once, against Tags and
                                              SubAccountId

  Still the platform's job: tag enforcement, Kubernetes allocation, shared-cost
  rules, and publishing the unallocated percentage.
```

## Interview tips

- Define it precisely: an open schema for billing data from the FinOps Foundation, exported natively by the major clouds and a growing number of SaaS providers.
- Explain `EffectiveCost` versus `BilledCost`. It is the most practical detail and shows you have queried the data.
- Know the rough version history - 1.0 in 2024, SaaS and virtual-currency support in 1.2, commitments and allocation in 1.3, invoice reconciliation in 1.4 - but lead with the problem it solves, not version trivia.
- Say what it does not do: it standardises the format, not the quality of your tags or your shared-cost rules. See [What is cost allocation tagging and why does it fail?](./what-is-cost-allocation-tagging-and-why-does-it-fail.md).
- Name the user: the platform team builds one pipeline, and every product team's showback and unit-economics numbers come out of it. See [How do you build unit economics for a platform?](./how-do-you-build-unit-economics-for-a-platform.md).
- A likely follow-up is multi-cloud; FOCUS is the answer to "how do you compare spend across providers without writing a translation layer?"

---

[⬅ Back to Platform FinOps](./README.md) · [All topics](../README.md)
