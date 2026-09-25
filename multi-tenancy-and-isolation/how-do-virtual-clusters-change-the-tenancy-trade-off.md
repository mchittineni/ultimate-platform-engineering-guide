---
title: "How do virtual clusters change the tenancy trade-off?"
id: 47
category: "Multi-Tenancy and Isolation"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - multi-tenancy-and-isolation
  - interview-questions
---

# How do virtual clusters change the tenancy trade-off?

**Short answer:** A virtual cluster gives a tenant its own Kubernetes API server, datastore, CRDs, and RBAC, running as workloads inside a namespace of a shared host cluster, while the tenant's pods are synced down and scheduled onto the host's nodes. That splits the old namespace-versus-cluster choice in two: tenants get control-plane isolation and cluster-admin freedom at close to namespace cost, but they still share nodes, the kernel, and the host's networking. It is the right answer for "we need cluster-scoped resources", not for "we run untrusted code".

## Detail

**The gap virtual clusters fill.** With plain namespaces, every tenant shares one API server and one set of cluster-scoped objects, so a team that needs its own CRDs, admission webhooks, operators, or a different set of cluster roles cannot have them without affecting everyone. The traditional answer was a dedicated cluster, with its fixed control-plane cost and a full copy of every platform component. Virtual clusters sit between the two.

**How the mechanism works.** Using vCluster as the reference implementation:

- The **control plane** - an upstream Kubernetes API server, controller manager, and a backing store (embedded SQLite by default, or etcd or an external database) - runs as a pod in a host namespace.
- The tenant talks to that API server with its own kubeconfig and is cluster-admin _inside_ it. It can install CRDs, create namespaces, and bind roles.
- A **syncer** copies the low-level objects that actually need to run - pods, and the services, config maps, secrets, and volumes they depend on - into the single host namespace, with rewritten names. The host scheduler places them on shared nodes.
- Higher-level objects - Deployments, CRDs and custom resources, the tenant's RBAC - stay in the virtual control plane and never touch the host API.

So the host cluster sees a namespace full of pods; the tenant sees a whole cluster.

**What changes in the trade-off:**

| Concern                                | Namespace | Virtual cluster                   | Dedicated cluster                           |
| -------------------------------------- | --------- | --------------------------------- | ------------------------------------------- |
| Own CRDs, webhooks, cluster roles      | No        | Yes                               | Yes                                         |
| API server and etcd contention         | Shared    | Isolated per tenant               | Isolated                                    |
| Tenant can pick its Kubernetes version | No        | Within supported skew of the host | Yes                                         |
| Kernel and node isolation              | Shared    | Shared (unless dedicated nodes)   | Separate                                    |
| Network, CNI, and node-level agents    | Shared    | Shared host networking and policy | Separate                                    |
| Fixed cost per tenant                  | Near zero | One small control-plane pod set   | Control plane + nodes + full platform stack |
| Create and delete time                 | Seconds   | Typically under a minute or two   | Many minutes                                |

**Where it is especially strong.** Ephemeral environments for pull requests or CI, where a throwaway full cluster is too slow and too expensive. Platform and operator teams who need to test CRD and controller changes without a real cluster. Tenants who legitimately need cluster-admin semantics - installing their own operator - that the platform does not want to grant on the host. And control-plane blast radius: a tenant's runaway controller hammers only its own API server.

**Where it does not help.** Pods still run on the host's nodes, share the kernel, and are subject to the host's CNI. A container escape is still a host compromise, so untrusted code still needs sandboxed runtimes or dedicated nodes. Recent vCluster releases can attach dedicated "private nodes" to a virtual cluster, which moves it much closer to a real cluster - and closer to a real cluster's cost.

**The platform has to enforce the boundary on the host.** Because the tenant is admin inside the virtual cluster, host-side controls do the real isolation: a ResourceQuota and LimitRange on the host namespace, Pod Security enforcement on synced pods, default-deny network policy, and restrictions on what the syncer may sync (for example, no hostPath volumes and no privileged pods). A virtual cluster with no host-side policy gives the tenant more power, not more isolation.

**Operational costs to name.** Each virtual control plane is a stateful workload that needs backups if it holds anything durable, version management within the host's supported skew, and observability. Debugging crosses two API servers, and name rewriting in the host can confuse tooling. Other approaches in the same space include hosted-control-plane projects such as Kamaji and k0smotron, and namespace-grouping tools such as Capsule, which extend soft tenancy rather than virtualising the API.

**Who the user is.** Tenant teams who want cluster-level autonomy - often platform-adjacent or data teams running operators - and any team using per-branch preview environments. For the platform team, the saving is not having to run dozens of real clusters, each with its own upgrade cycle and component stack.

## Example

```yaml
# vcluster.yaml - a tenant virtual cluster, with host-side guardrails.
# Deployed with: vcluster create team-data -n vc-team-data -f vcluster.yaml
controlPlane:
  distro:
    k8s:
      enabled: true # upstream Kubernetes; default store is embedded SQLite
sync:
  toHost:
    ingresses:
      enabled: false # tenants expose services through the platform's Gateway
  fromHost:
    storageClasses:
      enabled: true # tenants see the host's storage classes, cannot add their own
policies:
  podSecurityStandard: restricted # enforced on the pods synced to the host
  resourceQuota:
    enabled: true # applied to the host namespace, bounds every synced pod
    quota:
      requests.cpu: "20"
      requests.memory: 40Gi
      count/pods: "150"
  limitRange:
    enabled: true
  networkPolicy:
    enabled: true # isolates this virtual cluster's pods from other tenants
```

```text
The same workload, seen from both sides.

Tenant (inside the virtual cluster):
  $ kubectl get crd | grep sparkoperator
  sparkapplications.sparkoperator.k8s.io     # installed by the tenant itself
  $ kubectl get pods -n pipelines
  NAME            READY   STATUS
  ingest-driver   1/1     Running

Platform (host cluster):
  $ kubectl get pods -n vc-team-data
  NAME                                      READY   STATUS
  team-data-0                               1/1     Running   # virtual control plane
  ingest-driver-x-pipelines-x-team-data     1/1     Running   # synced, renamed pod
  $ kubectl get crd | grep sparkoperator
  (nothing - the CRD never reached the host)
```

## Interview tips

- Explain the mechanism in one breath: separate API server and datastore per tenant, pods synced to the host and scheduled on shared nodes.
- Frame it as splitting the trade-off: control-plane isolation without node or kernel isolation. That is the precise claim, and overstating it is the common mistake.
- Give the fitting use cases - tenants needing CRDs or operators, ephemeral preview environments - and the non-fitting one, untrusted code.
- Stress that the host must still enforce quota, Pod Security, and network policy on the synced pods; admin inside the virtual cluster is not admin on the host.
- It pairs naturally with [When do you give a tenant its own cluster instead of a namespace?](./when-do-you-give-a-tenant-its-own-cluster-instead-of-a-namespace.md) - a virtual cluster is often the answer that avoids a real one.

---

[⬅ Back to Multi-Tenancy and Isolation](./README.md) · [All topics](../README.md)
