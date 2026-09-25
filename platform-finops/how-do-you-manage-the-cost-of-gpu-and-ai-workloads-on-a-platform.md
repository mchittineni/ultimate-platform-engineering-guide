---
title: "How do you manage the cost of GPU and AI workloads on a platform?"
id: 236
category: "Platform FinOps"
difficulty: "Advanced"
tags:
  - platform-engineering
  - platform-finops
  - interview-questions
---

# How do you manage the cost of GPU and AI workloads on a platform?

**Short answer:** Treat GPUs as a scarce, pooled, quota-managed resource rather than something each team provisions for itself: acquire capacity centrally with the right mix of reservations, on-demand, and spot; share it through a queueing and quota layer such as Kueue with fair sharing and borrowing; slice devices where workloads are small; measure real GPU utilisation rather than allocation; and attribute cost per team and per unit of AI output - per training run, per thousand inferences, per million tokens. Model API spend is the other half of AI cost and needs the same treatment: routed through a platform gateway so it is attributable, budgeted, and cached.

## Detail

**Why GPU cost behaves differently.** A GPU node costs many times a general-purpose node, capacity for the newest accelerators is often unavailable on demand, and Kubernetes has traditionally allocated GPUs as whole integers - a pod asking for `nvidia.com/gpu: 1` gets an entire device even if it uses a fraction of it. The combination produces the characteristic failure: teams hoard nodes they struggled to obtain, allocation looks close to 100%, and actual GPU utilisation is low. Every idle GPU-hour is expensive, so the waste that is tolerable on CPU is not tolerable here.

**Capacity strategy is the first lever.** Different AI workloads want different purchase models:

| Workload                       | Shape                                  | Capacity model                                                         |
| ------------------------------ | -------------------------------------- | ---------------------------------------------------------------------- |
| Large training runs            | Many GPUs, days to weeks, schedulable  | Time-bound reservations (e.g. AWS Capacity Blocks for ML), commitments |
| Fine-tuning and experiments    | Bursty, interruptible with checkpoints | Spot with frequent checkpointing, on-demand fallback                   |
| Production inference           | Latency-sensitive, diurnal             | Committed baseline plus autoscaled on-demand; scale to zero off-peak   |
| Notebooks and interactive work | Long idle periods                      | Small or sliced GPUs, aggressive idle culling                          |

Buying this centrally matters even more than for CPU, because reservations for scarce accelerators are large, lumpy decisions that no single team can size.

**A queue in front of the pool.** Kueue, the Kubernetes SIG project for batch and AI queueing, admits jobs against quotas instead of letting them sit pending on the scheduler. A `ClusterQueue` gives each team a nominal GPU quota; queues in the same cohort can borrow each other's unused quota and have it reclaimed by preemption when the owner needs it back. This is the mechanism that stops hoarding: a team no longer needs to hold idle nodes to be sure of capacity, because its quota is guaranteed and borrowed capacity is returned. Kueue also handles all-or-nothing admission for distributed training, so a job that needs 32 GPUs does not hold 20 of them while waiting for the rest.

**Share the device when the workload is small.** Many inference and development workloads do not need a whole accelerator. Options, in increasing order of isolation: time-slicing (several pods share a GPU in turn, no memory isolation), NVIDIA MPS (concurrent kernels, limited isolation), and Multi-Instance GPU (MIG), which partitions supported GPUs into hardware-isolated slices with their own memory. Dynamic Resource Allocation (DRA), GA in Kubernetes 1.34, replaces the opaque integer with structured device requests - a workload can ask for a device with particular attributes or a partition - which makes sharing and precise placement a first-class scheduling concern rather than a node-label convention.

**Measure utilisation, not allocation.** Allocation tells you who holds a GPU; utilisation tells you whether it is doing anything. The NVIDIA DCGM exporter publishes per-GPU metrics such as `DCGM_FI_DEV_GPU_UTIL`, `DCGM_FI_PROF_GR_ENGINE_ACTIVE`, and `DCGM_FI_DEV_FB_USED`, labelled with the pod that holds the device. Joining those with ownership gives the report that actually changes behaviour: GPU-hours held versus GPU-hours active, per team and per workload. Low utilisation usually means a data-loading bottleneck, a notebook left running, an oversized inference replica, or batch sizes that do not fill the device.

**Attribute to a unit of AI output.** GPU-hours per team is the showback baseline. The more useful numbers are unit economics: cost per training run or per experiment, cost per thousand inferences, and cost per million tokens served. These let a team compare a self-hosted model against a model API on the same terms, and they show whether quantisation, batching, or a smaller model improved efficiency.

