---
title: "How do you use GKE fleets to manage many clusters?"
id: 180
category: "GCP Platform Engineering"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - gcp-platform-engineering
  - interview-questions
---

# How do you use GKE fleets to manage many clusters?

**Short answer:** A fleet is a logical group of clusters registered to one fleet host project, and it lets you configure features once for the whole group - Config Sync, Policy Controller, multi-cluster networking, upgrade sequencing - instead of cluster by cluster. Fleets rest on the idea of sameness: a namespace or a Kubernetes service account with the same name is treated as the same thing in every member cluster. On top of that, team scopes give each tenant a slice of the fleet with its own namespaces and RBAC, so teams think in terms of their environments rather than individual clusters.

## Detail

**The mechanism.** Each cluster becomes a fleet **membership** when it is registered - automatically at creation with `--fleet-project`, or explicitly for existing and non-GKE clusters. The fleet belongs to a **fleet host project**; a project hosts at most one fleet and a cluster belongs to one fleet, though member clusters can live in other projects. Fleet-level **features** are then enabled on the fleet and pushed to memberships. Since September 2025 these capabilities, previously sold as GKE Enterprise, are part of the base GKE offering, so using fleets no longer requires a separate edition.

**Sameness is the design principle, and the security boundary.** Fleets assume that a namespace called `payments` means the same tenant in every cluster, and that a Kubernetes service account `payments/checkout` is the same workload everywhere. Workload Identity Federation for GKE makes this literal: all member clusters share the fleet's identity pool, `FLEET_HOST_PROJECT.svc.id.goog`, so an IAM grant to that principal is honoured in every cluster. The consequence to state in an interview: **never put clusters of different trust levels in the same fleet.** A sandbox cluster where anyone can create a `payments` namespace would inherit production's permissions. The usual pattern is one fleet per environment - production, non-production, sandbox - each with its own host project.

**Fleet-level defaults stop drift at creation.** Features such as Config Sync and Policy Controller accept a fleet-default member configuration, applied to every cluster that joins. A new cluster registers and within minutes has the platform's baseline - namespaces, RBAC, network policy, admission constraints - reconciled from the platform's source. That removes the "cluster 14 was built before we added that policy" class of problem. See [How do you use Config Connector and Config Sync as a GCP control plane?](./how-do-you-use-config-connector-and-config-sync-as-a-gcp-control-plane.md) for the Config Sync side.

**Team scopes are the tenant abstraction.** A **scope** is a named subset of the fleet for a team. You bind clusters to it, create **fleet namespaces** within it - which then exist on every bound cluster - and grant the team's group a role across the scope. The team gets consistent access, logs, and metrics across its clusters without the platform hand-editing RBAC on each. Adding a region becomes binding one more cluster to the scope.

**Upgrade sequencing uses fleets as stages.** Rollout sequencing lets you chain fleets - non-production upstream of production, for example - with a soak time between them. When a new version arrives in the release channel, GKE upgrades the upstream fleet first and only moves on to the downstream fleet after the soak, so production is never the first place a version runs. Newer custom-stage sequences refine this further within a fleet. This is the fleet's most direct payoff for reliability; the wider practice is in [How do you upgrade a fleet of clusters without breaking tenants?](../kubernetes-platform/how-do-you-upgrade-a-fleet-of-clusters-without-breaking-tenants.md).

**Multi-cluster networking.** With the multi-cluster Services feature, a `ServiceExport` in one cluster makes a Service reachable from the others through a `ServiceImport`. Multi-cluster Gateway lets one Gateway, defined in a config cluster, load-balance across backends in several member clusters. Both depend on namespace sameness - the exported Service must live in the same-named namespace everywhere.

**Who uses this, and what it saves them.** Two users. The platform team gets one place to set baselines, sequence upgrades, and see fleet-wide posture, which is what makes fifty clusters operable by a team sized for five. Product teams get a scope: "your namespaces exist in these three regions and you have edit access to them", without caring which cluster is which.

**The trade-offs.** Sameness is powerful and unforgiving - a namespace naming mistake becomes a cross-cluster identity problem. Fleet features are Google-managed, so their version cadence and supported configuration are not entirely yours to choose. And a fleet is a GKE-centric model: if much of your estate is on other clouds, a vendor-neutral layer such as Argo CD or Flux with its own cluster inventory may be the better common denominator, with fleets used only for the GKE part.

## Example

```bash
# One fleet per environment: prod clusters register to the prod fleet host project.
gcloud container clusters create-auto prod-eu-1 \
  --project=gke-prod-eu --region=europe-west1 \
  --fleet-project=fleet-prod

gcloud container fleet memberships list --project=fleet-prod

# Every cluster that joins gets the platform baseline via Config Sync.
gcloud beta container fleet config-management enable \
  --project=fleet-prod \
  --fleet-default-member-config=fleet-default.yaml
```

```yaml
# fleet-default.yaml - applied to every member of fleet-prod.
applySpecVersion: 1
spec:
  configSync:
    enabled: true
    sourceType: oci
    sourceFormat: unstructured
    syncRepo: europe-docker.pkg.dev/fleet-prod/config/platform-baseline:v2026.09.2
    policyDir: .
    secretType: k8sserviceaccount # Workload Identity - no key, no Secret
```

```bash
# A team scope: bind clusters, create fleet namespaces, grant the team's group.
gcloud container fleet scopes create payments --project=fleet-prod

gcloud container fleet memberships bindings create prod-eu-1-payments \
  --membership=prod-eu-1 --scope=payments --location=europe-west1 \
  --project=fleet-prod

gcloud container fleet scopes namespaces create payments \
  --scope=payments --project=fleet-prod

gcloud beta container fleet scopes add-app-operator-binding payments \
  --role=edit --group=team-payments@example.com --project=fleet-prod

# Upgrade sequencing: non-prod fleet first, production 7 days later.
gcloud container fleet clusterupgrade update \
  --project=fleet-nonprod --default-upgrade-soaking=2d
gcloud container fleet clusterupgrade update \
  --project=fleet-prod --upstream-fleet=fleet-nonprod --default-upgrade-soaking=7d
```

```text
Why fleets are per environment - the sameness trap:

  fleet-prod   identity pool fleet-prod.svc.id.goog
    prod-eu-1    ns/payments sa/checkout  -> can read payments-prod secrets
    prod-us-1    ns/payments sa/checkout  -> same principal, same access (intended)

  if a sandbox cluster joined fleet-prod:
    sandbox-1    anyone creates ns/payments sa/checkout
                 -> SAME principal -> production secrets. Not intended.

  rule: one fleet per trust level; sandbox never shares a fleet with prod.
```

## Interview tips

- Define a fleet by what it does - configure once, apply to all members - and name the host project and memberships. Then go straight to sameness, because it is what makes fleets different from a cluster list.
- The sameness trap is the high-value point: shared identity pools mean a cluster of lower trust in the same fleet can impersonate production workloads. "One fleet per trust level" is the rule to state.
- Mention fleet-level defaults for Config Sync and Policy Controller as the answer to drift across many clusters.
- Explain team scopes and fleet namespaces as the tenant interface - teams get their namespaces across clusters with one binding.
- Rollout sequencing with soak times between fleets is a concrete reliability benefit and a common follow-up.
- Be current: since September 2025 fleet features are part of base GKE, not a separate GKE Enterprise edition.
- Show judgement on multi-cloud: fleets are GKE-centric, and a vendor-neutral GitOps layer may be the common denominator across clouds.

---

[⬅ Back to GCP Platform Engineering](./README.md) · [All topics](../README.md)
