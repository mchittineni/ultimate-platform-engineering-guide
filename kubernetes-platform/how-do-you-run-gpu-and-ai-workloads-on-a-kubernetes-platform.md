---
title: "How do you run GPU and AI workloads on a Kubernetes platform?"
id: 60
category: "Kubernetes Platform"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - kubernetes-platform
  - interview-questions
---

# How do you run GPU and AI workloads on a Kubernetes platform?

**Short answer:** Treat GPUs as a scarce, shared, expensive pool with its own node lifecycle, its own admission, and its own economics. Concretely: dedicated tainted GPU node pools with the driver stack managed by an operator, device allocation through the device plugin or - increasingly - Dynamic Resource Allocation, a queueing layer such as Kueue so training jobs wait for quota instead of fighting for nodes, sharing mechanisms (MIG, time-slicing) for small workloads, and inference served behind a model-aware gateway. The platform's job is to turn "I need two H100s for six hours" into a request a researcher can make without knowing any of this, and to keep utilisation high enough to justify the hardware.

## Detail

**GPUs break the usual Kubernetes assumptions.** CPU and memory are divisible, overcommittable, and cheap enough to waste a little. A GPU is none of those: it is allocated as a whole device by default, cannot be overcommitted, costs many times a general node, and is often capacity-constrained in the cloud region you want. A training job that needs eight GPUs is useless with seven. Every design decision below follows from that.

**The node layer.** GPU nodes need a kernel driver, a container runtime hook, a device plugin, and monitoring - and the versions must line up with the CUDA version the workloads expect. The NVIDIA GPU Operator (or the managed equivalent from your cloud provider) installs and upgrades that stack as DaemonSets, including the DCGM exporter for utilisation and health metrics. GPU pools should be tainted so ordinary Pods never land on them, scale to zero when idle, and be split by accelerator type, because an inference service sized for one GPU model should not silently land on another - see [node pools and scheduling](./how-do-you-design-node-pools-and-scheduling-for-mixed-workloads.md).

**Allocation: device plugin versus DRA.** The classic device plugin advertises an extended resource such as `nvidia.com/gpu: 8`, and a Pod requests an integer count. It is simple and universally supported, but it cannot express "a GPU with at least 80GB of memory" or "two GPUs on the same NVLink domain", and sharing is configured node-wide. Dynamic Resource Allocation, GA in Kubernetes 1.34, replaces the integer with a claim: vendors publish devices with attributes through `ResourceSlice`s, the platform defines `DeviceClass`es, and a workload's `ResourceClaim` selects devices with CEL expressions. For a platform this is the more expressive long-term interface, and it is where GPU sharing and partitioning are heading; the device plugin remains the pragmatic default where drivers or managed offerings do not yet support DRA.

**Sharing, for the many small workloads.** Most notebooks, small inference models, and CI jobs do not need a whole GPU. Three mechanisms exist, with different isolation:

| Mechanism    | How it works                                | Isolation                      | Good for                      |
| ------------ | ------------------------------------------- | ------------------------------ | ----------------------------- |
| MIG          | Hardware partitions a GPU into fixed slices | Strong: memory and compute     | Multi-tenant inference        |
| Time-slicing | Several Pods take turns on one GPU          | None: shared memory, no limits | Notebooks, dev, light jobs    |
| MPS          | Concurrent kernels from several processes   | Partial: limits, shared faults | Many small inference replicas |

Time-slicing is the one to be careful with in a multi-tenant cluster: one tenant can exhaust the memory of a GPU another tenant is using.

**Queueing is the piece most platforms add too late.** Without it, a training job either gets all its GPUs or sits with Pods half-scheduled, holding some GPUs while waiting for the rest - and two such jobs can deadlock each other. Kueue sits in front of the scheduler: jobs are created suspended, Kueue admits them only when the whole job fits within the team's quota, and releases them all at once. It adds per-team quotas with borrowing between teams, priorities and preemption, and fair sharing, which is how a platform answers "the research team hogged every GPU all weekend". It works with Jobs, JobSets, Kubeflow training jobs, RayJobs, and more, and it can trigger cluster autoscaling for the admitted job rather than for individual Pods.