**Model APIs are the other AI bill.** Token-priced model APIs grow with usage rather than capacity, and are easy to call from anywhere with a key. Route them through a platform AI gateway that holds the provider credentials, attributes every request to a team and service, enforces budgets and rate limits, caches repeated prompts where the provider supports it, and can route cheap tasks to cheaper models. FOCUS 1.2 added pricing-currency columns that accommodate token and credit billing, which makes model API spend fit the same cost dataset as cloud spend.

**Who it serves.** ML engineers and data scientists get guaranteed quota and a simple way to submit a job without negotiating for nodes. Product teams calling models get a key-free, attributed gateway. The platform team owns capacity, the queue, the sharing configuration, and the utilisation data. Finance gets GPU spend explained in units it can reason about.

**The trade-offs.** Queueing adds latency to job start compared with owning dedicated nodes, so interactive and urgent work needs a priority path. Preemption requires workloads to checkpoint, which is engineering effort for the ML teams. Device sharing trades isolation and predictable performance for utilisation, and MIG profiles fragment capacity if chosen badly. Reservations for scarce accelerators can leave you paying for idle capacity if a project slips.

## Example

```yaml
# Kueue (v1beta2 API): a shared GPU pool with a guaranteed quota per team and
# borrowing within a cohort, so nobody needs to hoard nodes.
apiVersion: kueue.x-k8s.io/v1beta2
kind: ResourceFlavor
metadata:
  name: h100-reserved
spec:
  nodeLabels:
    node.kubernetes.io/instance-type: p5.48xlarge
    platform.example.com/capacity: reserved
---
apiVersion: kueue.x-k8s.io/v1beta2
kind: ClusterQueue
metadata:
  name: team-search-gpu
spec:
  cohortName: ml-shared
  namespaceSelector:
    matchLabels: { platform.example.com/team: team-search }
  queueingStrategy: BestEffortFIFO
  preemption:
    reclaimWithinCohort: Any # lenders get their quota back
    withinClusterQueue: LowerPriority
  resourceGroups:
    - coveredResources: ["cpu", "memory", "nvidia.com/gpu"]
      flavors:
        - name: h100-reserved
          resources:
            - { name: cpu, nominalQuota: 384 }
            - { name: memory, nominalQuota: 4Ti }
            - name: nvidia.com/gpu
              nominalQuota: 16 # guaranteed share of the reservation
              borrowingLimit: 16 # may borrow idle GPUs from the cohort
---
apiVersion: kueue.x-k8s.io/v1beta2
kind: LocalQueue
metadata:
  name: training
  namespace: team-search
spec:
  clusterQueue: team-search-gpu
# Jobs opt in with the label kueue.x-k8s.io/queue-name: training
```

```text
Monthly GPU report - allocation versus activity, per team.

  TEAM            GPU-HOURS HELD   GPU-HOURS ACTIVE*   UTIL   UNIT COST TREND
  team-search          9,420            7,630           81%   cost / training run  -18%
  team-ranking         6,110            2,080           34%   cost / 1k inferences +12%
  team-assistants      2,300            1,750           76%   cost / 1M tokens     -30%
  notebooks (all)      3,880              540           14%   -

  * DCGM_FI_PROF_GR_ENGINE_ACTIVE above 10%, sampled per minute, by holding pod

  Findings with fixes attached:
    team-ranking   inference replicas each hold a full H100 at low load
                   -> move to MIG slices; batch requests; scale to zero overnight
    notebooks      idle >60 min on 71% of sessions
                   -> cull after 30 min idle; default notebook to a 1g MIG slice
    model APIs     via the platform AI gateway: 22% of prompt tokens served from
                   cache; two services moved to a smaller model for classification
```

## Interview tips

- Open with why GPUs are different: expensive, scarce, and allocated as whole devices, which produces hoarding and low real utilisation.
- Match capacity models to workload shapes - reservations for large training, spot with checkpoints for experiments, committed baseline plus autoscaling for inference.
- Kueue with guaranteed quota, cohort borrowing, and preemption is the key mechanism; explain that it removes the incentive to hoard.
- Know the sharing options - time-slicing, MPS, MIG - and that DRA (GA in Kubernetes 1.34) makes device requests structured rather than an opaque integer.
- Insist on utilisation from DCGM rather than allocation, and on unit economics per training run, per inference, or per token.
- Do not forget model API spend: a platform AI gateway gives attribution, budgets, caching, and model routing.
- Name the users - ML engineers, product teams calling models, finance - and the trade-offs: queue latency, checkpointing effort, isolation versus utilisation. See [How do you use commitments and spot capacity on behalf of every team?](./how-do-you-use-commitments-and-spot-capacity-on-behalf-of-every-team.md) and [How do you design node pools and scheduling for mixed workloads?](../kubernetes-platform/how-do-you-design-node-pools-and-scheduling-for-mixed-workloads.md).

---

[⬅ Back to Platform FinOps](./README.md) · [All topics](../README.md)
