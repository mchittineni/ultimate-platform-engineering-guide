---
title: "Where does edge computing fit in a hybrid platform?"
id: 189
category: "Multi-Cloud and Hybrid Platforms"
difficulty: "Beginner"
tags:
  - platform-engineering
  - multi-cloud-and-hybrid-platforms
  - interview-questions
---

# Where does edge computing fit in a hybrid platform?

**Short answer:** Edge computing is running workloads close to where data is produced or consumed - in shops, factories, hospitals, vehicles, or telecom sites - instead of in a central cloud region or data centre. In a hybrid platform it is the outermost tier: many small sites, little or no local staff, unreliable connectivity, and constrained hardware. The platform's job there is to make hundreds of sites manageable as a fleet, using pull-based delivery that tolerates disconnection, and to keep each site able to run on its own when the link is down.

## Detail

**Why workloads go to the edge.** Four reasons recur:

- **Latency.** A vision model checking products on a production line cannot wait for a round trip to a cloud region.
- **Bandwidth.** Cameras and sensors produce more data than it makes sense to ship; process locally and send summaries.
- **Autonomy.** A shop's tills must keep working when the internet does not.
- **Residency or safety.** Some data must not leave the site, and some control systems must not depend on an external network.

**Where it sits in the hybrid picture.** Think of three tiers: the cloud (elastic, managed services, central control planes), the data centre (owned, fixed capacity, a reliable link), and the edge (many small sites, intermittent links, minimal hardware). Providers also offer a "near edge" they operate - AWS Local Zones and Wavelength, Azure Extended Zones, and similar - which give lower latency to a metro area but are still the provider's infrastructure. The "far edge" is hardware you place on your own sites.

**What changes compared with a data centre.**

| Concern           | Data centre               | Edge site                                  |
| ----------------- | ------------------------- | ------------------------------------------ |
| Number of sites   | A handful                 | Tens to thousands                          |
| Local staff       | Operations team on hand   | None; a shop manager at best               |
| Connectivity      | Dedicated, redundant link | Consumer broadband or cellular, often down |
| Hardware          | Racks, redundancy         | One to three small nodes                   |
| Physical security | Controlled building       | A cupboard; devices can be stolen          |
| Change model      | Push from a pipeline      | Pull when connected; converge eventually   |

**Kubernetes at the edge is usually a lightweight distribution.** K3s and similar small distributions run a full Kubernetes API on one to three nodes with modest memory. Provider options also exist - AKS on Azure Local or AKS Edge Essentials managed through Azure Arc, Google Distributed Cloud, AWS Outposts servers, and EKS Hybrid Nodes - which trade neutrality for a managed control plane. Projects such as KubeEdge target very constrained devices with a cloud-side control plane.

**Pull, not push, is the key design choice.** A central pipeline pushing to a thousand sites fails whenever sites are offline, and it needs inbound network access to each one. A GitOps agent in each cluster (Flux or Argo CD) pulls desired state when it can, applies it, and keeps running the last good state when it cannot. Sites converge eventually, which is the realistic goal.

**Design for disconnection explicitly.**

- Each site must serve its local function with the uplink down: local data store, local queue, local authentication cache.
- Telemetry is buffered on disk and shipped when the link returns; alerting on "site not reporting" replaces alerting on every metric.
- Images are pulled from a local registry mirror or pre-loaded, so a new rollout does not need a large download at the worst moment.
- Rollouts are staged by ring - a few pilot sites, then a region, then everything - because rolling back a thousand sites over bad links is slow.

**The trade-off.** Edge brings latency and autonomy at the cost of a huge operational surface: many small clusters, physical exposure, and slow, uncertain change. Keep the edge footprint as small as the use case allows and run everything else centrally.

**Name the user.** Two users: application teams, who should deploy to "all stores in the UK" with the same service specification they use for cloud services; and the site operators, who need a device that works when plugged in and recovers on its own. The platform absorbs fleet management, certificate rotation, and staged rollout so neither group has to.

## Example

Each store cluster runs Flux, pulls the same base, and substitutes site-specific values from a local ConfigMap.

```yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: store-platform
  namespace: flux-system
spec:
  interval: 10m # checked when online; last good revision keeps running when not
  url: https://git.example.com/retail/store-platform.git
  ref:
    branch: ring-2 # stores are assigned to rollout rings: ring-0 pilot ... ring-3 all
---
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: store-apps
  namespace: flux-system
spec:
  interval: 15m
  retryInterval: 5m
  timeout: 5m
  sourceRef:
    kind: GitRepository
    name: store-platform
  path: ./apps/store
  prune: true
  postBuild:
    substituteFrom:
      - kind: ConfigMap
        name: site-identity # store ID, region, till count - written at provisioning
```

```text
Store 0412 during a four-hour broadband outage:

  tills and pricing   serve from the local database; card payments fall back to
                      the offline-authorisation limit
  vision model        keeps running on the local GPU node; results queued
  telemetry           buffered on disk by the OpenTelemetry Collector
  Flux                cannot fetch; keeps last applied revision; no drift
  central view        "store 0412 not reporting" - one alert, not four hundred

  on reconnect: queued events replay, telemetry backfills, Flux reconciles
  the ring-2 revision that was published during the outage.
```

## Interview tips

- Define edge by location and constraints - close to the data or user, many sites, weak links, little hardware, no local staff.
- Place it as the outer tier of a hybrid platform, and distinguish provider-run near edge (Local Zones, Wavelength) from your own far-edge hardware.
- Pull-based GitOps with eventual convergence is the central design point; explain why push fails at fleet scale.
- Describe offline behaviour concretely: local serving, buffered telemetry, pre-loaded images, ring-based rollouts.
- Likely follow-up: "How would you upgrade Kubernetes on a thousand stores?" - staged rings, health gates per ring, and the ability to pause. See [How do you upgrade a fleet of clusters without breaking tenants?](../kubernetes-platform/how-do-you-upgrade-a-fleet-of-clusters-without-breaking-tenants.md).

---

[⬅ Back to Multi-Cloud and Hybrid Platforms](./README.md) · [All topics](../README.md)
