---
title: "How do you structure a multi-account AWS platform?"
id: 155
category: "AWS Platform Engineering"
difficulty: "Advanced"
tags:
  - platform-engineering
  - aws-platform-engineering
  - interview-questions
---

# How do you structure a multi-account AWS platform?

**Short answer:** Use AWS Organizations with organisational units that reflect the boundaries you need to enforce, and treat the account as the primary isolation boundary - because on AWS it is the only boundary that gives you hard limits on quotas, blast radius, and IAM reach simultaneously. A workable default is one account per workload per environment, grouped into organisational units by environment and sensitivity, with service control policies applied at the organisational unit rather than per account.

## Detail

**Why the account is the boundary that matters on AWS.** Service quotas are per account, so a runaway workload cannot exhaust another account's limits. IAM policies cannot reach across accounts without an explicit trust relationship. Billing is naturally separated. And an account can be closed, which is a genuinely clean offboarding primitive. IAM-based separation within one account can approximate this and always leaks - a forgotten wildcard, a resource-based policy, a shared quota.

**Organisational units exist to attach policy, so shape them around policy differences,** not around your reporting structure. If production and non-production need different guardrails, that is an organisational unit boundary. If regulated workloads need additional controls, that is another. Organisational units mirroring the company org chart need re-shaping every reorganisation and rarely correspond to any control you actually apply.

**A conventional and defensible layout:**

| Organisational unit | Contains                                     | Distinct policy                                        |
| ------------------- | -------------------------------------------- | ------------------------------------------------------ |
| Security            | Log archive, audit, security tooling         | Most restrictive; no workloads                         |
| Infrastructure      | Shared networking, shared services, registry | Platform team only                                     |
| Workloads/Prod      | One account per workload                     | Region restrictions, no root use, deletion protections |
| Workloads/NonProd   | Dev and staging accounts                     | Looser, plus budget and expiry enforcement             |
| Sandbox             | Individual experimentation accounts          | Hard spend limits, auto-expiry, no production data     |
| Suspended           | Accounts being decommissioned                | Deny nearly everything                                 |

**Service control policies are guardrails, not permissions.** They set the maximum available permissions in an account and cannot grant anything. The high-value ones are: deny use of the root user, deny disabling of CloudTrail, GuardDuty, or Config, deny regions you do not operate in, deny deletion of specific protected resources, and require encryption. Keep them few and coarse - service control policies are hard to debug, because the resulting failure is an access denial with little explanation, and a badly scoped one can break a whole organisational unit.

**Pair them with the newer organisation-level controls.** Resource control policies (RCPs) are the resource-side counterpart to SCPs: attached to the same tree, they cap what any principal - including one from outside the organisation - can do to your S3 buckets, KMS keys, roles, queues, and a growing list of other services, which makes them the natural way to enforce a data perimeter centrally. Declarative policies pin service configuration, such as blocking public AMI and snapshot sharing or requiring IMDSv2, in a way that holds even as new APIs appear. And centralised root access management lets you remove root credentials from member accounts entirely, performing the rare root-only task from the management or a delegated account instead - a stronger position than an SCP denying root use.

**Centralise the things that only make sense once.** Logging to a dedicated archive account with restricted access, identity through your provider federated centrally so nobody has IAM users, networking via a transit gateway or shared VPC subnets from the infrastructure account, and image and artefact registries shared. Duplicating these per account produces drift and cost.

**Networking is where multi-account gets expensive.** Address planning must be done up front - overlapping CIDR ranges are painful to remediate later - and a transit gateway plus centralised egress is the usual pattern. Note that NAT gateways and cross-zone data transfer are frequently the largest surprise line items, which is an argument for centralised egress and for VPC endpoints for AWS service traffic.

**The account count is your operational load.** Every account needs baseline security tooling, network attachment, logging configuration, and lifecycle management. This is why account vending must be automated before you commit to a per-workload model - otherwise the boundary you chose for isolation becomes the thing that slows every new service down.

## Example

