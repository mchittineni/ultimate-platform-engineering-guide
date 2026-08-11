---
title: "Why does Kubernetes end up as the substrate for most platforms?"
id: 30
category: "Kubernetes Platform"
difficulty: "Beginner"
tags:
  - platform-engineering
  - kubernetes-platform
  - interview-questions
---

# Why does Kubernetes end up as the substrate for most platforms?

**Short answer:** Not primarily because it runs containers well - plenty of things do - but because it is an extensible declarative API with a reconciliation engine, RBAC, admission control, and a watch mechanism already built. A platform needs all of those anyway, so building on Kubernetes means you get the control-plane machinery for free and spend your effort on the interface and the defaults. The container orchestration is almost a side effect.

## Detail

**What you actually inherit:**

| Kubernetes gives you         | What a platform would otherwise build        |
| ---------------------------- | -------------------------------------------- |
| Declarative API with schemas | An API server, validation, versioning        |
| Custom resource definitions  | A way to define your own platform types      |
| Controller and watch pattern | Reconciliation loops and change notification |
| RBAC                         | Authorisation for every platform operation   |
| Admission webhooks           | A policy enforcement point                   |
| Namespaces and quotas        | Tenancy primitives                           |
| Secrets and config plumbing  | Delivery of configuration to workloads       |
| A large ecosystem            | Ingress, certificates, storage, telemetry    |

The middle rows are the ones that matter for platform engineering. A custom resource plus a controller gives you a versioned, validated, authorised, reconciled API for anything - not only workloads. That is why Crossplane, cert-manager, Argo CD, and most modern platform tooling are all Kubernetes controllers: they are using it as an extensible control plane rather than as a container scheduler.

**Reconciliation is the property that changes behaviour.** Declaring desired state and having a controller converge toward it continuously is fundamentally different from running a script. Drift is corrected rather than merely detected, operations are idempotent, and partial failures self-heal on the next loop. Building that reliably yourself is a serious undertaking, and it is the core of what a platform control plane does.

**The ecosystem argument is real but secondary.** Ingress controllers, certificate automation, CSI drivers, policy engines, and telemetry agents exist and interoperate because they target the same API. That saves enormous integration effort - but it is a consequence of the extensible API, not a separate reason.

**The honest costs.** Kubernetes is complex, and that complexity is now your platform team's to absorb rather than eliminate: upgrades and version skew, networking that is genuinely hard to debug, resource management subtleties, and a large security surface. Managed control planes remove a meaningful portion of this but not the workload-layer complexity, which is where most of it lives.

**When it is the wrong substrate.** If your workloads are a handful of stateless services, a PaaS or a serverless container runtime - Cloud Run, App Runner, Container Apps - gives you most of the outcome with a fraction of the operational burden. If you are entirely serverless functions and managed services, Kubernetes adds a cluster to run without a corresponding benefit. Being able to say "we chose Cloud Run and it was correct" is a sign of judgement rather than inexperience.

**The nuance worth adding.** You can use Kubernetes as a control plane without running your workloads on it. A management cluster hosting Crossplane can provision serverless services, databases, and queues while nothing customer-facing runs in a Pod. That decoupling - Kubernetes as the API, not necessarily as the runtime - is the strongest version of this answer.

## Example

```text
The same capability - "teams can declare a Postgres and get one" - built two ways.

WITHOUT Kubernetes, you build:
  HTTP API + schema validation + versioning ......... weeks
  authentication and authorisation model ............ weeks
  desired-state store with optimistic concurrency ... weeks
  reconciliation loop with backoff and retry ........ weeks
  change notification / watch semantics ............. weeks
  audit log of every change ......................... weeks
  policy enforcement point .......................... weeks
  ...then, finally, the logic that provisions a database.

WITH Kubernetes:
  one CustomResourceDefinition  -> API, schema, validation, versioning, audit
  RBAC rules                    -> authorisation
  one controller                -> reconciliation, watch, retry, backoff
  admission policy              -> enforcement
  ...then the logic that provisions a database - the only novel part.
```

```yaml
# This is the whole argument in one file: a validated, versioned, authorised,
# reconciled, auditable platform API - defined declaratively, no server written.
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata: { name: postgresinstances.platform.example.com }
spec:
  group: platform.example.com
  scope: Namespaced
  names: { kind: PostgresInstance, plural: postgresinstances, shortNames: [pg] }
  versions:
    - name: v1
      served: true
      storage: true
      subresources: { status: {} } # observed state, separate from intent
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              required: [size]
              properties:
                size: { type: string, enum: [small, medium, large] }
                backups: { type: string, enum: [none, daily, hourly], default: daily }
                pitr: { type: boolean, default: true }
      additionalPrinterColumns:
        - { name: Size, type: string, jsonPath: .spec.size }
        - { name: Ready, type: string, jsonPath: .status.conditions[?(@.type=="Ready")].status }
```

## Interview tips

- Lead with "extensible declarative API with a reconciliation engine", not with container orchestration. That reframing is what a platform interviewer is listening for.
- Point out that Crossplane, cert-manager, and Argo CD are all controllers - evidence that the industry uses Kubernetes as a control plane, not just a scheduler.
- Explain reconciliation versus scripting concretely: drift corrected rather than detected, idempotent operations, self-healing partial failures.
- Be willing to say Kubernetes is the wrong choice sometimes, and name the alternatives. Candidates who treat it as inevitable sound less credible than those who can justify it.
- The strongest close is Kubernetes as the API without being the runtime - a management cluster provisioning serverless and managed services.

---

[⬅ Back to Kubernetes Platform](./README.md) · [All topics](../README.md)
