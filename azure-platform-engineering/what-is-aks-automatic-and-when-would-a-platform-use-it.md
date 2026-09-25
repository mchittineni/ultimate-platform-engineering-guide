---
title: "What is AKS Automatic and when would a platform use it?"
id: 167
category: "Azure Platform Engineering"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - azure-platform-engineering
  - interview-questions
---

# What is AKS Automatic and when would a platform use it?

**Short answer:** AKS Automatic is an AKS mode in which Azure presets and operates most of the cluster: node autoprovisioning (Karpenter-based) instead of node pools you size, managed system nodes, automatic Kubernetes and node image upgrades, Azure CNI Overlay with Cilium, Entra-based access, workload identity, and deployment safeguards in enforce mode. You still get the full Kubernetes API. A platform uses it when it wants Kubernetes as the interface but does not want to own node and cluster tuning, and it avoids it when it needs the knobs Automatic locks.

## Detail

**The model is "preconfigured, default, optional".** Microsoft sorts every AKS Automatic setting into three buckets. Preconfigured features are always on and cannot be changed: node autoprovisioning, managed system node pools, the Standard tier with its uptime SLA, automatic cluster upgrades on the `stable` channel, node image upgrades on the `NodeImage` channel, Azure RBAC for Kubernetes authorisation, API server VNet integration, workload identity with the OIDC issuer, image cleaner, a locked node resource group, and deployment safeguards with baseline Pod Security Standards. Default features are set for you but can be changed, such as the managed virtual network, managed Prometheus and Container Insights, and the ingress controller. Optional features you enable yourself, such as a custom virtual network or the Istio add-on.

**Node autoprovisioning replaces node pool design.** Instead of creating pools of fixed VM sizes and letting the cluster autoscaler add nodes of that size, node autoprovisioning (NAP) is AKS's managed Karpenter. It reads pending pods' requests, picks suitable VM sizes, creates nodes, and consolidates or removes underused ones. You influence it through Karpenter `NodePool` resources (`karpenter.sh/v1`) that constrain SKU families, capacity type, zones, and total limits. System components run on managed system node pools that AKS hosts and operates, so the cluster has no system pool for you to size or patch.

**Deployment safeguards change what teams can deploy.** This is the part that surprises people. Safeguards use the Azure Policy add-on (Gatekeeper underneath) and, in Automatic, run in `Enforce` mode, which you cannot switch to `Warn`. They reject `latest` image tags, require liveness and readiness probes, block privileged pods and host namespaces through baseline Pod Security Standards, and they mutate: a container with no resource requests gets default requests and limits, and a multi-replica Deployment with no anti-affinity gets a topology spread constraint added. You can exclude namespaces, but you cannot pick individual safeguards. For a platform this is useful, because it is a ready-made baseline, but workloads imported from elsewhere often need changes before they deploy.

**Upgrades become continuous.** Automatic clusters follow the `stable` channel (the latest patch of minor version N-1) and weekly node images, within any planned maintenance window you set. AKS stops an upgrade if it detects deprecated API usage. What you give up is the ability to hold a cluster on a chosen minor version for a long time; if your change process needs that, Automatic is the wrong fit.

**When a platform would use it:**

| Situation                                                   | Why Automatic fits                                                                 |
| ----------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| A small platform team serving many product teams            | Removes node sizing, system pool care, and upgrade scheduling from the team's work |
| Clusters per team or per application (cluster-as-a-service) | Each cluster is consistent by construction, so the fleet has fewer snowflakes      |
| Teams moving from Container Apps that outgrew it            | Keeps a managed feel while opening up CRDs, operators, and GitOps                  |
| A new platform with no legacy workloads                     | Safeguards' baseline is easier to adopt from the start than to retrofit            |

**When it is the wrong choice:**

