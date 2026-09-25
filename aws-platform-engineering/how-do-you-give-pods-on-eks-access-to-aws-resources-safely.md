---
title: "How do you give pods on EKS access to AWS resources safely?"
id: 151
category: "AWS Platform Engineering"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - aws-platform-engineering
  - interview-questions
---

# How do you give pods on EKS access to AWS resources safely?

**Short answer:** Bind an IAM role to a specific Kubernetes service account, using either IRSA or EKS Pod Identity, so the Pod receives short-lived credentials with no stored key. Then make sure two things are true: the binding names an exact service account rather than a wildcard, and the node instance role carries almost nothing - because if it does, every Pod on the node inherits it regardless of your careful per-Pod work.

## Detail

**The node instance role is the mistake to check first.** Before IRSA existed, the common approach was granting permissions to the node's instance profile - which means every Pod scheduled on that node can use them via the instance metadata service. Many clusters still carry over-broad node roles, and any per-Pod identity work is undermined while that is true. The node role should hold only what the kubelet and the CNI need, and Pod access to the metadata endpoint should be blocked or restricted so workloads cannot reach it at all.

**IRSA: the OIDC federation approach.** The cluster has an OIDC issuer registered as an identity provider in IAM. The service account is annotated with a role ARN, the kubelet projects a signed token into the Pod, and the SDK exchanges it for temporary credentials. The security boundary lives entirely in the role's trust policy conditions - the exact `sub` naming namespace and service account, and the `aud`. A wildcard in either turns per-team isolation into one shared trust boundary, and it is the single most common serious misconfiguration here.

**EKS Pod Identity: the newer, simpler mechanism.** An association is created on the cluster mapping a namespace and service account to a role, and an agent supplies credentials. The differences that matter in practice:

| Aspect                   | IRSA                                 | Pod Identity                            |
| ------------------------ | ------------------------------------ | --------------------------------------- |
| Where the binding lives  | Role trust policy + SA annotation    | An association on the cluster           |
| Risk of a wildcard trust | Real - it is hand-written per role   | Much lower - no per-role trust policy   |
| Cross-account            | Requires role chaining               | Native: association names a target role |
| Reusing one role         | Trust policy grows with each cluster | Associations added, trust unchanged     |
| Cluster OIDC provider    | Required                             | Not required                            |

Two newer Pod Identity features strengthen the case. Since mid-2025 an association can name a **target role** in another account, and EKS performs the role chaining for you, so cross-account access no longer needs code or per-account OIDC providers. And Pod Identity attaches session tags - cluster name, namespace, service account - to the credentials, so one policy can use conditions such as `aws:PrincipalTag/kubernetes-namespace` for attribute-based access instead of a role per namespace. EKS Auto Mode clusters include the Pod Identity agent, so there is nothing to install.

For new clusters Pod Identity is the better default because it removes the class of mistake that hand-written trust policies invite. IRSA remains supported and widely deployed - and is still the mechanism for clusters outside EKS proper that expose their own OIDC issuer - so know both.

**One role per workload.** Not per team, not per namespace. Shared roles collapse your authorisation model and make an incident's blast radius unknowable. The platform should generate the role, its policy, the service account, and the binding from the service declaration - because at forty teams, hand-written trust policies guarantee some will be wrong.

**Scope the permission policy by resource, not just by action.** `s3:GetObject` on `*` is not least privilege. Bound it to a naming prefix the platform enforces at provisioning, or to a tag condition, so a workload cannot reach another tenant's buckets. The enforced naming convention is what makes resource-scoped policies possible.

**Audit continuously, because the findings come from drift.** Wildcard trust conditions, remaining long-lived access keys, service accounts shared across workloads, and over-broad node roles. In practice these are usually introduced while debugging and never reverted, rather than designed that way.

## Example

