---
title: "How does a platform provide workload identity without long-lived credentials?"
id: 127
category: "Platform Security"
difficulty: "Advanced"
tags:
  - platform-engineering
  - platform-security
  - interview-questions
---

# How does a platform provide workload identity without long-lived credentials?

**Short answer:** The workload proves who it is with a short-lived, cryptographically signed token issued by its runtime environment, and exchanges that token for short-lived credentials from the target system. On Kubernetes the projected service account token is the assertion, the cluster's OIDC issuer is the trust anchor, and the cloud provider's federation exchanges it for temporary credentials. No secret is ever stored, and the identity cannot be copied off the host and reused.

## Detail

**What replaces the stored key.** The kubelet projects a signed JSON Web Token into the Pod, scoped to a specific audience and with a short lifetime, and rotates it automatically. The cloud provider is configured to trust the cluster's OIDC issuer, and its federation endpoint validates the token's signature, issuer, audience, and subject before issuing temporary credentials. The chain of trust runs from the cluster's signing key to the cloud's trust policy - no shared secret anywhere in it.

**The trust policy conditions are the entire security boundary,** and this is where real deployments go wrong. The policy must pin the exact subject - the specific namespace and service account - and the exact audience. A trust policy that accepts any subject from the cluster's issuer means any Pod in the cluster can assume that role, which turns per-team isolation into a single shared trust boundary. This is the most common serious misconfiguration in this area, and reviewing for it is worth more than most other controls.

**Audience matters as much as subject.** A token minted for one audience should not be accepted by another. Omitting the audience condition allows token reuse across systems that trust the same issuer.

**The per-cloud mechanisms, which are the same idea:**

| Cloud | Mechanism                    | Binding                               |
| ----- | ---------------------------- | ------------------------------------- |
| AWS   | EKS Pod Identity, or IRSA    | Service account → IAM role            |
| Azure | Entra Workload ID            | Service account → managed identity    |
| GCP   | Workload Identity Federation | Service account → IAM service account |

EKS Pod Identity is now the default recommendation for new EKS workloads, with IRSA still supported and still common in existing estates (and needed outside EKS). The association is configured through the EKS API rather than as an annotation plus a per-cluster OIDC trust policy per role, and the role trusts the `pods.eks.amazonaws.com` service principal - which removes a class of trust-policy mistakes and simplifies reusing a role across clusters. The subject-pinning discipline below still applies to IRSA and to every other OIDC federation.

**Extend the same model beyond the cloud.** Databases can accept IAM authentication or short-lived certificates instead of passwords. Internal service-to-service calls can use mTLS with certificates issued to the workload identity - SPIFFE and SPIFFE Verifiable Identity Documents are the vendor-neutral standard here, and a service mesh usually implements it. Third-party services increasingly support OIDC federation directly. The goal is that the workload's identity, not a secret it holds, is what grants access everywhere.

**One identity per workload, never one per cluster or team.** The service account should be specific to the service, so its permissions can be minimal and an incident has a precise blast radius. A shared service account across a namespace collapses your authorisation model.

**The platform should make this the default and invisible.** A team declaring a service and its dependencies should get a service account, a federated cloud identity, and a scoped policy generated automatically. If teams are writing trust policies by hand, some of them will get the conditions wrong.

**Verify continuously.** Scan for trust policies with wildcard subjects, for any remaining long-lived access keys, and for service accounts shared across services. These findings usually originate in debugging changes that were never reverted rather than in bad initial design.

## Example

```json
// AWS trust policy. The two StringEquals conditions ARE the security boundary.
// Replace either with a wildcard and any pod in the cluster can assume this role.
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<account-id>:oidc-provider/oidc.eks.eu-west-1.amazonaws.com/id/<cluster-id>"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          // EXACT service account - one identity per workload
          "oidc.eks.eu-west-1.amazonaws.com/id/<cluster-id>:sub": "system:serviceaccount:team-payments:checkout",
          // Audience - stops a token minted for one system being replayed at another
          "oidc.eks.eu-west-1.amazonaws.com/id/<cluster-id>:aud": "sts.amazonaws.com"
        }
      }
    }
  ]
}
```

```yaml
# What the platform generates from the service declaration. The developer wrote
# `owner` and a dependency; they never see a trust policy.
apiVersion: v1
kind: ServiceAccount
metadata:
  name: checkout # one per workload, not per team
  namespace: team-payments
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::<account-id>:role/team-payments-checkout
---
apiVersion: apps/v1
kind: Deployment
metadata: { name: checkout, namespace: team-payments }
spec:
  template:
    spec:
      serviceAccountName: checkout
      containers:
        - name: checkout
          image: ghcr.io/example/checkout@sha256:9f2c8b1d...
          # No AWS_ACCESS_KEY_ID anywhere. EKS's pod identity webhook injects a
          # projected service account token (audience sts.amazonaws.com, short-
          # lived, rotated by the kubelet) plus AWS_ROLE_ARN and
          # AWS_WEB_IDENTITY_TOKEN_FILE. The SDK exchanges the token for
          # temporary credentials and refreshes them itself.
```

```text
Continuous verification - and note where the findings come from:

  $ platform identity audit

  ✗ CRITICAL  role team-data-etl trust policy uses a wildcard subject
                "...:sub": "system:serviceaccount:*:*"
              -> ANY pod in the cluster can assume this role. It has S3 write
                 access to the data lake.
              -> introduced 2026-04-02 while debugging a token audience mismatch;
                 never narrowed afterwards.

  ✗ HIGH      long-lived access key still exists for user svc-legacy-uploader
              last used 2026-01-14 (209 days ago)
              -> delete; the workload it served now uses IRSA.

  ⚠ MEDIUM    service account team-search:default used by 4 deployments
              -> one identity per workload; split so blast radius is per service.

  ✓           no static cloud credentials found in any namespace secret
  ✓           all 218 service accounts have projected tokens with an audience set

  Two of the three findings are drift from debugging, not design errors. That is
  the realistic failure mode, and it is why the audit is scheduled rather than
  one-off.
```

## Interview tips

- Describe the exchange precisely: a signed, short-lived, audience-scoped token from the runtime, exchanged at a federation endpoint for temporary credentials. Naming the chain of trust from the cluster signing key to the cloud trust policy is what demonstrates understanding.
- The wildcard trust-policy subject is the single highest-value point. Say what it breaks - any Pod in the cluster can assume the role - and that it is usually debugging drift rather than bad design.
- Mention the audience condition too. Most candidates remember the subject and forget that audience prevents cross-system token replay.
- Know the three cloud mechanisms by name, and mention EKS Pod Identity as the current default for new EKS workloads that removes a class of trust-policy mistakes - while being able to explain IRSA, which most existing estates still run.
- Extend the model beyond the cloud - database IAM authentication, mTLS with SPIFFE identities - to show you see it as an identity strategy rather than one integration.
- One identity per workload, and the platform generating it, are the two operational rules. Hand-written trust policies at scale guarantee some will be wrong.

---

[⬅ Back to Platform Security](./README.md) · [All topics](../README.md)
