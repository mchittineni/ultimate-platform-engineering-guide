---
title: "How do you choose between GKE, GKE Autopilot, and Cloud Run?"
id: 178
category: "GCP Platform Engineering"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - gcp-platform-engineering
  - interview-questions
---

# How do you choose between GKE, GKE Autopilot, and Cloud Run?

**Short answer:** Cloud Run for request-driven and event-driven containers where you want scale to zero and no cluster at all; GKE Autopilot when you need the Kubernetes API but not node management; GKE Standard when you genuinely need control over nodes - GPUs with specific drivers, particular machine families, DaemonSets that must run everywhere, or unusual scheduling. Autopilot should be the default Kubernetes choice, and Standard should require a reason.

## Detail

**Autopilot versus Standard is the more interesting half of this question.** Autopilot is real GKE with the same API: you get Deployments, custom resources, admission control, and the whole ecosystem. What you do not get is node management - Google provisions and patches nodes, you are billed for Pod resource requests rather than nodes, and various node-level operations are restricted. For a platform team the appeal is direct: a large share of Kubernetes operational burden is node pools, upgrades, and capacity, and Autopilot removes most of it while keeping the API that your platform machinery depends on.

**What Autopilot restricts, and these are the reasons to choose Standard:**

| Need                                       | Autopilot                      |
| ------------------------------------------ | ------------------------------ |
| Privileged containers, host namespaces     | Restricted                     |
| Arbitrary DaemonSets on every node         | Constrained                    |
| Specific machine families or custom images | Limited control                |
| Node-level agents needing host access      | Often blocked                  |
| GPUs with particular driver requirements   | Supported but with constraints |
| Very fine-grained bin-packing control      | Google decides placement       |

Notably, several of those are exactly what third-party security and observability agents want. Checking whether your required agents run on Autopilot is the practical first step, and it is what most often forces Standard. Two developments soften this: the Autopilot partner programme lets approved vendors ship allowlists so their privileged agents install on Autopilot, and since late 2025 Standard clusters can run workloads in Autopilot mode through compute classes, so the choice is increasingly made per workload rather than per cluster.

**Cloud Run is more capable than people assume.** It runs any container listening on a port, scales to zero, supports concurrency greater than one per instance, runs batch work as jobs and pull-based background consumers as worker pools (GA in April 2026), attaches GPUs to services and jobs, reaches the VPC through Direct VPC egress (preferred over Serverless VPC Access connectors), and supports per-service identity. Cloud Functions is now Cloud Run functions, so functions are simply another way of deploying to Cloud Run. For ordinary HTTP services and event consumers it is a smaller operational surface than any cluster, and its scale-to-zero behaviour makes it very cheap for non-production and internal tools.

**The distinguishing question is whether you need the Kubernetes API.** Not whether you need containers - all three run containers. If your platform is built on custom resources, admission control, Config Connector, or GitOps reconciliation of arbitrary resources, you need a cluster. If your workloads are services and workers and the platform provides its own abstractions, Cloud Run may cover them entirely.

**Scale to zero is the cost differentiator.** Cloud Run scales to zero; Autopilot bills for running Pods so an idle service still costs; Standard bills for nodes whether occupied or not. For preview environments and internal tools this difference is large enough to decide the answer on its own.

**A mixed estate is normal, and often the right answer on GCP:** Cloud Run for most services, one Autopilot cluster for the platform's own control plane and anything needing the Kubernetes API, and Standard only where an agent or hardware requirement forces it. The platform interface should hide which one a workload uses.

**Watch the cold start and concurrency questions on Cloud Run.** Cold starts matter for latency-sensitive paths, mitigated with minimum instances - which also removes the scale-to-zero saving, so it is a trade rather than a fix. And concurrency above one means your container must be safe to handle simultaneous requests, which is an application property rather than a configuration.

## Example

