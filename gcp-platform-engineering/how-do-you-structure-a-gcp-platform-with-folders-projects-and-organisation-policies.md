---
title: "How do you structure a GCP platform with folders, projects, and organisation policies?"
id: 93
category: "GCP Platform Engineering"
difficulty: "Advanced"
tags:
  - platform-engineering
  - gcp-platform-engineering
  - interview-questions
---

# How do you structure a GCP platform with folders, projects, and organisation policies?

**Short answer:** The project is the fundamental unit - of isolation, quota, billing, and IAM - and folders exist to attach IAM and organisation policies to groups of projects. Shape the folder hierarchy around the policies you need to differentiate, use one project per workload per environment, and attach organisation policies at the folder so they inherit. Organisation policies constrain what can be configured; IAM controls who can act.

## Detail

**The project is where almost everything lives.** Quotas are per project, APIs are enabled per project, billing attributes per project, and IAM bindings at the project level cover its resources. A project can also be deleted, which is a clean offboarding primitive. Trying to separate workloads inside one project with IAM alone means sharing quotas and accepting a much larger blast radius.

**Folders are policy attachment points.** IAM bindings and organisation policies set on a folder apply to everything beneath. That is their purpose, so the hierarchy should mirror policy differences - environment, sensitivity, whether public exposure is permitted - rather than the organisation chart, which changes and rarely corresponds to a control you apply.

**Organisation policies are the guardrail layer, and they are constraint-based rather than permission-based.** They restrict what configurations are possible regardless of what IAM permits, which makes them the right place for things that must never be true. The high-value ones:

| Constraint                             | Prevents                                  |
| -------------------------------------- | ----------------------------------------- |
| `iam.disableServiceAccountKeyCreation` | Long-lived service account keys existing  |
| `storage.publicAccessPrevention`       | Publicly readable buckets                 |
| `compute.vmExternalIpAccess`           | VMs with public addresses                 |
| `sql.restrictPublicIp`                 | Cloud SQL instances with public addresses |
| `gcp.resourceLocations`                | Resources outside approved regions        |
| `compute.requireShieldedVm`            | VMs without integrity monitoring          |
| `iam.allowedPolicyMemberDomains`       | Granting access to external identities    |

The first is the single most valuable one for a platform: disabling service account key creation forces every workload onto federated identity, which removes a whole class of credential leaks by construction rather than by policy review.

**Custom constraints extend this.** Beyond the predefined list, custom organisation policy constraints let you express rules against resource fields - requiring a specific label, forbidding a machine type family - which covers cases you would otherwise have to catch with detective controls.

**A conventional hierarchy:**

| Folder                | Contains                                 | Distinct policy                            |
| --------------------- | ---------------------------------------- | ------------------------------------------ |
| `platform/`           | Shared services, control plane, registry | Platform team only                         |
| `platform/networking` | Shared VPC host projects                 | Network administration isolated            |
| `platform/logging`    | Log sinks and the log project            | Write-only from elsewhere; restricted read |
| `workloads/prod`      | One project per workload                 | No public IPs, region restriction, no keys |
| `workloads/nonprod`   | Dev and staging projects                 | Looser, plus budget and expiry enforcement |
| `sandbox/`            | Individual experimentation projects      | Spend caps, expiry, no production data     |

**Centralise what only makes sense once:** log sinks aggregating to a dedicated project, identity federated from your provider with no separate accounts, Shared VPC host projects providing subnets to service projects, and Artifact Registry shared across the estate.

**Watch the quota model.** Many quotas are per project and per region, and defaults are frequently lower than production needs. The classic surprise is a workload that works in a long-established development project and fails in a freshly vended production project, so raising quotas belongs in vending rather than in incident response.

**Consider the reference implementations.** Google publishes landing-zone style blueprints for this pattern. Adopting one is usually faster and safer than assembling equivalents, and the honest position is to use it unless a specific requirement blocks you.

## Example

```text
Hierarchy shaped by the policies attached, not by the org chart.

  Organisation
  ├── folder: platform/                  IAM: platform team only
  │     ├── folder: networking/          org policy: no workloads here
  │     │     ├── proj: vpc-host-prod    (Shared VPC host)
  │     │     └── proj: vpc-host-nonprod
  │     ├── proj: logging                (aggregated sinks; restricted read)
  │     ├── proj: artifacts              (Artifact Registry, shared)
  │     └── proj: control-plane          (GKE running Config Connector, Config Sync)
  ├── folder: workloads/
  │     ├── folder: prod/                org policy:
  │     │     │                            iam.disableServiceAccountKeyCreation
  │     │     │                            compute.vmExternalIpAccess = deny
  │     │     │                            sql.restrictPublicIp = true
  │     │     │                            storage.publicAccessPrevention = enforced
  │     │     │                            gcp.resourceLocations = eu-west1|us-east1
  │     │     ├── proj: checkout-prod
  │     │     └── proj: search-prod      (one project per workload)
  │     └── folder: nonprod/             as prod, plus budget enforcement
  │           ├── proj: checkout-staging
  │           └── proj: checkout-dev
  └── folder: sandbox/                   org policy: spend cap, 30-day expiry,
        └── proj: sandbox-alice                      no access to production data

  The most valuable single line above is disableServiceAccountKeyCreation on
  workloads/. It makes the most common GCP credential leak impossible to create,
  rather than something to find in review.
```

```yaml
# Organisation policy at the folder, inherited by every project beneath.
# Attaching per project is how hierarchies drift.
name: folders/<workloads-prod-folder-id>/policies/iam.disableServiceAccountKeyCreation
spec:
  rules:
    - enforce: true
  inheritFromParent: true
---
name: folders/<workloads-prod-folder-id>/policies/compute.vmExternalIpAccess
spec:
  rules:
    - denyAll: true
  inheritFromParent: true
---
name: folders/<workloads-prod-folder-id>/policies/gcp.resourceLocations
spec:
  rules:
    - values:
        allowedValues:
          - in:eu-west1-locations
          - in:us-east1-locations
  inheritFromParent: true
```

```yaml
# A custom constraint - for rules the predefined list does not cover.
name: organizations/<org-id>/customConstraints/custom.requireCostCentreLabel
resourceTypes:
  - container.googleapis.com/Cluster
  - sqladmin.googleapis.com/Instance
  - storage.googleapis.com/Bucket
methodTypes: [CREATE, UPDATE]
condition: "has(resource.labels) && 'cost-centre' in resource.labels"
actionType: ALLOW
displayName: Require a cost-centre label
description: >
  Cost attribution depends entirely on labels being present at creation.
  Retrofitting them later is never complete.
```

## Interview tips

- Be precise that the project is the unit of isolation, quota, billing, and IAM, and that folders exist to attach policy. Getting that hierarchy straight is what the question tests.
- "Shape folders around policy differences, not the org chart" is the design principle, with the reason: org-shaped hierarchies need reshaping at every reorganisation.
- Distinguish organisation policies from IAM: constraints on what can be configured versus who can act. Many candidates conflate them.
- `iam.disableServiceAccountKeyCreation` is the single highest-value constraint to name, because it eliminates GCP's most common credential leak by construction and forces federated identity.
- Mention custom constraints - they are the current answer for rules the predefined list does not cover, and requiring a cost-centre label is a good example.
- Per-project-per-region quotas causing the "works in dev, fails in a new prod project" surprise is a practical detail that belongs in vending.
- Take a position on the published blueprints: adopt unless a specific requirement blocks you.

---

[⬅ Back to GCP Platform Engineering](./README.md) · [All topics](../README.md)
