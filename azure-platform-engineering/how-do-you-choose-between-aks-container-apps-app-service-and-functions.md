---
title: "How do you choose between AKS, Container Apps, App Service, and Functions?"
id: 166
category: "Azure Platform Engineering"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - azure-platform-engineering
  - interview-questions
---

# How do you choose between AKS, Container Apps, App Service, and Functions?

**Short answer:** Container Apps is the right default for most containerised workloads on Azure - it gives you scale to zero, revisions, traffic splitting, and Dapr without a cluster to operate. Choose AKS when you need the Kubernetes ecosystem itself, App Service when you have a conventional web application and want deployment slots and a mature managed runtime, and Functions for event-driven work. As with any runtime decision, a platform should support one primary plus one specialised, not all four.

## Detail

**Container Apps deserves to be the starting point, and many candidates overlook it.** It is built on Kubernetes and KEDA but does not expose a cluster: you get HTTP and event-driven autoscaling including scale to zero, revisions with weighted traffic splitting for canaries, managed ingress with certificates, Dapr for service invocation and state, and per-app managed identity. For an organisation whose workloads are ordinary services and workers, that covers the requirements at a fraction of the operational surface of AKS.

**The comparison in decision terms:**

| Runtime        | You operate                  | Best for                                          | Main constraint                                  |
| -------------- | ---------------------------- | ------------------------------------------------- | ------------------------------------------------ |
| Container Apps | Almost nothing               | Containerised services and workers, scale to zero | Less control; no arbitrary Kubernetes objects    |
| AKS            | A cluster and its components | Kubernetes ecosystem, controllers, portability    | Largest operational surface                      |
| App Service    | Almost nothing               | Conventional web apps, deployment slots           | Platform constraints; less container flexibility |
| Functions      | Nothing                      | Event-driven, short executions, bindings          | Execution limits, cold starts on consumption     |

**AKS is right when the ecosystem is the point.** If your platform is built on custom resources, admission control, Crossplane, a service mesh, or GitOps reconciliation of arbitrary resources, you need real Kubernetes - none of that exists in Container Apps. That is a legitimate and common reason for a platform team specifically, because the platform's own machinery often needs it even when the workloads would not. AKS Automatic has narrowed the operating gap: node provisioning, upgrades, networking, and baseline policy come preconfigured, so "we need Kubernetes but not a cluster to hand-tune" is now a realistic middle option rather than a contradiction.

**App Service still wins for a specific shape.** A conventional web application, particularly on a Windows or .NET stack, benefits from deployment slots with swap, easy custom domains and certificates, and a very mature runtime. Deployment slots in particular are a genuinely good blue-green mechanism with less assembly than the equivalent elsewhere.

**Functions is a workload-shape decision.** Bindings to Azure services remove a lot of glue code, and the consumption model suits spiky or infrequent work. It fits badly for long-running processing, latency-sensitive paths where cold starts matter, and sustained high throughput where a continuously running container is cheaper. Calculate the crossover rather than assuming. For new serverless function apps, the Flex Consumption plan is the default choice: it adds VNet integration, selectable instance memory, and always-ready instances to reduce cold starts, and the Linux Consumption plan it replaces retires on 30 September 2028.

**Scale to zero is the differentiator worth naming.** Container Apps and consumption Functions can go to zero; App Service and AKS node pools generally cannot in the same way. For preview environments, internal tools, and infrequently used services this is a large cost difference, and it is often the deciding factor for non-production.

**Networking requirements frequently decide it in enterprises.** If workloads must sit inside a VNet with private endpoints to every dependency and no public exposure, check the specific integration capabilities of each option against that requirement early - it eliminates candidates faster than any feature comparison, and it is where enterprise Azure designs usually converge.

**The platform interface should outlast the choice.** If teams declare a `Service` and the platform decides how it runs, moving a workload from Container Apps to AKS is a platform change rather than an edit to every repository. That is what makes the runtime an implementation detail.

## Example

