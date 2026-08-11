---
title: "How do you stop one tenant degrading another?"
id: 26
category: "Multi-Tenancy and Isolation"
difficulty: "Advanced"
tags:
  - platform-engineering
  - multi-tenancy-and-isolation
  - interview-questions
---

# How do you stop one tenant degrading another?

**Short answer:** Bound every shared resource a tenant can consume, and remember that this is not only CPU and memory - it includes the API server, etcd object counts, node-local disk and network, cloud API rate limits, and the observability pipeline. Requests and limits with a resource quota handle the obvious cases; the incidents that actually happen usually come from the resources nobody bounded.

## Detail

**Compute is the solved part.** Set requests so the scheduler reserves capacity, set limits so a runaway workload is capped, and understand the quality-of-service classes that result. Guaranteed pods - requests equal to limits - are evicted last; BestEffort pods with nothing set are evicted first. A tenant running BestEffort pods is the first casualty of anyone else's memory growth, which is why a platform should refuse to admit workloads without requests set.

**CPU throttling versus memory eviction.** A CPU limit throttles - the workload becomes slow, which shows up as latency rather than failure and can be maddening to diagnose. A memory limit kills - the container is OOMKilled immediately. The practical implication: CPU limits are often better omitted in favour of correct requests plus priority classes, while memory limits should always be set.

**The resources people forget, and where real incidents come from:**

| Shared resource        | Failure mode                                                     | Control                                        |
| ---------------------- | ---------------------------------------------------------------- | ---------------------------------------------- |
| API server             | One tenant's watch or list storm slows all reconciliation        | API priority and fairness; audit noisy clients |
| etcd                   | Thousands of objects or large objects degrade the cluster        | Object-count quotas; reject large annotations  |
| Node ephemeral disk    | One pod's logs fill the disk; node goes NotReady                 | `ephemeral-storage` requests and limits        |
| Node network           | A batch job saturates the NIC for co-located pods                | Bandwidth annotations, or separate node pools  |
| Cloud API rate limits  | Tenant's controller exhausts the shared quota                    | Per-tenant rate limiting; separate credentials |
| Observability pipeline | High-cardinality metrics degrade queries for everyone            | Cardinality limits, per-tenant ingest quotas   |
| Load balancers         | Each Service of type LoadBalancer is a cloud resource and a bill | Quota on `count/services.loadbalancers`        |
| PersistentVolumes      | Unbounded provisioning exhausts quota or budget                  | PVC count and storage quotas                   |

The first two rows are the distinctly platform-level ones, and they are why compute quotas alone do not make a cluster safely multi-tenant.

**Priority classes decide who loses.** Under real contention something must be evicted, and the default is effectively arbitrary. Map your service tiers to priority classes so a tier-3 batch job is preempted before a tier-1 API. Also set a preemption policy deliberately - a low-priority job that can preempt nothing is much safer.

**Pod disruption budgets protect availability during voluntary disruption**, which is the case you cause: node drains during upgrades and scaling events. Without one, a drain can remove every replica of a service at once. A platform should generate these by default from the tier rather than trusting each team to remember.

**Spread, or one node failure takes a tenant down.** Topology spread constraints or anti-affinity across zones and nodes should be a platform default, not an opt-in. Three replicas on one node is a common and entirely avoidable outage.

**Detection matters as much as prevention.** Track per-tenant consumption of each bounded resource, alert when a tenant approaches its quota rather than after it is refused, and keep a per-tenant view of API server request rates. Most noisy-neighbour incidents are visible for hours before anyone notices.

## Example

```yaml
# Requests/limits + quota is the baseline. The object counts and ephemeral
# storage lines are the ones that prevent the less obvious incidents.
apiVersion: v1
kind: ResourceQuota
metadata: { name: tenant-quota, namespace: team-search }
spec:
  hard:
    requests.cpu: "40"
    requests.memory: 80Gi
    limits.memory: 120Gi
    requests.ephemeral-storage: 40Gi # unbounded logs fill the node disk
    count/pods: "200" # protects etcd and the scheduler
    count/services.loadbalancers: "2" # each one is a cloud resource and a bill
    persistentvolumeclaims: "20"
---
apiVersion: v1
kind: LimitRange
metadata: { name: defaults, namespace: team-search }
spec:
  limits:
    - type: Container
      default: { cpu: 500m, memory: 512Mi } # limit if unspecified
      defaultRequest: { cpu: 100m, memory: 128Mi } # request if unspecified -
      # ensures no BestEffort pods
      max: { cpu: "8", memory: 16Gi } # no single giant pod
---
# Tier -> priority. Under contention, batch loses before the payments API does.
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata: { name: tier-1 }
value: 1000000
preemptionPolicy: PreemptLowerPriority
---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata: { name: tier-3-batch }
value: 1000
preemptionPolicy: Never # batch never evicts anyone else
```

```yaml
# API server fairness - the control that compute quotas cannot provide.
# A tenant controller with a list/watch storm is confined to its own share.
apiVersion: flowcontrol.apiserver.k8s.io/v1
kind: FlowSchema
metadata: { name: tenant-controllers }
spec:
  priorityLevelConfiguration: { name: tenant-workloads }
  matchingPrecedence: 1000
  distinguisherMethod: { type: ByUser } # one tenant cannot starve another
  rules:
    - subjects:
        - kind: ServiceAccount
          serviceAccount: { name: "*", namespace: "team-search" }
      resourceRules:
        - verbs: ["list", "watch", "get"]
          apiGroups: ["*"]
          resources: ["*"]
```

## Interview tips

- Answer the obvious part quickly - requests, limits, quotas, QoS classes - then spend your time on the resources people forget. That is where the differentiation is.
- API server and etcd contention is the answer that marks you as having operated a shared cluster. Naming API priority and fairness by name is strong.
- The CPU-throttles-versus-memory-kills distinction, and the conclusion that CPU limits are often better omitted, is a nuanced point interviewers like.
- Ephemeral storage from unbounded logs taking a node NotReady is a specific, real incident. Concrete failure modes beat lists of controls.
- Mention that pod disruption budgets and topology spread should be platform defaults generated from the tier - it connects isolation back to interface design.

---

[⬅ Back to Multi-Tenancy and Isolation](./README.md) · [All topics](../README.md)
