---
title: "What is account vending and how do you automate it?"
id: 156
category: "AWS Platform Engineering"
difficulty: "Advanced"
tags:
  - platform-engineering
  - aws-platform-engineering
  - interview-questions
---

# What is account vending and how do you automate it?

**Short answer:** Account vending is creating a new AWS account that arrives fully configured - in the right organisational unit, with logging, security tooling, network attachment, identity federation, budgets, and tags already applied - from a single declarative request. It matters because if a per-workload account model is your isolation boundary, a manually configured account is a multi-day ticket, and the boundary you chose for safety becomes the thing that slows every new service down.

## Detail

**A raw new account is not usable, and that is the whole problem.** Creating one takes an API call. Making it safe and connected requires CloudTrail and Config delivering to the log archive, GuardDuty enabled and joined to the security account, identity provider federation and permission sets, a VPC with the right non-overlapping address range and a transit gateway attachment, service quotas raised from defaults, budgets and alarms, cost allocation tags, and registration in your inventory. That list is where the multi-day ticket comes from, and every item skipped is a gap discovered later.

**Address allocation is the piece that must be centrally managed.** Each account's VPC needs a CIDR range that does not overlap with any other, because overlapping ranges break transit gateway routing and are extremely painful to remediate once workloads exist. The vending process must allocate from a managed pool and record the allocation - not let anyone pick.

**Build it as a declarative request reconciled by automation.** An `Account` object naming the workload, the environment, the owning team, the cost centre, and the tier; a controller or pipeline that creates the account and applies every baseline; and continuous reconciliation so accounts created a year ago gain this year's baseline. The reconciliation matters as much as the creation - a vending pipeline that only runs once leaves you with accounts at different baselines and no way to tell which.

**Use the managed tooling where it fits.** AWS Control Tower provides a landing zone with Account Factory, a catalogue of preventive, detective, and proactive controls, and baseline configuration, and for many organisations adopting it is faster and safer than building equivalents. Account Factory for Terraform (AFT) turns it into the declarative, Git-driven flow described here, with your own customisations applied after creation. Its cost is opinionated structure and less flexibility, though landing zone 4.0 (November 2025) loosened that considerably by making the Config, CloudTrail, and Backup integrations optional and dropping the mandatory Security OU - so the honest position is to use it unless you have a specific requirement it blocks, and be able to say what that requirement would be. See [what Control Tower sets up](./what-does-aws-control-tower-set-up-for-a-platform.md) for the detail.

**Tag at creation, or cost attribution and offboarding both fail.** Owner, cost centre, environment, workload, and data classification applied to the account itself and propagated as defaults. Retrofitting tags across an account's resources later is tedious and never complete.

**Design closure at the same time as creation.** Accounts get abandoned - a project cancelled, a team dissolved. Closure needs a sequence: revoke access, snapshot anything with a retention obligation, remove the network attachment and release the address range back to the pool, release quotas and budgets, then move the account to a suspended organisational unit that denies almost everything, and close it after a cooling-off period. The address range release is the step most often forgotten, and it silently exhausts your pool.

**Measure time to a usable account.** The number that matters is request to a team being able to deploy. Minutes to a couple of hours is achievable; if it is days, teams will start sharing accounts and your isolation model quietly stops being true.

## Example

```yaml
# The whole request. Everything else is derived and continuously reconciled.
apiVersion: platform.example.com/v1
kind: Account
metadata: { name: checkout-prod }
spec:
  workload: checkout
  environment: production
  organisationalUnit: Workloads/Prod # determines which SCPs apply
  owner: group:team-payments
  costCentre: eng-payments
  tier: 1
  dataClassification: pci # selects the stricter baseline
  regions: [eu-west-1] # quotas raised only where needed
  networking:
    attachTo: transit-gateway-prod
    cidr: auto # allocated from the managed pool, never chosen by hand
  budget: { monthly: 40000, currency: USD, alertAt: [50, 80, 100] }
```

```text
What vending applies - and re-applies, so an account created last year gains
this year's baseline automatically.

  IDENTITY
    federation from the identity provider; ZERO IAM users created
    root credentials never set (centralised root access management)
    permission sets: team-payments-admin (non-prod), team-payments-readonly (prod),
                     platform-admin, break-glass (time-bound)
  LOGGING AND AUDIT
    CloudTrail (org trail) -> log-archive, which this account cannot write to
    Config recorder + conformance pack -> log-archive
    GuardDuty enabled, invited to the security account as a member
    Security Hub enabled, findings aggregated centrally
  NETWORK
    VPC with CIDR allocated from the pool and RECORDED   10.42.16.0/20
    private + public subnets across 3 AZs
    transit gateway attachment + route propagation
    central egress via network-prod; NAT is NOT created per account (cost)
    VPC endpoints for S3, ECR, STS, Secrets Manager, CloudWatch (cost + private path)
  GUARDRAILS
    SCPs inherited from Workloads/Prod OU
    account-level: EBS encryption by default, S3 public access block,
                   IMDSv2 required
  OPERATIONS
    service quotas raised from defaults (a common cause of "it works in dev")
    budget + anomaly detection + alarms to the owning team
    cost allocation tags activated
  REGISTRATION
    account recorded in the platform inventory with owner and tier
    added to the fleet definition so cluster/bundle reconciliation reaches it
```

```text
Vending and closure, timed:

  $ platform account vend checkout-prod

    [1/9] account created (Organizations)                        0:42
    [2/9] moved to OU Workloads/Prod - SCPs now apply            0:05
    [3/9] identity federation + permission sets                  0:18
    [4/9] CloudTrail, Config, GuardDuty, Security Hub            2:10
    [5/9] CIDR 10.42.16.0/20 allocated and recorded              0:03
    [6/9] VPC, subnets, TGW attachment, endpoints                4:31
    [7/9] quota increase requests submitted                      0:12  (async)
    [8/9] budget, anomaly detection, cost tags                   0:22
    [9/9] registered in inventory + fleet definition             0:06
    ---------------------------------------------------------------
    usable account                                              ~8:29

  $ platform account close search-dev --reason "project cancelled"

    [1/7] access revoked (federation, permission sets)
    [2/7] retention snapshots taken (2 RDS, 1 S3) - expiry recorded
    [3/7] TGW attachment removed
    [4/7] CIDR 10.42.48.0/20 RELEASED back to the pool   <-- the step most often
                                                             forgotten; skipping
                                                             it silently exhausts
                                                             the address space
    [5/7] budget closed, quotas released
    [6/7] moved to OU Suspended (deny-almost-all), 30-day cooling-off
    [7/7] inventory marked closed; scheduled for closure 2026-11-02
```

## Interview tips

- Frame the problem correctly: creating an account is one API call, making it safe and connected is the multi-day part. That list is the answer.
- Centrally managed CIDR allocation is the detail that marks real experience, because overlapping ranges are extremely painful to fix after workloads exist.
- Emphasise continuous reconciliation, not one-shot creation. Otherwise you have accounts at different baselines with no way to tell which.
- Take a clear position on Control Tower: use it unless you have a specific requirement it blocks, and be able to name what that would be. Both "always build it yourself" and "never look at the managed option" sound inexperienced.
- Tagging at creation, because retrofitting is never complete, connects vending to cost attribution and offboarding.
- Closure as a designed sequence - and specifically releasing the address range back to the pool - is the step almost everyone forgets and a memorable thing to raise.
- Close on time-to-usable-account as the metric, with the consequence: if it is days, teams share accounts and your isolation model stops being true.

---

[⬅ Back to AWS Platform Engineering](./README.md) · [All topics](../README.md)
