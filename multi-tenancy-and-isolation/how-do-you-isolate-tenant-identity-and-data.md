---
title: "How do you isolate tenant identity and data?"
id: 28
category: "Multi-Tenancy and Isolation"
difficulty: "Advanced"
tags:
  - platform-engineering
  - multi-tenancy-and-isolation
  - interview-questions
---

# How do you isolate tenant identity and data?

**Short answer:** Give every tenant its own workload identity, scope that identity to only its own resources through the cloud provider's authorisation model, and make sure no shared credential exists that could cross the boundary. The isolation is only as strong as its weakest path - and in practice the weakest path is almost always a shared service account, an over-broad IAM role, or a secret store where one tenant can read another's paths.

## Detail

**Identity is the boundary that matters most.** Network policy stops a workload reaching something; identity determines what it is allowed to do when it gets there. A tenant with credentials scoped to their own resources is contained even if the network is flat, whereas a tenant with a shared administrative role is uncontained no matter how good the network policy is.

**Per-tenant workload identity, federated rather than stored.** Each tenant's workloads get their own service account, federated to a cloud identity with a trust policy naming that specific service account. No long-lived keys, and the trust policy conditions must be tight - a trust policy that accepts any service account in the cluster is a common and serious mistake, because it lets any tenant assume any role.

**Scope authorisation by resource, not just by action.** An IAM policy granting `s3:GetObject` on `*` is not tenant isolation. The policy must be bounded to the tenant's own resources, and the reliable way to achieve that is a naming and tagging convention the platform enforces at provisioning time, so policies can be written against a prefix or a tag condition and cannot accidentally widen.

**Secret store paths need the same discipline.** A tenant should be able to read `secret/team-payments/*` and nothing else. Flat secret namespaces with a shared read role are a frequent finding - and because secrets are exactly the material that lets you cross other boundaries, this is the highest-consequence version of the mistake.

**The three data isolation models,** and the trade-off is between blast radius and operational cost:

| Model                           | Isolation                          | Cost and operations                                |
| ------------------------------- | ---------------------------------- | -------------------------------------------------- |
| Shared store, row-level         | Weakest - one query bug leaks data | Cheapest; one thing to operate                     |
| Shared store, schema per tenant | Moderate - separate grants         | Cheap; migrations multiply                         |
| Store per tenant                | Strongest                          | Most expensive; N backups, N upgrades, N failovers |

For internal platform tenants, a store per tenant is usually right because the tenants are teams and you are provisioning per service anyway. Row-level isolation is a product concern for customer-facing multi-tenant applications, and if you use it, the enforcement must be at a layer the application cannot forget - database row-level security rather than a `WHERE` clause in every query.

**Encryption keys can carry the boundary.** A per-tenant key means access to the ciphertext without the key is useless, which is a meaningful additional control for regulated tenants and gives you crypto-shredding as a deletion mechanism. It costs key management complexity, so it is a tier decision rather than a default.

**Audit per tenant, and make it queryable.** Every cross-boundary access attempt should be attributable. "Which identities read this tenant's data last month" is a question you will be asked - by an auditor, or during an incident - and it needs to be answerable from logs rather than reconstructed.

**Verify rather than assume.** The valuable exercise is periodically attempting cross-tenant access with a tenant's own credentials and confirming it fails. Policies drift, trust conditions get loosened during debugging, and nobody notices until it matters.

## Example

```json
// AWS trust policy for a tenant's role. The two conditions are the whole
// control: without both, any pod in the cluster could assume this role.
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Federated": "arn:aws:iam::<account-id>:oidc-provider/<oidc-issuer>" },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          // Exact service account, not a wildcard. A wildcard here is the
          // single most common cross-tenant escalation path.
          "<oidc-issuer>:sub": "system:serviceaccount:team-payments:checkout",
          "<oidc-issuer>:aud": "sts.amazonaws.com"
        }
      }
    }
  ]
}
```

```json
// Permission policy, scoped by an enforced naming prefix and a tag condition.
// Both are applied by the platform at provisioning time, so a tenant cannot
// create a resource outside its own prefix.
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:::example-team-payments-*/*"
    },
    {
      "Effect": "Allow",
      "Action": ["secretsmanager:GetSecretValue"],
      "Resource": "arn:aws:secretsmanager:*:*:secret:team-payments/*"
    },
    {
      "Effect": "Allow",
      "Action": ["kms:Decrypt", "kms:GenerateDataKey"],
      "Resource": "*",
      "Condition": {
        "StringEquals": { "aws:ResourceTag/tenant": "team-payments" }
      }
    }
  ]
}
```

```text
The verification that keeps it honest - run on a schedule, not once at design time:

  $ platform tenancy verify --tenant team-payments

    identity
      ✓ service accounts have no static credentials
      ✓ trust policy pins exact service account (no wildcard sub)
      ✓ no tenant workload can assume another tenant's role
    authorisation
      ✓ s3 access bounded to example-team-payments-*
      ✓ secret paths bounded to team-payments/*
      ✗ FINDING: role team-payments-checkout has kms:Decrypt on * with no tag
                 condition (added 2026-02-14 during an incident, never reverted)
    data
      ✓ dedicated Postgres instance; no shared credential
      ✓ per-tenant CMK; crypto-shred available for deletion
    audit
      ✓ all data access attributable to a tenant identity

  1 finding. Note its origin: a debugging change that was never reverted. That
  is how isolation actually erodes - not by bad design, but by drift.
```

## Interview tips

- Lead with identity as the primary boundary and explain why: it contains a tenant even when the network does not.
- The wildcard trust-policy condition is the specific mistake to name. It is common, serious, and naming it demonstrates you have reviewed real IAM.
- "Scope by resource, not just by action" plus the enforced naming and tagging convention that makes it possible is the mechanism interviewers want to hear.
- Secret store path scoping deserves explicit mention - secrets are the material that lets an attacker cross every other boundary.
- Say that you would verify by attempting cross-tenant access on a schedule, and that findings usually originate in debugging changes that were never reverted. That is the realistic failure mode.

---

[⬅ Back to Multi-Tenancy and Isolation](./README.md) · [All topics](../README.md)
