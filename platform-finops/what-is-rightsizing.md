---
title: "What is rightsizing?"
id: 227
category: "Platform FinOps"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-finops
  - interview-questions
---

# What is rightsizing?

**Short answer:** Rightsizing is matching the resources you pay for to the resources a workload actually needs - a smaller or different instance type for a virtual machine, or lower CPU and memory requests for a Kubernetes container. You measure real usage over a representative period, compare it with what is provisioned, and change the size while keeping enough headroom for peaks. It is usually the largest optimisation available, and the reason it is hard is not the analysis but getting the change made safely across hundreds of services.

## Detail

**Why over-provisioning happens.** Engineers size a service before it has traffic, pick a generous number to be safe, and never revisit it. Nobody is paged for a service that uses 10% of what it asked for, so the waste is silent. Multiply that across an estate and the gap between provisioned and used capacity is often the biggest single line of avoidable spend.

**What you are sizing depends on the platform:**

| Where             | What you pay for                        | What to rightsize                 |
| ----------------- | --------------------------------------- | --------------------------------- |
| Virtual machines  | The instance type, while it runs        | Instance family and size          |
| Kubernetes        | Nodes, which are filled by pod requests | Container CPU and memory requests |
| Managed databases | The provisioned instance or capacity    | Instance class, provisioned IOPS  |
| Serverless        | Memory setting multiplied by duration   | Memory configuration              |

In Kubernetes the key idea is that a **request reserves capacity whether or not it is used**. The scheduler packs pods onto nodes by their requests, so a container requesting 2 CPU and using 0.2 still occupies 2 CPU of a node you pay for. Rightsizing requests is what lets the cluster autoscaler or Karpenter run fewer nodes.

**The method.** Collect usage over a period that includes the workload's real peaks - at least a couple of weeks, and a month-end if the service has one. Use a high percentile (p95 or p99) rather than the average, because averages hide the peaks that cause throttling and out-of-memory kills. Add headroom, then compare with the current setting. Memory deserves more caution than CPU: too little CPU makes a container slow, too little memory gets it killed.

**Tools do the measurement for you.** AWS Compute Optimizer, Azure Advisor, and Google Cloud's recommenders produce instance recommendations from usage. In Kubernetes the Vertical Pod Autoscaler (VPA) watches usage and produces request recommendations; run in `Off` mode it only recommends, which is the safe starting point. Kubernetes 1.35 made in-place pod resize generally available, so requests can change without recreating the pod, and VPA's `InPlaceOrRecreate` mode uses it - which makes automatic rightsizing much less disruptive than it used to be.

**The trade-offs.** Rightsizing too aggressively removes the headroom that absorbs traffic spikes and node failures, and a workload that was fine becomes flaky. Rightsizing interacts with horizontal autoscaling: if the HPA scales on CPU utilisation, changing the request changes the utilisation percentage and therefore the replica count, so the two need to be tuned together. And recommendations only help if someone acts on them.

**Who does what on a platform.** The platform team collects the data, generates recommendations with the evidence attached, and makes the change easy - ideally a pull request against the service's configuration that the owning team can review and merge. For low-risk, low-tier workloads, the platform can apply changes automatically. The product team keeps the judgement about its own service, because it knows about the month-end batch or the launch next week that the metrics do not.

**Rightsizing also means changing shape, not just size.** Moving to a current instance generation, to Arm-based instances where the software supports it, or from a general-purpose family to a compute- or memory-optimised one can reduce cost more than shrinking the size.

## Example

```yaml
# Recommendation-only VPA: measures usage and suggests requests, changes nothing.
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: checkout-api
  namespace: team-payments
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: checkout-api
  updatePolicy:
    updateMode: "Off" # recommend only; "InPlaceOrRecreate" once trusted
  resourcePolicy:
    containerPolicies:
      - containerName: app
        minAllowed: { cpu: 100m, memory: 256Mi }
        controlledResources: ["cpu", "memory"]
```

```text
$ kubectl describe vpa checkout-api -n team-payments   (recommendation section)

  Container Name:  app
  Lower Bound:     cpu 180m   memory 410Mi
  Target:          cpu 350m   memory 620Mi
  Upper Bound:     cpu 900m   memory 1100Mi

The platform's recommendation PR to team-payments:

  checkout-api/app   current requests: cpu 2000m, memory 2Gi
                     p95 usage (28 days, incl. month-end): cpu 310m, memory 560Mi
                     proposed:         cpu 500m, memory 768Mi   (headroom added)
  effect: 6 replicas free ~9 CPU of reserved node capacity
  note:   HPA targets 70% CPU utilisation of the request - expect fewer
          replicas at the same load; review minReplicas with this change.
```

## Interview tips

- Define it as matching provisioned to needed, then explain the Kubernetes twist: requests reserve capacity even when unused, which is why rightsizing requests reduces node count.
- Say "high percentile, over a period that includes peaks" rather than "average usage". Averages are the classic mistake.
- Treat memory more cautiously than CPU and explain why - throttling versus being killed.
- Mention the HPA interaction; it shows you have done this in practice rather than read about it.
- Name the current state of the art: in-place pod resize is GA in Kubernetes 1.35 and VPA can use it, which makes automatic rightsizing viable for more workloads.
- Name the user: the platform generates the evidence and the pull request, the team keeps the judgement. See [How do you find and remove idle platform cost?](./how-do-you-find-and-remove-idle-platform-cost.md) for the wider waste picture.

---

[⬅ Back to Platform FinOps](./README.md) · [All topics](../README.md)
