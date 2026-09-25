---
title: "What are AWS Organizations and service control policies?"
id: 146
category: "AWS Platform Engineering"
difficulty: "Beginner"
tags:
  - platform-engineering
  - aws-platform-engineering
  - interview-questions
---

# What are AWS Organizations and service control policies?

**Short answer:** AWS Organizations groups many AWS accounts under one management account, arranges them into a tree of organisational units, consolidates their billing, and lets you attach policies to any point in that tree. Service control policies (SCPs) are the best-known of those policies: they set the maximum permissions available to IAM users and roles in the accounts below them, and they never grant anything. Resource control policies (RCPs) are their newer counterpart, capping what can be done _to_ your resources, whoever is asking.

## Detail

**The pieces of an organisation.** There is one **management account** that creates the organisation and pays the bill, any number of **member accounts**, and a **root** with **organisational units** (OUs) nested beneath it. An account sits in exactly one OU. Policies attached to the root or an OU are inherited by everything beneath it, which is what makes the structure useful: you express a rule once for "all production accounts" rather than once per account.

**Why platform teams care.** On AWS the account is the strongest isolation boundary - quotas, IAM reach, and billing are all per account - so a serious platform ends up with dozens or hundreds of them. Organizations is what makes that many accounts governable. The users of this capability are mostly invisible to it: product teams working inside their accounts, who benefit from guardrails they never have to configure, and security and finance teams, who get one place to enforce rules and one bill to read.

**What an SCP actually does.** An SCP is a JSON policy in the IAM language, but it is a filter rather than a grant. When a principal in a member account makes a request, AWS evaluates its identity policies, any resource policy, and every SCP on the path from the root down to the account. A request succeeds only if it is allowed by the principal's own policies _and_ not blocked by any SCP. So an SCP that allows `s3:*` gives nobody S3 access; it merely leaves S3 available for IAM to grant.

**Two evaluation rules catch people out.**

- An explicit `Deny` in any SCP, at any level, wins.
- For an action to be available, it must be allowed at _every_ level from the root to the account. AWS attaches a `FullAWSAccess` SCP everywhere by default, which is why most organisations write deny-list SCPs and leave that allow in place. Removing it from one OU silently blocks everything beneath.

**What SCPs do not touch.** They do not apply to the management account at all, which is the main reason to keep workloads out of it. They do not restrict service-linked roles, which AWS services use on your behalf. And they do not affect principals from _outside_ your organisation acting on your resources - which is the gap RCPs close.

**Resource control policies, the other half.** Introduced in late 2024, an RCP attaches to the same tree but applies to resources in those accounts rather than principals. The canonical use is a **data perimeter**: "no principal outside my organisation may read my S3 buckets, decrypt with my KMS keys, or assume my roles", enforced centrally even if a team writes an over-permissive bucket policy. RCPs cover a growing but not universal set of services - they launched with S3, STS, KMS, SQS, and Secrets Manager and have since added more (ECR, DynamoDB, and CloudWatch Logs among them) - so check the current list rather than assuming.

**The other policy types.** Organizations also holds management policies that configure rather than restrict: tag policies (permitted tag keys and values), backup policies, AI services opt-out policies, and declarative policies that pin a service configuration - such as blocking public AMI sharing or requiring IMDSv2 on EC2 - across accounts in a way that survives API changes.

**The trade-off.** SCPs are powerful and blunt. A denial caused by an SCP arrives as an `AccessDenied` that the affected engineer usually cannot see the source of, a bad SCP on a busy OU breaks many teams at once, and there are hard limits (five SCPs attached per target, 5,120 characters each). Keep them few, coarse, and tested in a non-production OU first.

## Example

```json
// SCP attached to the Workloads OU. Deny-list style: FullAWSAccess stays
// attached, and these statements carve out what nobody below may do.
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyLeavingTheOrganisation",
      "Effect": "Deny",
      "Action": "organizations:LeaveOrganization",
      "Resource": "*"
    },
    {
      "Sid": "DenyUnapprovedRegions",
      "Effect": "Deny",
      "NotAction": ["iam:*", "organizations:*", "sts:*", "route53:*", "cloudfront:*", "support:*"],
      "Resource": "*",
      "Condition": {
        "StringNotEquals": { "aws:RequestedRegion": ["eu-west-1", "eu-central-1"] }
      }
    }
  ]
}
```

```json
// RCP attached at the root: resources in the organisation cannot be used by
// principals from outside it, except AWS services acting on your behalf.
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EnforceOrgIdentityPerimeter",
      "Effect": "Deny",
      "Principal": "*",
      "Action": ["s3:*", "sqs:*", "kms:*", "secretsmanager:*", "sts:AssumeRole"],
      "Resource": "*",
      "Condition": {
        "StringNotEqualsIfExists": { "aws:PrincipalOrgID": "o-exampleorgid" },
        "BoolIfExists": { "aws:PrincipalIsAWSService": "false" }
      }
    }
  ]
}
```

```bash
# Policy types are enabled per root, then policies are created and attached.
aws organizations enable-policy-type \
  --root-id r-ab12 --policy-type RESOURCE_CONTROL_POLICY

aws organizations create-policy \
  --name workloads-guardrails --type SERVICE_CONTROL_POLICY \
  --description "Region restriction and org-leave protection" \
  --content file://workloads-guardrails.json

aws organizations attach-policy \
  --policy-id p-examplepolicy --target-id ou-ab12-workloads
```

```text
How a request from checkout-prod is evaluated:

  Root            SCP FullAWSAccess (allow)   RCP perimeter (deny outsiders)
   └─ Workloads   SCP workloads-guardrails (deny regions, deny leave)
       └─ Prod    SCP FullAWSAccess (allow)
           └─ checkout-prod
                role checkout-deployer   identity policy: allow ec2:RunInstances

  RunInstances in eu-west-1   -> allowed by IAM, not denied by any SCP   ALLOWED
  RunInstances in us-east-1   -> denied by workloads-guardrails          DENIED
  (the engineer sees AccessDenied with an "explicit deny in a service control
   policy" reason - make sure they know where to look)
```

## Interview tips

- Say plainly that SCPs **never grant** permissions; they bound them. Candidates who describe an SCP "giving access to S3" have not used one.
- Explain the two rules: any deny wins, and an allow must exist at every level from the root down. That second one explains why removing `FullAWSAccess` breaks an OU.
- Name the exemptions - the management account and service-linked roles - and draw the conclusion: keep workloads out of the management account.
- Mention RCPs as the resource-side complement and the data perimeter as their main use. It shows your knowledge is current.
- Expect the follow-up "how would you roll out a new SCP safely?" - test in a sandbox OU, check CloudTrail for actions it would have denied, then attach to non-production before production. See [how to structure a multi-account platform](./how-do-you-structure-a-multi-account-aws-platform.md) for where these policies sit in a full design.

---

[⬅ Back to AWS Platform Engineering](./README.md) · [All topics](../README.md)
