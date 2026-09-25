---
title: "How do you manage EKS node capacity with Karpenter?"
id: 157
category: "AWS Platform Engineering"
difficulty: "Advanced"
tags:
  - platform-engineering
  - aws-platform-engineering
  - interview-questions
---

# How do you manage EKS node capacity with Karpenter?

**Short answer:** Karpenter watches for unschedulable Pods and provisions nodes shaped to fit them, choosing instance types from a broad set you allow rather than scaling fixed node groups. That gives better bin-packing, faster scale-up, and easier spot usage. In exchange you must configure disruption deliberately - consolidation will move your Pods - so pod disruption budgets, `do-not-disrupt` where appropriate, and a node expiry policy become load-bearing rather than optional.

## Detail

**How it differs from the cluster autoscaler.** The cluster autoscaler scales pre-defined node groups, so it can only add more of a shape you already chose - and a Pod that fits no group stays pending. Karpenter reads the pending Pods' actual requirements - CPU, memory, architecture, GPU, zone, topology constraints - and launches an instance that fits, from any type you have allowed. Fewer pre-decisions, better packing, and one fewer reason for Pods to sit pending.

**Consolidation is the feature and the risk.** Karpenter continuously looks for opportunities to run the same Pods on fewer or cheaper nodes, and acts by draining and replacing. That is where the cost saving comes from, and it means node churn is routine rather than exceptional. Workloads that cannot tolerate being moved need to say so, and workloads that can must have correct disruption budgets - because consolidation will exercise them far more often than a monthly cluster upgrade would.

**The controls that make it safe:**

| Control                          | What it does                                                  |
| -------------------------------- | ------------------------------------------------------------- |
| `disruption.consolidationPolicy` | Whether to consolidate on underutilisation or only when empty |
| `disruption.budgets`             | Limits how many nodes may be disrupted at once, and when      |
| `karpenter.sh/do-not-disrupt`    | Marks a Pod or node as not safe to move                       |
| `expireAfter`                    | Retires nodes by age - how you get patched AMIs in            |
| `terminationGracePeriod`         | Bounds how long a drain may block                             |
| Pod disruption budgets           | The workload's own protection during every drain              |

**Node expiry is how patching happens.** Setting `expireAfter` means nodes are replaced regularly, so a new AMI reaches the fleet without a separate rollout. This turns node currency from a project into a property, and it is one of the strongest reasons to adopt Karpenter in a platform. It also means your workloads must genuinely tolerate node replacement, which is a healthy forcing function.

**Allow a wide instance set, and constrain by requirement instead.** Restricting to two instance types defeats the purpose and makes spot capacity fragile. Allow many families and sizes, then express what actually matters - architecture, generation, capacity type, minimum resources - as requirements. Wide diversity is also what makes spot interruption manageable, because a shortage in one type is not a shortage everywhere.

**Spot works well here, with the usual conditions.** Karpenter can prefer spot and fall back to on-demand, and handles interruption notices by draining ahead of reclamation. It still needs disruption budgets, diversity across types and zones, and workloads that tolerate restarts. Express it in the platform interface as an `interruptible` property rather than making each team learn the mechanics.

**Separate node pools by purpose, not by team.** A small on-demand pool for platform components that must never be preempted or consolidated aggressively, a general pool, a spot pool for interruptible work, and a GPU pool. Teams get isolation from quotas and priority classes, not from their own node pool.

**Know the API generation you are reading.** Karpenter 1.x is GA and uses `karpenter.sh/v1` `NodePool` and `karpenter.k8s.aws/v1` `EC2NodeClass`; the older `Provisioner` and `AWSNodeTemplate` objects, and the `v1beta1` APIs that replaced them, are gone. Many blog posts and charts still show them, and they will not apply to a current cluster. Also know the managed alternative: **EKS Auto Mode** runs Karpenter for you with the same `NodePool` API but an AWS-owned `NodeClass` and node image, so if running Karpenter itself is the toil, that is the option to weigh - see [EKS Auto Mode](./what-is-eks-auto-mode-and-when-would-a-platform-use-it.md).

**Watch for the failure modes.** Pods requesting more than any allowed instance provides stay pending forever - alert on pending duration. Unsatisfiable disruption budgets block consolidation and node expiry, so nodes silently stop being replaced and drift out of patch currency. And workloads with long termination grace periods can hold up drains longer than expected.

## Example