**Inference is a different workload.** Training is batch: throughput, checkpointing, preemption tolerance. Inference is a latency-sensitive service with unusual properties: slow cold starts (loading tens of gigabytes of weights), request cost that varies enormously by prompt length, and a load signal - queue depth, KV-cache utilisation - that CPU metrics do not capture. Model servers such as vLLM handle batching; KServe or similar provides the serving abstraction; and the Gateway API Inference Extension adds an `InferencePool` backend with an endpoint picker that routes each request to the replica with capacity, rather than round-robin. Autoscale on queue depth or tokens in flight, not CPU.

**The economics are part of the design.** Idle GPUs are the most expensive waste on the platform. Report GPU utilisation per team from DCGM, reclaim idle notebook GPUs after a timeout, run interruptible training on spot capacity with frequent checkpoints, and attribute GPU hours explicitly rather than folding them into shared cost - see [idle platform cost](../platform-finops/how-do-you-find-and-remove-idle-platform-cost.md).

**The user.** Researchers and ML engineers want to say "this job needs four GPUs of this class for this long" and get an honest queue position. Application teams want a model endpoint. Neither should learn taints, MIG profiles, or driver versions.

## Example

```yaml
# Kueue: a team's GPU quota, and the flavour that maps to a tainted node pool.
apiVersion: kueue.x-k8s.io/v1beta2
kind: ResourceFlavor
metadata: { name: h100 }
spec:
  nodeLabels: { platform.example.com/accelerator: nvidia-h100 }
  tolerations:
    - { key: nvidia.com/gpu, operator: Exists, effect: NoSchedule }
---
apiVersion: kueue.x-k8s.io/v1beta2
kind: ClusterQueue
metadata: { name: research }
spec:
  namespaceSelector: {}
  resourceGroups:
    - coveredResources: ["cpu", "memory", "nvidia.com/gpu"]
      flavors:
        - name: h100
          resources:
            - { name: cpu, nominalQuota: 384 }
            - { name: memory, nominalQuota: 3Ti }
            - { name: nvidia.com/gpu, nominalQuota: 32 } # 4 nodes x 8
---
apiVersion: kueue.x-k8s.io/v1beta2
kind: LocalQueue
metadata: { name: training, namespace: team-research }
spec:
  clusterQueue: research
---
# The researcher's job: a queue name and a GPU count. Kueue admits it only
# when all 8 GPUs fit in quota, so it never holds half its GPUs while waiting.
apiVersion: batch/v1
kind: Job
metadata:
  name: finetune-ranker
  namespace: team-research
  labels: { kueue.x-k8s.io/queue-name: training }
spec:
  suspend: true # Kueue unsuspends on admission
  parallelism: 1
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: train
          image: registry.example.com/team-research/ranker-train:0.9.2
          resources:
            limits: { nvidia.com/gpu: 8 } # extended resources: limit implies request
            requests: { cpu: "64", memory: 512Gi }
```

```yaml
# The DRA alternative: claim a device by attribute instead of by count.
apiVersion: resource.k8s.io/v1
kind: ResourceClaimTemplate
metadata: { name: large-gpu, namespace: team-search }
spec:
  spec:
    devices:
      requests:
        - name: gpu
          exactly:
            deviceClassName: gpu.nvidia.com
            selectors:
              - cel:
                  expression: device.capacity["gpu.nvidia.com"].memory.compareTo(quantity("80Gi")) >= 0
---
apiVersion: v1
kind: Pod
metadata: { name: embed-server, namespace: team-search }
spec:
  resourceClaims:
    - { name: gpu, resourceClaimTemplateName: large-gpu }
  containers:
    - name: server
      image: vllm/vllm-openai:v0.10.1
      resources:
        claims: [{ name: gpu }]
```

## Interview tips

- Open with why GPUs are different: whole-device allocation, no overcommit, high cost, scarce capacity. The rest of the design follows from those properties.
- Name the all-or-nothing problem for distributed training and Kueue as the answer - quota-based admission of whole jobs, borrowing, and fair sharing. It is the detail that shows real experience.
- Compare the device plugin's integer count with DRA claims and CEL selectors (GA in 1.34), and be honest that the device plugin is still the pragmatic default in many clusters.
- Know the three sharing mechanisms and their isolation, and flag time-slicing as unsafe for untrusted multi-tenancy.
- Separate training from inference: batch and checkpoints versus latency, cold starts, and scaling on queue depth. Close on utilisation reporting - idle GPUs are the platform's most expensive failure.

---

[⬅ Back to Kubernetes Platform](./README.md) · [All topics](../README.md)