```text
Choosing, in the order that eliminates options fastest:

  Do you need the Kubernetes API itself - CRDs, admission control, operators,
  Config Connector, GitOps reconciliation of arbitrary resources?
    no  -> CLOUD RUN. Scale to zero, no cluster, per-service identity.
    yes -> continue

  Do you need node-level control - privileged agents, DaemonSets everywhere,
  specific machine families, custom node images, particular GPU drivers?
    no  -> GKE AUTOPILOT. Real GKE API, no node management. THE DEFAULT.
    yes -> GKE STANDARD, and record why.

  Practical first check that decides it more often than anything else:
    do your required security and observability agents run on Autopilot?
    Several want host access, which Autopilot restricts. Verify before designing.
```

```text
A defensible GCP estate for 160 services:

  Cloud Run ..................................... 118 services
    HTTP services, event consumers, scheduled jobs. Every non-production
    instance scales to zero - which is most of the cost saving.

  GKE Autopilot ................................. 38 services + the control plane
    justification: the platform runs Config Connector, Config Sync, and Kyverno,
    which need the Kubernetes API. Autopilot removes node pools, node upgrades,
    and capacity planning while keeping that API.

  GKE Standard .................................... 4 services
    justification: GPU inference needing a specific driver version, plus a
    vendor security agent that requires host-level access. Each recorded as an
    exception with a review date.

  Note what changed the operational load: the platform team upgrades ONE
  Autopilot cluster's workloads rather than managing node pools across a fleet.
```

```yaml
# Cloud Run: scale to zero, no secrets, private egress, per-service identity.
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: checkout
  annotations:
    run.googleapis.com/ingress: internal-and-cloud-load-balancing
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "0" # scale to zero
        autoscaling.knative.dev/maxScale: "100"
        run.googleapis.com/vpc-access-egress: private-ranges-only
        # Direct VPC egress into a Shared VPC subnet - full resource names.
        run.googleapis.com/network-interfaces: '[{"network":"projects/vpc-host-prod/global/networks/shared-prod","subnetwork":"projects/vpc-host-prod/regions/europe-west1/subnetworks/snet-eu-west1-run"}]'
    spec:
      # Per-service identity - federated, no key
      serviceAccountName: sa-checkout@checkout-prod.iam.gserviceaccount.com
      containerConcurrency: 80 # >1 requires the app to be concurrency-safe
      containers:
        - image: europe-docker.pkg.dev/artifacts/example/checkout@sha256:9f2c8b1d...
          resources: { limits: { cpu: "1", memory: 512Mi } }
          env:
            - name: DB_HOST # IAM database auth - no password
              value: "10.42.0.14"
```

```text
The cold-start trade, stated honestly:

  minScale: 0    cheapest; first request after idle pays a cold start
  minScale: 1+   no cold start; the scale-to-zero saving is gone

  This is a trade, not a fix. For internal tools and preview environments,
  minScale 0 and an occasional cold start is obviously correct. For a
  latency-sensitive customer path, minScale 1+ means Cloud Run's cost advantage
  largely disappears and the comparison against a cluster changes.
```

## Interview tips

- Recommending Autopilot as the default Kubernetes choice, with Standard requiring a reason, is the current and defensible position - and it directly reduces the operational burden a platform team carries.
- Be specific about what Autopilot restricts, and note that several restrictions collide with third-party agents that want host access. Suggesting that as the first practical check reads as experience.
- The distinguishing question is whether you need the Kubernetes API, not whether you need containers. That reframing is what makes the answer crisp.
- Scale to zero as the cost differentiator, especially for preview environments and internal tools, is concrete and often decisive.
- State the cold-start trade honestly: minimum instances remove cold starts and also remove the cost advantage. Presenting it as a trade rather than a fix is more credible.
- Cloud Run concurrency above one being an application property rather than a setting is a good precise detail.
- Close on the mixed estate with recorded exceptions, and on the platform interface hiding which runtime a workload uses.

---

[⬅ Back to GCP Platform Engineering](./README.md) · [All topics](../README.md)