```yaml
# NodePool: allow a wide instance set, constrain by requirement, and be explicit
# about disruption - because consolidation WILL move pods.
apiVersion: karpenter.sh/v1
kind: NodePool
metadata: { name: general }
spec:
  template:
    metadata:
      labels: { platform.example.com/pool: general }
    spec:
      nodeClassRef: { group: karpenter.k8s.aws, kind: EC2NodeClass, name: default }
      requirements:
        - { key: kubernetes.io/arch, operator: In, values: [amd64, arm64] }
        - { key: karpenter.sh/capacity-type, operator: In, values: [on-demand] }
        # Wide families and sizes - narrow lists defeat bin-packing and make
        # spot fragile. Constrain by generation, not by naming two types.
        - { key: karpenter.k8s.aws/instance-category, operator: In, values: [c, m, r] }
        - { key: karpenter.k8s.aws/instance-generation, operator: Gt, values: ["5"] }
        - { key: topology.kubernetes.io/zone, operator: In, values: [eu-west-1a, eu-west-1b, eu-west-1c] }
      # Node expiry is how patched AMIs reach the fleet - currency becomes a
      # property rather than a rollout project.
      expireAfter: 720h # 30 days
      terminationGracePeriod: 1h # bounds how long a drain may block
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 1m
    budgets:
      - nodes: "10%" # never churn more than a tenth at once
      - nodes: "0" # and never during business-hours peak
        schedule: "0 9 * * mon-fri"
        duration: 9h
  limits: { cpu: "2000", memory: 4000Gi } # a backstop against runaway provisioning
---
apiVersion: karpenter.sh/v1
kind: NodePool
metadata: { name: burst }
spec:
  template:
    spec:
      nodeClassRef: { group: karpenter.k8s.aws, kind: EC2NodeClass, name: default }
      taints:
        - { key: interruptible, value: "true", effect: NoSchedule }
      requirements:
        - { key: karpenter.sh/capacity-type, operator: In, values: [spot, on-demand] }
        - { key: karpenter.k8s.aws/instance-category, operator: In, values: [c, m, r] }
        - { key: karpenter.k8s.aws/instance-generation, operator: Gt, values: ["5"] }
      expireAfter: 168h
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 30s # batch work: consolidate aggressively
```

```yaml
# The workload side. Tier-1 gets a correct PDB from the platform; the stateful
# singleton opts out of movement entirely.
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: checkout
  namespace: team-payments
  annotations:
    platform.example.com/generated-from: "service/checkout:tier=1"
spec:
  minAvailable: 2 # never equal to replicas - that blocks every drain
  selector: { matchLabels: { app: checkout } }
---
apiVersion: apps/v1
kind: StatefulSet
metadata: { name: leader-election-singleton, namespace: team-data }
spec:
  template:
    metadata:
      annotations:
        # Consolidation must not move this. Explicit, and it means the node it
        # sits on will not be consolidated or expired - so it needs its own
        # patching plan, recorded as an exception.
        karpenter.sh/do-not-disrupt: "true"
```

```text
The failure modes to alert on - all of them are quiet:

  PENDING PODS THAT CAN NEVER SCHEDULE
    pod requests 96 CPU; no allowed instance type provides it
    -> pending forever. Alert on pending duration > 5m, not on "pods pending".

  UNSATISFIABLE PDB BLOCKING CONSOLIDATION AND EXPIRY
    deployment: 1 replica, PDB minAvailable: 1
    -> the node can never be drained, so it is never consolidated AND never
       expired. It silently ages out of patch currency.
    $ platform karpenter blocked-nodes
        ip-10-42-19-84   age 94d   expireAfter 30d   BLOCKED BY PDB team-ops/report-gen
        -> the node is 3x past its expiry. This is a security finding, not a
           capacity one.

  DO-NOT-DISRUPT ACCUMULATION
    12 pods annotated do-not-disrupt, 9 added during incidents and never removed
    -> each one pins a node out of the consolidation and patching cycle.
       Treat the annotation as an exception with an expiry.

  LONG TERMINATION GRACE PERIODS
    a 30-minute grace period turns every consolidation into a 30-minute drain
    -> bound it with terminationGracePeriod on the NodePool.
```

## Interview tips

- Lead with the mechanism difference: Karpenter shapes nodes to pending Pods rather than scaling pre-defined groups, so a Pod that fits no group is no longer a permanent pending Pod.
- Consolidation as both the benefit and the risk is the core of a senior answer. Node churn becomes routine, so disruption budgets stop being optional paperwork.
- `expireAfter` as the AMI patching mechanism is the most valuable platform-level insight - node currency becomes a property rather than a rollout project.
- "Allow a wide instance set and constrain by requirement" is the configuration advice that matters, and it is also what makes spot capacity resilient.
- The unsatisfiable pod disruption budget blocking both consolidation and expiry is the best failure mode to raise: it turns a capacity setting into a silent security finding, because the node stops being patched.
- Treating `do-not-disrupt` annotations as exceptions with expiries shows you have watched incident-time annotations accumulate.
- If asked about versions, say Karpenter 1.x with `karpenter.sh/v1` NodePools, and that Auto Mode is the AWS-operated variant of the same model.
- Node pools by purpose rather than by team connects back to the tenancy model - teams get isolation from quotas and priority, not their own nodes.

---

[⬅ Back to AWS Platform Engineering](./README.md) · [All topics](../README.md)
