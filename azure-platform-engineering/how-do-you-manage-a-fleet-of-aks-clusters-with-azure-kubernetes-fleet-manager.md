---
title: "How do you manage a fleet of AKS clusters with Azure Kubernetes Fleet Manager?"
id: 171
category: "Azure Platform Engineering"
difficulty: "Advanced"
tags:
  - platform-engineering
  - azure-platform-engineering
  - interview-questions
---

# How do you manage a fleet of AKS clusters with Azure Kubernetes Fleet Manager?

**Short answer:** Join clusters to a Fleet Manager resource as members, group them into update groups, and define update strategies (ordered stages with waits and approvals) so Kubernetes and node image upgrades roll across the fleet test-first rather than all at once. Auto-upgrade profiles then trigger those runs whenever AKS publishes a new version. If you enable the optional hub cluster, you also get resource placement: `ClusterResourcePlacement` objects that propagate namespaces and resources to member clusters chosen by labels, names, or spread rules. Fleet Manager coordinates clusters; it does not replace your GitOps or your tenancy design.

## Detail

**Two shapes of fleet, and the choice is one-way.** A Fleet Manager without a hub cluster only orchestrates updates: it calls the AKS API on each member in the order you define. A Fleet Manager with a hub cluster adds a small, Microsoft-provisioned Kubernetes API that acts as the fleet's control plane for resource placement, managed fleet namespaces, and the preview multi-cluster networking features. You can add a hub later, but you cannot remove one, and a hub's public or private network mode is fixed at creation. Start hubless if all you need is safe upgrades.

**Members can be AKS clusters in any subscription and region, and Arc-enabled clusters.** A member is a lightweight join, so one fleet can span production subscriptions in several regions, plus Arc-enabled Kubernetes clusters on other clouds or on-premises. Each member can be assigned an update group, which is the unit update strategies work with. Labels on members, such as `environment=prod` or a ring number, are what placement policies select on.

**Update orchestration is the reason most teams adopt it.** Without Fleet Manager, each cluster's auto-upgrade channel moves independently, so production can upgrade before staging has proved the version. An update run fixes the order:

| Concept              | What it is                                                                                                      |
| -------------------- | --------------------------------------------------------------------------------------------------------------- |
| Update group         | A set of member clusters updated together                                                                       |
| Stage                | An ordered set of groups; the next stage starts only when this one finishes                                     |
| Wait / approval      | A timed soak after a stage, or a manual or automated approval gate                                              |
| Update strategy      | A reusable template of stages and groups                                                                        |
| Update run           | One execution: upgrade type (`Full`, `ControlPlaneOnly`, `NodeImageOnly`), target version, node image selection |
| Auto-upgrade profile | Creates update runs automatically when a new version appears on a channel                                       |