```json
// IRSA trust policy. The two conditions ARE the boundary. A wildcard in `sub`
// means ANY pod in the cluster can assume this role.
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
          "oidc.eks.eu-west-1.amazonaws.com/id/<cluster-id>:sub": "system:serviceaccount:team-payments:checkout",
          "oidc.eks.eu-west-1.amazonaws.com/id/<cluster-id>:aud": "sts.amazonaws.com"
        }
      }
    }
  ]
}
```

```bash
# Pod Identity: the association lives on the cluster, so there is no per-role
# trust policy to get wrong. This is why it is the better default for new clusters.
aws eks create-pod-identity-association \
  --cluster-name prod-eu-1 \
  --namespace team-payments \
  --service-account checkout \
  --role-arn arn:aws:iam::<account-id>:role/team-payments-checkout

# Cross-account: EKS assumes the local role, then chains to the target role
# in the data account. No SDK changes and no OIDC provider in that account.
aws eks create-pod-identity-association \
  --cluster-name prod-eu-1 \
  --namespace team-payments \
  --service-account ledger-reader \
  --role-arn arn:aws:iam::<account-id>:role/team-payments-ledger-reader \
  --target-role-arn arn:aws:iam::<data-account-id>:role/ledger-read-from-prod-eu-1
```

```json
// The permission policy - scoped by an enforced naming prefix and a tag
// condition, not by action alone.
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
      "Resource": "arn:aws:secretsmanager:eu-west-1:*:secret:team-payments/*"
    },
    {
      "Effect": "Allow",
      "Action": ["kms:Decrypt", "kms:GenerateDataKey"],
      "Resource": "*",
      "Condition": { "StringEquals": { "aws:ResourceTag/tenant": "team-payments" } }
    }
  ]
}
```

```text
The node role check - do this before anything else, because it can invalidate
all the per-pod work above.

  $ aws iam list-attached-role-policies --role-name eks-node-prod-eu-1

    AmazonEKSWorkerNodePolicy          ✓ required
    AmazonEC2ContainerRegistryReadOnly ✓ required (image pulls)
    AmazonEKS_CNI_Policy               ✓ required (or move to the CNI's own SA)
    AmazonS3FullAccess                 ✗ EVERY POD ON EVERY NODE HAS THIS.
                                         Added 2024 for a since-removed workload.
                                         Remove it.

  And block pod access to the metadata endpoint, so workloads cannot reach the
  node role even if it is over-broad:
    - IMDSv2 required, hop limit 1  (a pod is one hop away, so it cannot reach it)
    - or a NetworkPolicy denying egress to 169.254.169.254

  Audit findings, in the order they usually appear:
    ✗ wildcard `sub` in one trust policy  -> added while debugging, never narrowed
    ✗ node role with S3FullAccess          -> legacy from a removed workload
    ⚠ 4 deployments sharing team-search:default -> split, one role per workload
    ✓ no long-lived access keys in any namespace secret
```

## Interview tips

- Check the node instance role first and say why: an over-broad node role means every Pod on that node inherits it, which undoes all per-Pod identity work. Most candidates skip straight to IRSA.
- Blocking Pod access to the instance metadata endpoint - IMDSv2 with hop limit 1, or a network policy - is the defence-in-depth detail that shows real hardening experience.
- The wildcard trust-policy subject is the specific serious misconfiguration to name, along with the `aud` condition that most people forget.
- Know both IRSA and Pod Identity, and take a position: Pod Identity for new clusters because it removes the hand-written trust policy that invites the mistake. Mentioning its native cross-account target roles and session tags shows your knowledge is current.
- One role per workload, generated by the platform. At scale, hand-written trust policies guarantee some are wrong.
- Resource-scoped policies via an enforced naming prefix or tag condition, not action-scoped policies on `*`.
- Note that audit findings are usually debugging drift rather than bad design - it is the realistic failure mode and explains why the audit must be scheduled.

---

[⬅ Back to AWS Platform Engineering](./README.md) · [All topics](../README.md)
