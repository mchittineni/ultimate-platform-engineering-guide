---
title: "How do you choose a datastore for a platform service?"
id: 22
category: "Platform Architecture"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-architecture
  - interview-questions
---

# How do you choose a datastore for a platform service?

**Short answer:** Start from the access patterns and the consistency requirement, not from the technology. For the overwhelming majority of platform services the correct answer is managed PostgreSQL, and the interesting part of the answer is being able to say precisely what would change your mind - very high write throughput, genuinely global low-latency writes, a time-series or append-only shape, or data you can afford to lose. A platform team should also expose only two or three vetted options to its own users, for the same reason.

## Detail

**The questions that actually decide it:**

- **What are the read and write patterns?** Point lookups by key, range scans, ad-hoc joins, aggregation over history? Joins and ad-hoc querying push hard toward relational; pure key access opens up other options.
- **What consistency do you need?** Can two components read different values a second apart without causing a bug? Control-plane state usually cannot - a reconciler reading stale state may create a duplicate resource.
- **What is the write volume, honestly?** Most platform services handle tens to hundreds of writes per second. That is comfortably within a single PostgreSQL instance and nowhere near the point where a distributed store is justified.
- **How bad is data loss?** Losing the record of provisioned resources is worse than losing the resources themselves, because you can no longer reconcile. That requirement dominates the choice for control-plane data.
- **What does the team already run well?** A datastore your team cannot operate confidently at 3am is the wrong choice regardless of its fit on paper.

**The default and its justification.** Managed PostgreSQL gives ACID transactions, strong consistency, joins, JSON columns when you need schema flexibility, mature tooling, and operational familiarity almost everywhere. It scales vertically far further than most people assume, and read replicas handle read-heavy growth. "Start with Postgres and know your exit criteria" is a defensible senior answer, not a lazy one.

**When something else is genuinely right:**

| Requirement                               | Reasonable choice          | What you give up                |
| ----------------------------------------- | -------------------------- | ------------------------------- |
| Very high write throughput, key access    | Cassandra / ScyllaDB       | Joins, strong consistency       |
| Global writes with low local latency      | Spanner / CockroachDB      | Cost, operational familiarity   |
| Serverless, spiky, AWS-native, key access | DynamoDB                   | Query flexibility - model first |
| Time-series metrics at volume             | Prometheus / TimescaleDB   | General-purpose querying        |
| Cache, sessions, ephemeral coordination   | Redis / Valkey             | Durability - treat as lossy     |
| Full-text and aggregation search          | OpenSearch / Elasticsearch | Source-of-truth reliability     |

**The platform-specific wrinkle: your control plane may already have a datastore.** If you build on Kubernetes, custom resources are stored in etcd and you inherit consistency, watch semantics, and RBAC for free. That is genuinely the right answer for platform desired state - but etcd is not a general database. Do not put audit history, cost records, or high-churn operational data in custom resources; etcd is small, sensitive to object size and write rate, and its performance affects the entire cluster.

**A common and effective split:** desired state in custom resources, and observed history - audit trails, cost snapshots, deployment records, scorecard results - in PostgreSQL alongside. Different requirements, different stores, and neither compromised.

**The platform team's other obligation.** You are also choosing on behalf of your users. Offering every datastore means supporting every datastore. Two or three vetted options with good defaults, plus a documented process for justifying a fourth, is the pattern that keeps the operational surface finite.

## Example

```text
Deciding for three real platform services - same estate, three answers.

1. Platform desired state (Service, PostgresInstance claims)
   pattern: read by name, watch for changes, ~50 writes/min
   consistency: strong - a reconciler acting on stale state duplicates resources
   loss tolerance: none - losing this orphans real infrastructure
   -> Kubernetes custom resources (etcd). Free watch semantics, RBAC, admission.
      Guard: keep objects small; nothing high-churn in status fields.

2. Deployment and audit history (who changed what, flag flips, policy exemptions)
   pattern: append-heavy, queried by time range, service, and actor; joins to
            the catalogue; retained 2 years for auditors
   consistency: eventual is fine - it is a record, not a decision input
   loss tolerance: low, but reconstructible from other logs
   -> Managed PostgreSQL, partitioned by month. Explicitly NOT custom resources:
      ~40k rows/day would destabilise etcd.

3. Rendered manifest cache (the reconciler's last-known-good render)
   pattern: read by content hash, high read rate, cheap to recompute
   consistency: irrelevant
   loss tolerance: total - a cold cache just means slower reconciliation
   -> Redis. Nothing durable stored; recomputation is the recovery path.

The lesson: one platform, three stores, each justified by a different requirement.
Using etcd for all three would take down the cluster; using PostgreSQL for all
three would throw away watch semantics you get for free.
```

```text
What is offered to platform users - deliberately narrow:

  postgres    default for anything relational or unclear
  redis       cache and ephemeral coordination; documented as lossy
  s3-bucket   objects, with lifecycle and encryption defaults applied

  Anything else: an ADR explaining the access pattern that the three above
  cannot serve, plus who will operate it. Two teams have done this; both were
  justified (one search index, one time-series store).
```

## Interview tips

- Lead with access patterns and consistency, not with a technology. Candidates who open with a favourite database are answering a different question.
- "PostgreSQL by default, and here is exactly what would change my mind" is a strong, senior-sounding position - the exit criteria are what make it credible rather than lazy.
- The etcd caveat is the platform-specific insight: custom resources are correct for desired state and wrong for high-churn history. This is a real failure mode and naming it is high signal.
- The desired-state-versus-observed-history split is a clean, memorable design and worth volunteering.
- Mention that you are also choosing for your users, and that a narrow menu bounds the operational surface. It shows you think about the platform's support load, not just this one service.

---

[⬅ Back to Platform Architecture](./README.md) · [All topics](../README.md)