Auto-upgrade profiles support `Stable`, `Rapid`, `NodeImage`, and `TargetKubernetesVersion` channels, with a security-patch channel in preview. Node image selection is either `Latest` (each cluster takes its region's newest image) or `Consistent` (the newest image available in every member region, so the whole fleet runs one image). Update runs honour each cluster's planned maintenance windows, and a stage can tolerate a configured number of failures. For regulated estates, `Consistent` plus a staged strategy is the easy audit story: one image, one order, recorded runs.

**Resource placement is Kubernetes-native multi-cluster scheduling.** On the hub you create the resources you want everywhere, such as a namespace with its RBAC, quotas, and network policies, and a `ClusterResourcePlacement` (API `placement.kubernetes-fleet.io/v1`) that selects them and a policy for choosing clusters. `PickAll` places onto every member that matches an affinity, which suits platform components such as monitoring agents. `PickFixed` names clusters explicitly. `PickN` chooses a number of clusters using required or preferred affinity and topology spread constraints, for example spreading an application across regions. The default rollout strategy is a rolling update across clusters with `maxUnavailable` and a wait between clusters, and overrides let you vary a field per cluster, such as a replica count or a regional endpoint. A namespaced `ResourcePlacement` does the same within a namespace, which is how tenants can place their own resources without cluster-scoped rights. The placement engine is open source as KubeFleet, a CNCF sandbox project, so the same API can be run outside Azure.

**Managed fleet namespaces are the tenancy primitive.** With a hub, Fleet Manager can create a namespace on a chosen set of member clusters with resource quotas, network policies, and access assigned once for all of them. That turns "give team payments a namespace in prod-weu and prod-neu" into one object instead of a script per cluster.

**Where it overlaps with GitOps.** If you already run Argo CD or Flux with an ApplicationSet or Kustomization per cluster, you have a working placement mechanism. Fleet placement is worth it when you want placement decisions driven by cluster properties and labels, clusters that come and go without editing Git, and a Kubernetes API for "run this on three production clusters, spread by region". A common split is GitOps delivering to the hub, and Fleet placing from the hub to members; Fleet's own automated deployments feature (in preview) stages from Git to the hub. Pick one owner per resource, because two systems reconciling the same object on the same cluster will fight.

**The trade-offs.** The hub is a new critical dependency for placement; members keep running if it is unavailable, but you cannot change placement until it returns. A `PickAll` with a bad resource is fleet-wide blast radius, so use the rolling strategy and label-based rings rather than trusting a single apply. Update runs orchestrate upgrades but do not test your workloads; the stage wait only helps if something is watching SLOs during it. And some capabilities (multi-cluster networking, DNS-based load balancing, automated deployments, failure thresholds) are preview, so check status before designing around them.

**Who the user is.** The platform team uses update orchestration to keep dozens of clusters current without a spreadsheet. Product teams benefit indirectly (fewer upgrade surprises, consistent namespaces everywhere) and directly when you give them `ResourcePlacement` or managed namespaces to deploy across regions without learning each cluster.

## Example

```bash
# Fleet with a hub (needed for placement and managed namespaces)
az fleet create -g rg-platform-fleet -n fleet-prod -l westeurope \
  --enable-hub --enable-managed-identity

# Join members into rings via update groups; labels are what placement selects on
az fleet member create -g rg-platform-fleet -f fleet-prod -n aks-canary-weu \
  --member-cluster-id "$CANARY_WEU_ID" --update-group ring0 --labels environment=canary
az fleet member create -g rg-platform-fleet -f fleet-prod -n aks-prod-weu \
  --member-cluster-id "$PROD_WEU_ID" --update-group ring1 --labels environment=prod
az fleet member create -g rg-platform-fleet -f fleet-prod -n aks-prod-neu \
  --member-cluster-id "$PROD_NEU_ID" --update-group ring2 --labels environment=prod

# A reusable strategy: canary, soak for a day, then production region by region
cat > rings.json <<'EOF'
{
  "stages": [
    { "name": "canary", "groups": [{ "name": "ring0" }], "afterStageWaitInSeconds": 86400 },
    { "name": "prod-weu", "groups": [{ "name": "ring1" }], "afterStageWaitInSeconds": 21600 },
    { "name": "prod-neu", "groups": [{ "name": "ring2" }] }
  ]
}
EOF
az fleet updatestrategy create -g rg-platform-fleet -f fleet-prod -n rings --stages rings.json

# New Stable-channel versions trigger a run using that strategy, one image fleet-wide
az fleet autoupgradeprofile create -g rg-platform-fleet -f fleet-prod -n stable-rings \
  --channel Stable --node-image-selection Consistent \
  --update-strategy-id "$(az fleet updatestrategy show -g rg-platform-fleet -f fleet-prod -n rings --query id -o tsv)"
```

```yaml
# On the hub: place the checkout namespace (and everything in it) onto two
# production clusters, spread across regions, one cluster at a time.
apiVersion: placement.kubernetes-fleet.io/v1
kind: ClusterResourcePlacement
metadata:
  name: checkout
spec:
  resourceSelectors:
    - group: ""
      version: v1
      kind: Namespace
      name: team-payments-checkout
  policy:
    placementType: PickN
    numberOfClusters: 2
    affinity:
      clusterAffinity:
        requiredDuringSchedulingIgnoredDuringExecution:
          clusterSelectorTerms:
            - labelSelector:
                matchLabels:
                  environment: prod
    topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: fleet.azure.com/location
        whenUnsatisfiable: DoNotSchedule
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      unavailablePeriodSeconds: 300
```

```text
What a version release looks like with this fleet:

  AKS publishes a new Stable patch
    -> auto-upgrade profile creates an update run from strategy "rings"
    -> canary (ring0) upgraded; 24h soak while SLO alerts watch it
    -> prod-weu (ring1) upgraded inside its maintenance window; 6h soak
    -> prod-neu (ring2) upgraded
  Any failure stops the run before the next stage. The run history is the
  audit record of which cluster ran which version, when.
```

## Interview tips

- Separate the two capabilities clearly: update orchestration (works without a hub) and resource placement (needs the hub). Mention that adding a hub is one-way.
- Walk through groups, stages, strategies, runs, and auto-upgrade profiles in order; it shows you have designed rings rather than read a feature list.
- `Consistent` versus `Latest` node image selection is a precise detail that matters for multi-region audit and debugging.
- Know `PickAll`, `PickFixed`, and `PickN`, and give one use for each: platform agents, named clusters, and region-spread applications.
- Address the GitOps overlap directly and propose a single owner per resource.
- Be honest about blast radius and preview features. For the general pattern beyond Azure, see [How do you upgrade a fleet of clusters without breaking tenants?](../kubernetes-platform/how-do-you-upgrade-a-fleet-of-clusters-without-breaking-tenants.md) and [How do you keep platform components consistent across many clusters?](../kubernetes-platform/how-do-you-keep-platform-components-consistent-across-many-clusters.md).

---

[⬅ Back to Azure Platform Engineering](./README.md) · [All topics](../README.md)
