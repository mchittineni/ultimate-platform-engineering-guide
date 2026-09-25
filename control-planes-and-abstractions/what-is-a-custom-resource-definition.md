---
title: "What is a custom resource definition?"
id: 68
category: "Control Planes and Abstractions"
difficulty: "Beginner"
tags:
  - platform-engineering
  - control-planes-and-abstractions
  - interview-questions
---

# What is a custom resource definition?

**Short answer:** A CustomResourceDefinition (CRD) teaches the Kubernetes API server about a new kind of object - say `PostgresInstance` - with its own name, schema, and validation. Once it is installed, you can create, list, watch, and delete those objects with `kubectl` and the same RBAC, audit logging, and admission policies as built-in resources. A CRD on its own only stores data; it becomes useful when a controller watches those objects and does the real work, which is how operators, Crossplane, Argo CD, and most platform APIs are built.

## Detail

**What a CRD actually adds.** Kubernetes ships with resources such as Pods, Deployments, and Services. A CRD registers a new _type_ alongside them. The API server starts serving a new endpoint - for example `/apis/platform.example.com/v1/namespaces/team-payments/postgresinstances` - stores the objects in etcd, and validates them against the schema you supplied. You get all of this without writing or running a server of your own.

**Definition versus instance.** The CRD is the type; a _custom resource_ is one object of that type. The CRD is usually installed once by a platform team or an operator's Helm chart. Custom resources are created many times by the people using the platform - one `PostgresInstance` per database a team needs.

**The CRD does nothing by itself.** Creating a `PostgresInstance` object does not create a database. It is just a record saying "this is wanted". A _controller_ watches for those records and runs a reconciliation loop: it sees a new instance, provisions the database, and writes the result back into the object's `status`. The CRD is the API; the controller is the implementation. This split is why the pattern works so well for platforms - the contract that users see can stay stable while the implementation behind it changes.

**What goes in a CRD:**

- **Group, version, and names.** `platform.example.com`, `v1`, kind `PostgresInstance`, plural `postgresinstances`. The group should be a domain you own, so it cannot clash with anyone else's.
- **Scope.** `Namespaced` (almost always right for team-facing resources, because RBAC and quotas are per namespace) or `Cluster`.
- **Schema.** An OpenAPI v3 schema describing allowed fields, types, enumerations, defaults, and required fields. Since Kubernetes 1.29, CEL validation rules are GA, so you can express cross-field rules in the schema too.
- **Subresources.** `status`, so the user's `spec` and the controller's `status` are written separately.
- **Printer columns.** What `kubectl get` shows, so users can see readiness at a glance.

**Versioning.** A CRD can serve several versions at once (`v1alpha1`, `v1`), with one marked as the storage version. Moving between versions without breaking users may require a conversion webhook, which is one of the more demanding parts of running your own CRDs.

**Trade-offs.** CRDs are cheap to create and easy to over-create. Each one is an API you must support, version, and eventually migrate. Badly designed CRDs leak implementation details - exposing every cloud setting rather than the few choices users actually need - and they are hard to change once teams depend on them. Large numbers of CRDs also add load to the API server; installing a cloud provider that registers hundreds of them is a known cause of slow clusters. Deleting a CRD deletes every custom resource of that type, which with a controller behind it can mean deleting real infrastructure.

**Who the user is.** Application developers use custom resources as a simple, validated way to ask for things - a database, a DNS name, a preview environment - without learning the cloud APIs underneath. Platform engineers design the CRDs and own the controllers. Getting the schema right is the platform team's product design work.

## Example

```yaml
# Installed once by the platform team.
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: postgresinstances.platform.example.com # must be <plural>.<group>
spec:
  group: platform.example.com
  scope: Namespaced
  names:
    kind: PostgresInstance
    plural: postgresinstances
    singular: postgresinstance
    shortNames: [pg]
  versions:
    - name: v1
      served: true
      storage: true
      subresources:
        status: {}
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              required: [size]
              properties:
                size: { type: string, enum: [small, medium, large] }
                backups: { type: string, enum: [none, daily], default: daily }
            status:
              type: object
              x-kubernetes-preserve-unknown-fields: true
      additionalPrinterColumns:
        - { name: Size, type: string, jsonPath: .spec.size }
        - { name: Ready, type: string, jsonPath: '.status.conditions[?(@.type=="Ready")].status' }
```

```yaml
# Created by an application team - one per database they need.
apiVersion: platform.example.com/v1
kind: PostgresInstance
metadata:
  name: checkout-db
  namespace: team-payments
spec:
  size: small
```

```text
$ kubectl apply -f checkout-db.yaml
postgresinstance.platform.example.com/checkout-db created

$ kubectl apply -f bad.yaml          # size: huge
The PostgresInstance "orders-db" is invalid: spec.size: Unsupported value:
"huge": supported values: "small", "medium", "large"
                         ^ rejected by the schema before any controller runs

$ kubectl get pg -n team-payments
NAME          SIZE    READY
checkout-db   small   True       <- status written by the controller
```

## Interview tips

- Separate the three pieces clearly: the CRD is the type, the custom resource is an instance, and the controller is what makes anything happen.
- Say why platforms like them: you inherit Kubernetes RBAC, audit, admission policy, `kubectl`, and GitOps tooling for free on your own API.
- Mention schema validation and CEL rules; rejecting bad input at the API is far better than failing later in a controller.
- Name the costs: every CRD is an API to support and version, and deleting a CRD deletes all its instances.
- A likely follow-up is how to design a good one - see [modelling a platform API with custom resources](./how-do-you-model-a-platform-api-with-kubernetes-custom-resources.md) - or whether to write your own controller or use Crossplane or kro.

---

[⬅ Back to Control Planes and Abstractions](./README.md) · [All topics](../README.md)
