---
title: "What is the difference between an IAM user and an IAM role?"
id: 148
category: "AWS Platform Engineering"
difficulty: "Beginner"
tags:
  - platform-engineering
  - aws-platform-engineering
  - interview-questions
---

# What is the difference between an IAM user and an IAM role?

**Short answer:** An IAM user is a long-lived identity that belongs to one account and authenticates with its own credentials - a console password, access keys, or both - which stay valid until someone rotates or deletes them. An IAM role has no credentials of its own: a trusted principal _assumes_ it through AWS STS and receives temporary credentials that expire, typically within an hour. For a platform, the practical rule is that people and workloads should use roles, and IAM users should be rare, justified exceptions.

## Detail

**An IAM user is a named identity with standing credentials.** You create `alice` or `ci-bot` in an account, attach permission policies, and give it a password for the console or an access key pair (`AKIA...` plus a secret) for the API. Those keys work from anywhere on the internet until they are revoked. That is the core problem: a key pasted into a CI variable, a laptop dotfile, or a public repository is a credential that nobody may notice has leaked, and it does not expire on its own.

**An IAM role is a set of permissions that someone borrows.** A role has two policies that do different jobs:

- the **trust policy** says _who_ may assume the role - another AWS account, an AWS service such as EC2 or Lambda, an identity provider through SAML or OIDC, or a specific role;
- the **permission policies** say _what_ the role may do once assumed.

Assuming a role calls STS (`AssumeRole`, `AssumeRoleWithWebIdentity`, or `AssumeRoleWithSAML`), which returns an access key ID (`ASIA...`), a secret, and a **session token**, all with an expiry. When they expire, the caller assumes the role again. A leaked session credential is a problem for minutes or hours, not indefinitely.

**How each kind of user reaches AWS on a well-run platform.**

| Who                      | Mechanism                                                           | Long-lived secret? |
| ------------------------ | ------------------------------------------------------------------- | ------------------ |
| Engineers                | IAM Identity Center permission sets, federated from the company IdP | No                 |
| EC2 instances            | Instance profile (a role attached to the instance)                  | No                 |
| Pods on EKS              | EKS Pod Identity or IRSA                                            | No                 |
| Lambda functions         | Execution role                                                      | No                 |
| CI pipelines             | OIDC federation (for example GitHub Actions to STS)                 | No                 |
| Workloads outside AWS    | IAM Roles Anywhere with X.509 certificates                          | No (certificate)   |
| Another account's system | Cross-account role with a trust policy naming that account          | No                 |

IAM Identity Center is worth naming precisely: a permission set assigned to a user in an account is materialised as an IAM role in that account, so even human access is role-based under the hood. The user of the platform - a developer - signs in once with their company identity and picks an account and role; they never hold an AWS key.

**Where IAM users still appear.** Legacy third-party tools that only accept static keys, a small number of break-glass identities kept locked away, and services that specifically require them. Each should be treated as an exception: recorded, owned, rotated, and ideally monitored for any use at all. Where a tool supports it, replace keys with OIDC federation or Roles Anywhere.

**Roles are also how accounts talk to each other.** In a multi-account platform, a deployment pipeline in a tooling account assumes a deployer role in each workload account. The trust policy in the target names the source role, and the source role's policy allows `sts:AssumeRole` on the target - both sides must agree. That two-sided handshake is what keeps cross-account access explicit.

**The trade-off.** Roles push complexity into trust relationships. A trust policy with a loose condition - a wildcard OIDC subject, or trusting a whole account rather than a specific role - quietly widens who can assume it, and session duration limits and role chaining (a role assuming another role is capped at a one-hour session) can surprise long-running jobs. The platform should generate trust policies from templates rather than letting each team hand-write them.

## Example

```json
// Trust policy for a deploy role assumed by GitHub Actions via OIDC.
// No access key exists anywhere; the pipeline gets short-lived credentials
// only when running on main in this one repository.
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::111122223333:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:example-org/checkout:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

```bash
# The difference is visible in the credentials themselves.
$ aws sts get-caller-identity --profile legacy-user
{ "Arn": "arn:aws:iam::111122223333:user/ci-bot" }          # AKIA... key, never expires

$ aws sts assume-role \
    --role-arn arn:aws:iam::111122223333:role/checkout-deployer \
    --role-session-name alice-debug --duration-seconds 3600
{
  "Credentials": {
    "AccessKeyId": "ASIA...",
    "SecretAccessKey": "...",
    "SessionToken": "...",
    "Expiration": "2026-09-25T11:04:12Z"
  },
  "AssumedRoleUser": {
    "Arn": "arn:aws:sts::111122223333:assumed-role/checkout-deployer/alice-debug"
  }
}
```

```text
Platform audit - what "zero IAM users" looks like in practice:

  $ aws iam generate-credential-report && aws iam get-credential-report ...

  account          users  active keys  oldest key   status
  checkout-prod      0        0            -        OK
  search-prod        0        0            -        OK
  shared-services    1        1         212 days    EXCEPTION: vendor-scanner
                                                    owner team-security,
                                                    replace with Roles Anywhere
  break-glass        2        0            -        OK (console + MFA only)
```

## Interview tips

- Lead with credentials: users have **standing** credentials, roles hand out **temporary** ones via STS. Everything else follows from that.
- Name both halves of a role - trust policy (who) and permission policy (what). Many candidates only describe the second.
- Show you know how each consumer gets a role: Identity Center for people, instance profiles, Pod Identity, execution roles, OIDC for CI, Roles Anywhere for off-AWS workloads.
- Treat remaining IAM users as tracked exceptions, not a normal pattern, and mention the credential report as the way to find them.
- Expect a follow-up on cross-account access or CI. See [secretless CI/CD](../platform-security/how-do-you-run-a-secretless-ci-cd-pipeline.md) and [pod access on EKS](./how-do-you-give-pods-on-eks-access-to-aws-resources-safely.md).

---

[⬅ Back to AWS Platform Engineering](./README.md) · [All topics](../README.md)
