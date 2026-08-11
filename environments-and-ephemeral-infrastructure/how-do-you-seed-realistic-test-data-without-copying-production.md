---
title: "How do you seed realistic test data without copying production?"
id: 62
category: "Environments and Ephemeral Infrastructure"
difficulty: "Advanced"
tags:
  - platform-engineering
  - environments-and-ephemeral-infrastructure
  - interview-questions
---

# How do you seed realistic test data without copying production?

**Short answer:** Generate data that preserves the properties that matter - volume, distribution, referential integrity, and the awkward edge cases - rather than copying real records and hoping anonymisation is sufficient. Where you must derive from production, transform inside the production boundary before anything is exported, and treat re-identification risk as the real constraint, because anonymisation is much harder than it looks.

## Detail

**Why copying production is the tempting wrong answer.** It gives realistic data instantly. It also copies personal data into environments with weaker access controls, a wider audience, and no deletion guarantees - which is a compliance problem under most privacy regimes, and a breach if any of those environments is exposed. Preview environments in particular are numerous, short-lived, and not somewhere you want customer records.

**Anonymisation is genuinely hard, and this is the part to demonstrate you understand.** Removing names and email addresses leaves quasi-identifiers - postcode, date of birth, transaction timestamps, an unusual purchase pattern - that re-identify individuals when combined. Format-preserving replacement of obvious fields is not the same as anonymisation. If you go this route, the honest framing is pseudonymisation, which in most regimes is still personal data and still in scope.

**Synthetic generation is the better default.** Generate from a schema-aware model that produces referentially consistent data at the right volume and distribution. It has no privacy exposure, can be committed and versioned, can be deliberately extended with edge cases, and can be regenerated at any size.

**What "realistic" actually needs to mean:**

| Property              | Why it matters                                                |
| --------------------- | ------------------------------------------------------------- |
| Volume                | Queries that are fast on 100 rows are not on 10 million       |
| Distribution          | Real data is skewed - a few enormous accounts, many tiny ones |
| Referential integrity | Broken foreign keys produce failures unrelated to the change  |
| Cardinality           | Index and query-plan behaviour depends on it                  |
| Edge cases            | Unicode names, empty collections, expired records, refunds    |
| Temporal spread       | Data across time, not all created at once                     |

The skew row is the one most synthetic generators miss. Uniformly distributed data hides exactly the performance problems production will show you, because the pathological case is always the account with a hundred thousand orders.

**If you must derive from production, transform before export.** The transformation runs inside the production boundary, the output is what leaves, and raw data never lands anywhere else. Subset as well as mask - a coherent 1% slice that preserves referential integrity is far safer and far faster to restore than a masked full copy.

**Preserve the awkward cases deliberately.** Every team has a set of records that break things: the customer with an apostrophe in their name, the order with a partial refund and a currency change, the account with no billing address. Curate those as fixtures in the seed so they are always present. This is often more valuable than volume.

**Make it a platform capability with versions.** A named, versioned seed - refreshed on a schedule, published as a restorable snapshot - so every environment starts from a known state and a test failure is attributable. Ad hoc seeding scripts per team produce environments nobody can compare.

**Access-control the seed anyway.** Even synthetic data can leak business information - your product catalogue, pricing structure, or customer count. Treat it as internal, not public.

## Example

```text
Three approaches, honestly compared.

COPY PRODUCTION
  realism      perfect
  privacy      unacceptable - personal data in weakly controlled environments
  speed        slow to restore at full size
  verdict      no. And "we anonymise it" usually means pseudonymise, which in
               most privacy regimes is still personal data.

MASK + SUBSET FROM PRODUCTION (transform inside the boundary)
  realism      high - real distributions and real edge cases
  privacy      residual re-identification risk from quasi-identifiers
  speed        good if subsetted to a coherent 1% slice
  verdict      acceptable for a small number of controlled environments with a
               documented risk assessment. Not for 30 preview environments.

SYNTHETIC GENERATION (schema-aware, distribution-matched)
  realism      good if you deliberately model skew, cardinality, and edge cases
  privacy      none to manage
  speed        fast; regenerate at any size; commit and version it
  verdict      the default, and the only sane option for ephemeral environments.
```

```yaml
# A versioned seed as a platform artefact. Distribution is modelled explicitly -
# uniform data is what hides your real performance problems.
apiVersion: platform.example.com/v1
kind: DataSeed
metadata: { name: checkout-seed, namespace: platform }
spec:
  version: v14
  strategy: synthetic
  refresh: "0 2 * * *" # nightly regeneration, published as a snapshot
  schema:
    source: migrations # generated from the real schema, so it cannot drift
    repo: example/checkout
  volume:
    accounts: 50000
    orders: 4000000
  distribution:
    # Deliberate skew - the pathological account is the one that finds the bug
    orders_per_account:
      type: pareto
      shape: 1.4
      max: 120000 # one account with 120k orders exists on purpose
    order_value: { type: lognormal, median: 42.00, currency_mix: [EUR, GBP, USD] }
    created_at: { spread: 36months } # temporal spread, not all one timestamp
  fixtures:
    # Curated awkward cases, always present. Often worth more than the volume.
    - name: unicode-name
      note: "O'Brien-Müller, 名前 - has broken CSV export and search twice"
    - name: partial-refund-currency-change
      note: "order refunded partly after a currency switch - RB-91"
    - name: account-no-billing-address
    - name: expired-payment-method-with-active-subscription
    - name: order-with-zero-value-line
  output:
    snapshot: s3://platform-seeds/checkout/v14.dump # restore, do not migrate
    access: internal # synthetic still leaks catalogue and pricing structure
```

```text
Why the skew matters - the same query, two seeds:

  SELECT * FROM orders WHERE account_id = ? ORDER BY created_at DESC LIMIT 50;

  uniform seed (100 orders per account, evenly)
    p99 3ms.  Ships. Looks fine everywhere.

  pareto seed (median 12 orders, max 120,000)
    p99 3ms for typical accounts
    1,900ms for the largest account - missing composite index on
    (account_id, created_at)

  Production has accounts like that. The uniform seed cannot find this class of
  bug, which is why distribution is a first-class property of the seed rather
  than an afterthought.
```

## Interview tips

- Lead with the reframing: generate data with the right properties rather than copying records and hoping masking is enough.
- Demonstrating that you understand quasi-identifiers and re-identification - and that masking usually yields pseudonymisation, which is still personal data - is the strongest signal in this answer.
- Distribution and skew is the technical insight. The query that is fast for typical accounts and terrible for the largest one is a concrete, memorable example.
- "Transform inside the production boundary" is the right rule if derivation is unavoidable, along with subsetting to a coherent slice rather than masking a full copy.
- Curated awkward-case fixtures are cheap and disproportionately valuable; volunteering a couple of real-sounding examples lands well.
- Versioning the seed so failures are attributable, and access-controlling it because synthetic data still leaks business information, are the two details that show maturity.

---

[⬅ Back to Environments and Ephemeral Infrastructure](./README.md) · [All topics](../README.md)
