---
title: "How do you automate project vending on GCP?"
id: 98
category: "GCP Platform Engineering"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - gcp-platform-engineering
  - interview-questions
---

# How do you automate project vending on GCP?

**Short answer:** A declarative request produces a project created under the right folder, linked to a billing account, with the required APIs enabled, attached to the Shared VPC with subnet-scoped access, logging sinks and budgets configured, quotas raised, IAM bound to the owning group, and a registry entry - all reconciled continuously rather than applied once. On GCP the two steps most often forgotten are enabling the specific APIs a workload needs and raising per-project quotas from their defaults.

## Detail

**A raw project is close to useless.** Creating one is an API call. Making it usable requires the folder placement that determines which organisation policies apply, a billing account link, service APIs enabled, Shared VPC attachment with subnet-level network user grants, log sinks to the aggregation project, a budget with alerts, IAM bindings for the owning group, and quota increases. Each of those omitted is a failure someone discovers later, usually at an inconvenient time.

**API enablement is GCP-specific and easy to miss.** Services are disabled until enabled per project, so a workload that works in a long-established development project fails in a fresh one with an error about an API not being enabled. Vending should enable a baseline set plus whatever the workload declares, and enabling APIs should be part of the reconciled definition rather than something a developer discovers.

**Quotas are per project and per region, and defaults are often low.** This is the second classic surprise, and it presents as a deployment failing at scale rather than as a configuration problem. Raising the quotas a tier-1 workload will need belongs in vending, and quota requests can take time to approve - which is another reason to do it at creation rather than under pressure.

**Folder placement is the security step.** Organisation policies are inherited from the folder, so placing the project under `workloads/prod` is what applies the no-public-IP, no-service-account-keys, region-restriction, and public-access-prevention constraints. A project created in the wrong place is a project without guardrails, and this is worth validating rather than assuming.

**Attach to Shared VPC with subnet-scoped grants.** Attach the project as a service project and grant the network user role on the specific subnets it should use - not on the host project. Getting this wrong lets the project use any subnet in the host project.

**Reconcile continuously, do not vend once.** Re-running the definition on a schedule means a project created a year ago gains this year's baseline - new log sinks, new budget thresholds, newly required APIs - automatically. One-shot vending leaves you with projects at different baselines and no way to tell which.

**Sensible implementations.** Terraform with a project-factory style module is the common path and gives you the reviewable plan. Config Connector can do it too if your control plane is Kubernetes - though note it cannot create the project containing the cluster it runs in, so a bootstrap layer remains. Either way, teams should never create projects directly.

**Design closure alongside creation.** Deleting a project is genuinely clean on GCP, which is an advantage - but it needs sequencing: revoke access, snapshot what has a retention obligation, detach from the Shared VPC, release subnet grants, close the budget, remove log sink exclusions, then delete. GCP's deletion grace period is useful here, giving a recovery window before the project is unrecoverable.

**Measure time to a usable project.** The number that matters is request to a team being able to deploy. If it is days, teams will share projects and your isolation model quietly stops being true.

## Example

```yaml
# The whole request. Everything else is derived and continuously reconciled.
apiVersion: platform.example.com/v1
kind: Project
metadata: { name: checkout-prod }
spec:
  workload: checkout
  environment: production
  folder: workloads/prod # DETERMINES WHICH ORG POLICIES APPLY
  owner: group:team-payments@example.com
  costCentre: eng-payments
  tier: 1
  billingAccount: <billing-account-id>
  regions: [europe-west1]
  sharedVpc:
    hostProject: vpc-host-prod
    subnets: [snet-eu-west1-app] # network user granted on THESE only
  apis: # beyond the baseline set
    - sqladmin.googleapis.com
    - pubsub.googleapis.com
    - secretmanager.googleapis.com
  budget: { monthly: 40000, currency: USD, alertAt: [50, 80, 100] }
```

```text
What vending applies - and re-applies weekly, so old projects gain new baselines.

  PLACEMENT AND BILLING
    project created under folder workloads/prod
      -> inherits: disableServiceAccountKeyCreation, vmExternalIpAccess deny,
                   restrictPublicIp, publicAccessPrevention, resourceLocations
    billing account linked (a project without billing fails in confusing ways)

  APIS  (GCP-specific, and the most common "works in dev, fails in prod")
    baseline: compute, container, logging, monitoring, iam, cloudresourcemanager,
              artifactregistry, cloudkms
    declared: sqladmin, pubsub, secretmanager

  NETWORK
    attached to vpc-host-prod as a service project
    networkUser granted on snet-eu-west1-app ONLY - not on the host project
    no Cloud NAT created here; egress via the host project's NAT

  OBSERVABILITY AND COST
    log sink -> aggregation project (retention by tier)
    budget + alerts to the owning group
    labels: tenant, cost-centre, workload, environment

  IAM
    group:team-payments -> viewer in prod, editor in non-prod
    platform group -> admin
    NO service account keys possible (org policy from the folder)

  QUOTAS  (per project AND per region; defaults are often low)
    CPUs, in-use addresses, Cloud SQL instances, Pub/Sub throughput
    -> requested at creation, because approval can take time and you do not
       want to discover this during a launch

  REGISTRATION
    recorded in the platform inventory with owner and tier
    added to the fleet definition
```

```text
Timings, and the closure sequence:

  $ platform project vend checkout-prod

    [1/8] project created under folder workloads/prod          0:22
          -> org policies now inherited. Validated, not assumed.
    [2/8] billing account linked                               0:06
    [3/8] 11 APIs enabled                                      1:48
    [4/8] Shared VPC attached; networkUser on 1 subnet         0:31
    [5/8] log sink -> aggregation project                      0:14
    [6/8] budget, alerts, labels                               0:11
    [7/8] IAM bound to group:team-payments                     0:08
    [8/8] quota increases requested (4)                        0:09  (async approval)
    ---------------------------------------------------------------
    usable project                                            ~3:29

  $ platform project close search-dev --reason "project cancelled"

    [1/6] IAM bindings revoked
    [2/6] retention snapshots taken (1 SQL instance) - expiry recorded
    [3/6] detached from Shared VPC; subnet networkUser grants removed
    [4/6] budget closed; log sink removed from aggregation
    [5/6] project deleted -> enters GCP's deletion grace period
          (a genuine advantage: a recovery window before it is unrecoverable)
    [6/6] inventory marked closed; permanent deletion date recorded
```

## Interview tips

- Frame it as with any vending question: creation is one API call, making the project usable is the work. Then list what "usable" requires.
- API enablement is the GCP-specific detail interviewers listen for, and the "works in dev, fails in a fresh project" symptom makes it concrete.
- Per-project-per-region quotas with low defaults is the second GCP-specific surprise, and noting that approval takes time justifies doing it at creation.
- Folder placement as the security step - it is what applies the organisation policies - and validating rather than assuming it.
- Subnet-scoped network user grants rather than host-project-scoped connects this back to the Shared VPC design.
- Continuous reconciliation over one-shot vending, with the payoff that old projects gain new baselines automatically.
- GCP's deletion grace period as a genuine advantage for closure is a nice detail, and closure sequencing shows you designed the whole lifecycle.

---

[⬅ Back to GCP Platform Engineering](./README.md) · [All topics](../README.md)