```text
Organisation layout - shaped by the policies applied, not the org chart.

  Root
  ├── OU: Security                      SCP: no workloads, deny data egress
  │     ├── log-archive                 (immutable CloudTrail + config history)
  │     ├── audit                       (read-only cross-account access)
  │     └── security-tooling            (GuardDuty admin, Security Hub)
  ├── OU: Infrastructure                SCP: platform team only
  │     ├── network-prod                (transit gateway, central egress, DNS)
  │     ├── network-nonprod
  │     └── shared-services             (registry, artefacts, platform CI)
  ├── OU: Workloads
  │     ├── OU: Prod                    SCP: deny root, deny region != eu-west-1|
  │     │   │                                us-east-1, deny CloudTrail changes,
  │     │   │                                deny unencrypted RDS/S3
  │     │   ├── checkout-prod
  │     │   ├── search-prod
  │     │   └── ... (one account per workload)
  │     └── OU: NonProd                 SCP: as Prod, plus budget enforcement
  │         ├── checkout-staging
  │         └── checkout-dev
  ├── OU: Sandbox                       SCP: hard spend cap, 30-day expiry,
  │     └── sandbox-alice                    deny access to production data
  └── OU: Suspended                     SCP: deny all except read + delete

  Centralised once, not per account:
    identity      federated from the identity provider; zero IAM users anywhere;
                  member-account root credentials removed (centralised root access)
    perimeter     RCP at the root: org resources unusable by outside principals
    logging       all CloudTrail + Config to log-archive, which nobody can write to
    networking    transit gateway attachment + central egress from network-prod
    registry      shared-services, cross-account pull with a resource policy
```

```json
// A high-value SCP. Coarse and few - SCPs are hard to debug, because the
// failure is an unexplained AccessDenied.
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyRootUser",
      "Effect": "Deny",
      "Action": "*",
      "Resource": "*",
      "Condition": { "StringLike": { "aws:PrincipalArn": "arn:aws:iam::*:root" } }
    },
    {
      "Sid": "DenyRegionsWeDoNotOperateIn",
      "Effect": "Deny",
      "NotAction": ["iam:*", "organizations:*", "route53:*", "cloudfront:*", "support:*"],
      "Resource": "*",
      "Condition": {
        "StringNotEquals": { "aws:RequestedRegion": ["eu-west-1", "us-east-1"] }
      }
    },
    {
      "Sid": "ProtectAuditTrail",
      "Effect": "Deny",
      "Action": [
        "cloudtrail:StopLogging",
        "cloudtrail:DeleteTrail",
        "config:DeleteConfigurationRecorder",
        "guardduty:DeleteDetector"
      ],
      "Resource": "*"
    },
    {
      "Sid": "RequireEncryptedRDS",
      "Effect": "Deny",
      "Action": "rds:CreateDBInstance",
      "Resource": "*",
      "Condition": { "Bool": { "rds:StorageEncrypted": "false" } }
    }
  ]
}
```

## Interview tips

- The core claim: on AWS the account is the only boundary that simultaneously bounds quotas, blast radius, and IAM reach - and IAM-based separation within one account always leaks eventually.
- "Shape organisational units around the policies you apply, not the org chart" is the design principle, and it explains why org-chart-shaped structures need constant reshaping.
- Be precise that service control policies bound maximum permissions and grant nothing. Then name the high-value ones: root denial, audit-trail protection, region restriction, encryption requirements.
- Mention RCPs alongside SCPs - SCPs bound your principals, RCPs bound access to your resources - and centralised root access management as the modern answer to root credentials in member accounts. It shows your knowledge is current. For the fundamentals, see [Organizations and SCPs](./what-are-aws-organizations-and-service-control-policies.md).
- Warn that service control policies are hard to debug because the failure is a bare access denial, and that this argues for keeping them few and coarse.
- Centralising logging, identity, networking, and registries is what stops per-account duplication and drift - and the log archive being unwritable by the accounts it audits is a specific, valuable detail.
- Naming NAT gateway and cross-zone data transfer as the surprise cost lines, with centralised egress and VPC endpoints as the mitigation, shows operational experience.
- Close on the account count being your operational load, which is why vending must be automated before committing to per-workload accounts.

---

[⬅ Back to AWS Platform Engineering](./README.md) · [All topics](../README.md)