- You need Windows node pools, a bring-your-own CNI, or kubenet. Automatic user nodes are Linux (Azure Linux or Ubuntu).
- You run privileged agents that need host access, such as some security or storage DaemonSets, and cannot exclude their namespaces.
- Your change process requires pinning a minor version or scheduling every upgrade by hand.
- You rely on writing to the node resource group directly, which Automatic locks.
- You already have a mature AKS Standard estate with its own tuned node pools, policies, and upgrade pipeline. Automatic's value there is smaller, and adopting it realistically means building new clusters and moving workloads, with all the safeguard fixes that implies.

**It does not remove the platform.** Automatic presets the cluster, not the product around it. Tenancy (namespaces, quotas, RBAC per team), identity wiring for each workload, ingress and DNS, GitOps, cost allocation, and fleet-wide policy beyond the safeguards remain platform work. The honest positioning is that Automatic moves the platform team up the stack: less time on nodes and upgrades, more on the golden path. Treat Automatic and Standard as two offerings in your cluster catalogue, with Automatic as the default and Standard as the escape hatch with a recorded reason.

**Current details worth knowing.** On new clusters from Kubernetes 1.36, the default ingress is Gateway API through the application routing add-on; older versions use the add-on's managed NGINX. Automatic also carries a pod readiness SLA covering scheduling and node provisioning. Both are signs Microsoft intends Automatic as the default way into AKS.

## Example

```bash
# Create an Automatic cluster. Most of what an AKS Standard create needs as
# flags is preconfigured.
az aks create \
  --resource-group rg-platform-aks \
  --name aks-team-checkout-prod \
  --sku automatic \
  --location westeurope

# Give a team namespace-scoped access through Entra and Azure RBAC
# (local accounts are not available on Automatic).
az role assignment create \
  --assignee-object-id "$TEAM_PAYMENTS_GROUP_ID" \
  --assignee-principal-type Group \
  --role "Azure Kubernetes Service RBAC Writer" \
  --scope "$(az aks show -g rg-platform-aks -n aks-team-checkout-prod --query id -o tsv)/namespaces/team-payments"
```

```yaml
# Constrain node autoprovisioning: general-purpose D/E families, on-demand,
# three zones, and a hard ceiling so a runaway workload cannot exhaust quota.
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: general
spec:
  limits:
    cpu: "400"
    memory: 1600Gi
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
  template:
    spec:
      nodeClassRef:
        group: karpenter.azure.com
        kind: AKSNodeClass
        name: default
      requirements:
        - key: karpenter.azure.com/sku-family
          operator: In
          values: ["D", "E"]
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["on-demand"]
        - key: topology.kubernetes.io/zone
          operator: In
          values: ["westeurope-1", "westeurope-2", "westeurope-3"]
```

```text
A workload imported from an older cluster, applied to Automatic:

  image: ghcr.io/example/checkout:latest        -> DENIED  (no latest tag)
  no livenessProbe / readinessProbe             -> DENIED  (probes required)
  securityContext.privileged: true              -> DENIED  (baseline PSS)
  no resources.requests                         -> MUTATED (defaults applied)
  replicas: 3, no anti-affinity                 -> MUTATED (topology spread added)

  Fix the first three in the service template once, and every team inherits it.
```

## Interview tips

- Explain it through the preconfigured, default, and optional split; it shows you know which parts are negotiable.
- Name node autoprovisioning as managed Karpenter and say that `NodePool` limits are how you keep it bounded.
- Deployment safeguards in enforce mode, including the mutations, are the practical detail that separates hands-on answers from brochure answers.
- Give real reasons not to use it (Windows nodes, privileged agents, version pinning, an existing tuned estate), not just reasons to.
- Close with the point that Automatic moves the platform up the stack rather than replacing it. Compare with GKE Autopilot in [How do you choose between GKE, GKE Autopilot, and Cloud Run?](../gcp-platform-engineering/how-do-you-choose-between-gke-gke-autopilot-and-cloud-run.md) and see [What does AKS manage for you, and what is left to the platform?](./what-does-aks-manage-for-you-and-what-is-left-to-the-platform.md).

---

[⬅ Back to Azure Platform Engineering](./README.md) · [All topics](../README.md)
