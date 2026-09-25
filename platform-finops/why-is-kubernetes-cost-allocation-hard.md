---
title: "Why is Kubernetes cost allocation hard?"
id: 228
category: "Platform FinOps"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-finops
  - interview-questions
---

# Why is Kubernetes cost allocation hard?

**Short answer:** The cloud bill charges for nodes, but teams run pods, and many teams' pods share the same nodes. The bill has no idea which namespace used which part of a machine, so the cost has to be reconstructed from cluster data: what each pod requested, what it actually used, how long it ran, and what the node cost at the time. Then you still have to decide what to do with idle capacity, the control plane, shared add-ons, storage, and network - none of which belong to one team. Tools such as OpenCost do the arithmetic; the hard part is agreeing the rules.

## Detail

**The mismatch at the root of it.** In a normal cloud account, one resource maps to one owner, and a tag says who. In a shared cluster, a single node might run pods from eight teams in an hour, and pods come and go every few minutes. The billing export says "this instance cost this much"; it cannot say "team-search used 30% of it". The allocation has to be computed inside the cluster.

**Requests or usage - the first decision.** A pod's request reserves capacity on a node, whether or not it is used. Its usage is what it actually consumed. Charging by usage looks fair but lets a team reserve a large amount and pay for little of it, pushing the cost of their reservation onto everyone else. Charging by requests reflects what the team took away from the pool and encourages accurate requests. The common compromise is to charge the **greater of request and usage** for each resource, which covers both over-requesting and pods that burst above their request.

**CPU and memory have to be priced separately.** A node is sold as a bundle, so you need a rule to split its cost into a price per CPU-hour and per GiB-hour. Tools use the provider's published ratios or a configurable split. A memory-heavy workload and a CPU-heavy workload on the same node should not pay the same.

**Idle capacity is the biggest argument.** Nodes are never 100% allocated: there is headroom for scaling, bin-packing gaps, and capacity kept for node failure. That idle share can be a large fraction of cluster cost. You can spread it across teams in proportion to their usage, or keep it as a platform cost. Keeping it on the platform's line is often better, because the platform chose the buffer size and is the only one who can shrink it.

**Everything else that is not a pod.** The managed control plane fee, system components (DNS, ingress or Gateway controllers, logging agents, the service mesh), persistent volumes, load balancers created by `Service` objects, and cross-zone traffic between pods all need a rule. Some attach cleanly to a namespace (a persistent volume claim has one); others are shared by definition.

**Discounts and spot pricing change the rate.** If nodes run on spot or are covered by a commitment, the real cost per CPU-hour is lower than the list price. Allocation should use the effective rate the organisation paid, otherwise teams see numbers that do not add up to the bill.

**Ownership has to come from somewhere.** Allocation groups by namespace, label, or both. If namespaces map cleanly to teams, it is easy. If one namespace hosts three teams' services, or labels are missing, the result is a large "unallocated" bucket. Enforcing an owner label at admission is what makes the output usable.

**The tools.** OpenCost, a CNCF project, runs in the cluster, reads Kubernetes and pricing data, and produces cost by namespace, label, controller, or pod. Cloud providers now offer native options too - AWS split cost allocation data for EKS adds pod-level cost to the Cost and Usage Report, GKE cost allocation adds namespace and label breakdowns to the billing export, and AKS has a cost analysis add-on.

**Who uses the result.** Product teams see a number for their namespaces in the portal or a monthly report, with the workings visible. The platform team owns the rules and the tooling and publishes how much is idle or unallocated. A number a team can reproduce is one it will act on.

## Example

```text
One node-hour, split three ways - the same data, three answers.

  node: m7i.2xlarge, 8 vCPU, 32 GiB, effective rate R per hour
  price split: CPU share 65%, memory share 35%

  POD                     CPU REQ   CPU USED   MEM REQ   MEM USED
  search-api  (search)      2.0       0.4       4 GiB     3 GiB
  indexer     (search)      1.0       1.8       8 GiB     6 GiB
  checkout    (payments)    2.0       1.6       6 GiB     5 GiB
  system pods (platform)    0.5       0.3       2 GiB     1 GiB
  unallocated               2.5        -       12 GiB      -

  BY USAGE ONLY        search-api looks cheap; its 2-CPU reservation is paid
                       by nobody, so the idle share grows
  BY REQUEST ONLY      indexer bursts to 1.8 CPU but pays for 1.0
  MAX(REQUEST, USAGE)  search-api pays for 2.0 CPU, indexer for 1.8 -
                       both behaviours are priced

  unallocated 2.5 CPU / 12 GiB: absorbed by the platform, shown as its own line
```

```bash
# OpenCost: seven days of cost aggregated by namespace, from its API.
curl -s "http://localhost:9003/allocation/compute?window=7d&aggregate=namespace" \
  | jq -r '.data[0] | to_entries[] | "\(.key)\t\(.value.totalCost)"' \
  | sort -t$'\t' -k2 -nr | head
```

```text
team-search       1843.27
team-payments     1611.90
__idle__           958.44   <- the idle share, reported separately
kube-system        212.05
```

## Interview tips

- Start from the mismatch: the bill charges for nodes, teams run pods, and pods share nodes. Everything else follows from that.
- The requests-versus-usage question is the one interviewers probe. "Greater of the two" is the standard answer, and explaining why shows you understand incentives.
- Say what you would do with idle capacity and why. Keeping it on the platform's line is a defensible position - see [How do you attribute shared platform cost to teams?](./how-do-you-attribute-shared-platform-cost-to-teams.md).
- Mention effective rates: allocation should reflect spot and commitment discounts so that the total reconciles to the bill.
- Name the tools - OpenCost and the providers' native pod-level allocation - but make the point that the tool does the arithmetic and the rules are the hard part.
- Ownership labels are a prerequisite; see [What is cost allocation tagging and why does it fail?](./what-is-cost-allocation-tagging-and-why-does-it-fail.md).

---

[⬅ Back to Platform FinOps](./README.md) · [All topics](../README.md)
