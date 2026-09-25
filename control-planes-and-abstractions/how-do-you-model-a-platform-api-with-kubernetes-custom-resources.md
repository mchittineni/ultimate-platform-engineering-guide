---
title: "How do you model a platform API with Kubernetes custom resources?"
id: 75
category: "Control Planes and Abstractions"
difficulty: "Advanced"
tags:
  - platform-engineering
  - control-planes-and-abstractions
  - interview-questions
---

# How do you model a platform API with Kubernetes custom resources?

**Short answer:** Split intent from observed state - `spec` is what the user asked for and only they write it, `status` is what the controller found and only it writes it - and use the status subresource so the two cannot be updated in the same request. Then invest in the parts that determine usability: a schema with real validation and defaults, honest status conditions, printer columns so `kubectl get` is informative, events for anything a human will debug, and namespaced resources so RBAC and quotas work.

## Detail

**The spec/status split is the fundamental contract.** Users declare intent in `spec`; the controller reports reality in `status`. Enabling the status subresource means a user's update to `spec` cannot clobber `status` and vice versa, which prevents a whole class of race conditions between the controller and whoever is editing the object. A custom resource without a status subresource is a design error.

**Status conditions are how anything can tell what happened.** Follow the standard shape - `type`, `status`, `reason`, `message`, `lastTransitionTime`, `observedGeneration` - and use the conventional types: `Ready` for the summary, plus specific ones like `Provisioned` or `Degraded`. `observedGeneration` is the field people omit and the one that matters most: without it, nobody can distinguish "reconciled successfully" from "has not looked at your change yet".

**Validation belongs in the schema, not the controller.** Enumerations, ranges, patterns, required fields, and defaults expressed in the OpenAPI schema are rejected at submission time with a clear message. CEL validation rules extend this to cross-field constraints - "hourly backups require `pitr: true`", "`max` must be at least `min`" - which used to require a webhook. Anything caught in the schema is a good error message; anything caught in the controller is a support ticket, because the user has to find the controller's logs.

**Immutability where changing a field is meaningless.** Some fields cannot be changed after creation without destroying and recreating the resource. Say so in the schema with a CEL rule rather than letting a user edit it and discover the controller ignores them - silent no-ops are worse than rejections.

**Ergonomics are not cosmetic.** Printer columns decide whether `kubectl get postgresinstances` tells you anything. Short names make the resource usable interactively. Categories let it appear in `kubectl get all`. Events give a debuggable narrative. These are small pieces of work that determine whether people find the API pleasant, and platform teams routinely skip all of them.

**Namespaced by default.** Namespacing gives you RBAC per team, quota by object count, and a natural tenancy boundary. Cluster-scoped resources are for genuinely cluster-wide concerns - a `Tenant` or a `ClusterPolicy` - and are much harder to delegate safely.

**Design deletion at the same time as creation.** Owner references give you cascading deletion of derived objects for free. Finalizers let you clean up external systems before the object disappears - and are also where controllers deadlock, blocking namespace deletion indefinitely, so a documented escape route is part of the design rather than an afterthought.

**You may not need to write the controller.** If the API only composes existing resources, a composition engine can generate the CRD and the reconciler for you: Crossplane v2 composite resources are namespaced by default and can include any Kubernetes resource, and kro generates a CRD and controller from a single ResourceGraphDefinition. The design rules above still apply to the schema you expose; only the Go code disappears.

**Do not put high-churn data in status.** Every status write is an etcd write, and a controller updating status every few seconds across thousands of objects will degrade the cluster. Status is for state that changes when something meaningful happens; metrics and progress counters belong in your metrics system.

## Example

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata: { name: postgresinstances.platform.example.com }
spec:
  group: platform.example.com
  scope: Namespaced # RBAC per team, quota by count, natural tenancy
  names:
    kind: PostgresInstance
    plural: postgresinstances
    shortNames: [pg] # kubectl get pg
    categories: [platform] # kubectl get platform
  versions:
    - name: v1
      served: true
      storage: true
      subresources:
        status: {} # separates intent from observation - not optional
      schema:
        openAPIV3Schema:
          type: object
          required: [spec]
          properties:
            spec:
              type: object
              required: [size]
              properties:
                size:
                  type: string
                  enum: [small, medium, large] # constrained, not free-form
                backups:
                  type: string
                  enum: [none, daily, hourly]
                  default: daily # safe default, omittable
                pitr: { type: boolean, default: true }
                region:
                  type: string
                  x-kubernetes-validations:
                    - rule: "self == oldSelf"
                      message: "region is immutable; create a new instance to move"
              x-kubernetes-validations:
                # Cross-field rule - a clear rejection instead of a silent surprise
                - rule: "self.backups != 'hourly' || self.pitr == true"
                  message: "hourly backups require pitr: true"
            status:
              type: object
              properties:
                observedGeneration: { type: integer } # the field people forget
                endpoint: { type: string }
                conditions:
                  type: array
                  items:
                    type: object
                    required: [type, status]
                    properties:
                      type: { type: string }
                      status: { type: string, enum: ["True", "False", "Unknown"] }
                      reason: { type: string }
                      message: { type: string }
                      lastTransitionTime: { type: string, format: date-time }
      additionalPrinterColumns:
        - { name: Size, type: string, jsonPath: .spec.size }
        - { name: Ready, type: string, jsonPath: '.status.conditions[?(@.type=="Ready")].status' }
        - { name: Endpoint, type: string, jsonPath: .status.endpoint, priority: 1 }
        - { name: Age, type: date, jsonPath: .metadata.creationTimestamp }
```

```text
Why observedGeneration decides whether the API is usable:

  $ kubectl get pg checkout-db -o yaml
    metadata:
      generation: 4                 <- user has changed spec 4 times
    status:
      observedGeneration: 3         <- controller has processed 3
      conditions:
        - type: Ready
          status: "True"            <- TRUE, but for the PREVIOUS spec

  Without observedGeneration, `Ready: True` here is actively misleading - it
  reports success for a spec the user has already replaced. With it, tooling can
  say "reconciling" rather than "done", which is the difference between an API
  people trust and one they poll nervously.

  $ kubectl get pg
    NAME           SIZE    READY   AGE
    checkout-db    small   True    31d
    search-db      medium  False   4m      <- printer columns make this visible
                                              at a glance; without them you get
                                              only NAME and AGE
```

## Interview tips

- Lead with the spec/status split and the status subresource, and say why: it prevents the controller and the user racing on the same object.
- `observedGeneration` is the highest-signal detail in this answer. Explain concretely how `Ready: True` is misleading without it.
- Push validation into the schema with enums, defaults, and CEL cross-field rules, and give the reasoning: schema errors are good messages, controller errors are support tickets.
- Mention printer columns, short names, and events. They sound minor and they are exactly what separates an API people enjoy from one they tolerate.
- Warn against high-churn status writes degrading etcd - it shows you have thought about the control plane's own reliability, not just the interface.

---

[⬅ Back to Control Planes and Abstractions](./README.md) · [All topics](../README.md)