```text
Choosing, in the order that eliminates options fastest:

  Must the workload sit inside a VNet with private endpoints and no public
  exposure? -> check each option's networking integration against the exact
  requirement first. This eliminates candidates faster than anything else.

  Do you need Kubernetes-specific tooling - CRDs, admission control, operators,
  Crossplane, a mesh, GitOps of arbitrary resources?
    yes -> AKS. The platform's own machinery often needs this even when the
           workloads would not.
    no  -> continue

  Is it event-driven with short executions, and would bindings remove real glue?
    yes -> Functions on the Flex Consumption plan. Calculate the crossover:
           sustained high volume usually favours a container running
           continuously.
    no  -> continue

  Is it a conventional web app, especially .NET, that would benefit from
  deployment slots and swap?
    yes -> App Service
    no  -> continue

  Otherwise -> CONTAINER APPS. Scale to zero, revisions, weighted traffic
  splitting, managed ingress, per-app identity, no cluster to operate.
```

```yaml
# Container Apps: revisions with weighted traffic splitting gives you canary
# rollout without assembling anything - a real advantage over doing this yourself.
apiVersion: 2024-03-01
type: Microsoft.App/containerApps
name: checkout
properties:
  configuration:
    ingress:
      external: false # internal only; exposed via the hub gateway
      targetPort: 8080
      traffic: # canary, built in
        - { revisionName: checkout--rev-1-4-1, weight: 95 }
        - { revisionName: checkout--rev-1-4-2, weight: 5, label: canary }
    secrets: [] # none - identity-based access to everything
  template:
    containers:
      - name: checkout
        image: ghcr.io/example/checkout@sha256:9f2c8b1d...
        resources: { cpu: 0.5, memory: 1Gi }
    scale:
      minReplicas: 0 # SCALE TO ZERO - often the deciding factor for
      maxReplicas: 30 # non-production and internal tools
      rules:
        - name: http
          http: { metadata: { concurrentRequests: "50" } }
        - name: queue # event-driven scaling via KEDA, no cluster to run
          custom:
            type: azure-servicebus
            metadata: { queueName: orders, messageCount: "20" }
            # no connection string: the scaler authenticates as the app's identity
            identity: /subscriptions/<sub-id>/resourceGroups/rg-team-payments/providers/Microsoft.ManagedIdentity/userAssignedIdentities/id-checkout
  identity:
    type: UserAssigned # per-app identity, same model as AKS workload identity
    userAssignedIdentities:
      /subscriptions/<sub-id>/resourceGroups/rg-team-payments/providers/Microsoft.ManagedIdentity/userAssignedIdentities/id-checkout: {}
```

```text
A defensible estate for 180 services on Azure:

  PRIMARY: Container Apps ....................... 121 services
    ordinary HTTP services and queue workers. Scale to zero on all 43
    non-production instances. No cluster operated for any of these.

  AKS ............................................ 38 services
    justification: the platform's own control plane - Crossplane compositions,
    Kyverno policy, Argo CD reconciliation - plus workloads needing operators.
    One cluster per environment, not per team.

  Functions ...................................... 17 functions
    Event Grid and Service Bus handlers, scheduled jobs. Bindings genuinely
    remove glue code here.

  App Service ..................................... 4 services
    legacy .NET applications where deployment slots and swap are already the
    team's release process. Migrating them would add risk for no benefit.

  What this is not: four runtimes chosen by preference. One default, one for the
  platform's own machinery, and two shape-based fits.
```

## Interview tips

- Naming Container Apps as the default is the answer that distinguishes a current Azure view from an AKS-by-reflex one. Give its capabilities specifically: scale to zero, revisions, weighted traffic splitting, Dapr, per-app identity.
- The AKS justification most relevant to a platform interview is that the platform's own machinery needs Kubernetes even when the workloads would not. That is a precise, credible reason.
- Scale to zero as a differentiator, especially for preview environments and internal tools, is a concrete cost argument.
- Put the VNet and private endpoint requirement first as an elimination step. In enterprise Azure it decides the answer more often than any feature.
- App Service deployment slots as a genuinely good blue-green mechanism shows you evaluate rather than dismiss the older option.
- Close with the platform interface outlasting the runtime choice, so moving a workload is a platform change rather than an edit to every repository.

---

[⬅ Back to Azure Platform Engineering](./README.md) · [All topics](../README.md)
