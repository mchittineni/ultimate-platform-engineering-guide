---
title: "How do kro, Crossplane compositions, and Helm charts differ for composing resources?"
id: 73
category: "Control Planes and Abstractions"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - control-planes-and-abstractions
  - interview-questions
---

# How do kro, Crossplane compositions, and Helm charts differ for composing resources?

**Short answer:** All three bundle several Kubernetes resources behind one set of inputs, but they do it at different points. A Helm chart is a template rendered at install time into plain manifests - it creates no new API and nothing reconciles the bundle as a unit. kro and Crossplane both create a new custom resource type backed by a controller that reconciles the whole group continuously: kro does it with one declarative ResourceGraphDefinition and CEL expressions, while Crossplane uses an XRD plus a composition function pipeline and adds providers for cloud APIs. Choose Helm to package software, kro for lightweight in-cluster APIs, and Crossplane when the abstraction must drive cloud infrastructure or needs richer logic.

## Detail

**Helm: templating plus release tracking.** A chart is a set of Go templates and a `values.yaml`. `helm install` renders them client-side into manifests, applies them, and records a _release_ so it can upgrade or roll back later. The consumer interface is the values file - loosely typed unless the chart ships a `values.schema.json`. There is no new Kubernetes kind, so RBAC, admission policies, and `kubectl get` see only the individual Deployments and Services, not "the app". Nothing watches the bundle after install unless a GitOps tool such as Argo CD or Flux re-applies it. Helm is excellent at distributing third-party software and at being the rendering step inside GitOps.

**kro: a declarative API generator.** A `ResourceGraphDefinition` (currently `kro.run/v1alpha1`) contains a schema, written in kro's compact SimpleSchema syntax, and a list of resource templates. Fields reference the schema and each other with CEL expressions such as `${schema.spec.image}` or `${database.status.endpoint}`. kro infers a dependency graph from those references, generates a CRD for the new kind, and runs a controller that creates resources in dependency order and keeps them reconciled. `readyWhen` gates dependants on readiness and `includeWhen` makes resources conditional. kro composes Kubernetes resources only; for cloud infrastructure you compose the custom resources of a cloud controller - ACK, Azure Service Operator, Config Connector, or Crossplane managed resources. It started as a joint effort by engineers at AWS, Google Cloud, and Microsoft and is now a Kubernetes SIG Cloud Provider subproject; its API is still alpha.

**Crossplane compositions: an API plus a programmable pipeline.** A `CompositeResourceDefinition` defines the new kind; a `Composition` runs a pipeline of composition functions that decide what to create. Functions can be patch-and-transform YAML, Go templates, KCL, Python, or CEL - there is even a function that accepts kro-style definitions - so arbitrary logic is possible, including calling external systems. Crossplane brings its own providers that talk to cloud APIs directly, plus packaging, dependency management, and, since v2, namespaced composites that can include any Kubernetes resource. It is the most capable of the three and the heaviest to operate.

**The comparison:**

| Dimension              | Helm chart                  | kro                                        | Crossplane composition                      |
| ---------------------- | --------------------------- | ------------------------------------------ | ------------------------------------------- |
| Creates a new API      | No - values file only       | Yes - generated CRD                        | Yes - XRD                                   |
| When it runs           | At install or upgrade       | Continuously, in-cluster                   | Continuously, in-cluster                    |
| Logic                  | Go templates                | CEL expressions, dependency graph inferred | Function pipeline in several languages      |
| Ordering and readiness | Hooks and `--wait`, coarse  | `readyWhen`, graph-ordered                 | Function-controlled, readiness per resource |
| Cloud resources        | Via other controllers' CRDs | Via other controllers' CRDs                | Native providers, or any CRD                |
| Status for the user    | Release status only         | Status fields defined in CEL               | XR status and conditions                    |
| Maturity               | Very mature, ubiquitous     | Alpha API                                  | Mature, CNCF graduated                      |
| Operational cost       | None in-cluster             | One controller                             | Core, providers, and functions              |

**They combine rather than compete.** Helm commonly installs kro or Crossplane themselves. A platform might publish kro or Crossplane APIs and let GitOps apply the instances. Templating a custom resource with Helm is also normal - the chart just emits a `WebApp` object instead of a Deployment.

**How to choose.** If you are shipping software for others to install, use Helm. If you want a thin, typed, reconciled API over Kubernetes resources and are comfortable with an alpha API, kro is the lightest option. If the API must provision cloud infrastructure, needs complex logic, or must be packaged and versioned across many clusters, Crossplane fits. The user is the application developer either way; the question is how much the platform team is prepared to operate to give them a real API instead of a values file.

## Example

```yaml
# kro: one object defines the API, the resources, and their wiring.
apiVersion: kro.run/v1alpha1
kind: ResourceGraphDefinition
metadata:
  name: webapp
spec:
  schema:
    apiVersion: v1alpha1
    kind: WebApp
    spec:
      name: string
      image: string
      replicas: integer | default=2
      exposed: boolean | default=false
    status:
      availableReplicas: ${deployment.status.availableReplicas}
  resources:
    - id: deployment
      template:
        apiVersion: apps/v1
        kind: Deployment
        metadata:
          name: ${schema.spec.name}
        spec:
          replicas: ${schema.spec.replicas}
          selector: { matchLabels: { app: "${schema.spec.name}" } }
          template:
            metadata: { labels: { app: "${schema.spec.name}" } }
            spec:
              containers:
                - name: app
                  image: ${schema.spec.image}
                  ports: [{ containerPort: 8080 }]
      readyWhen:
        - ${deployment.status.availableReplicas == deployment.spec.replicas}
    - id: service
      template:
        apiVersion: v1
        kind: Service
        metadata:
          name: ${schema.spec.name}
        spec:
          selector: ${deployment.spec.selector.matchLabels} # creates a graph edge
          ports: [{ port: 80, targetPort: 8080 }]
    - id: route
      includeWhen:
        - ${schema.spec.exposed}
      template:
        apiVersion: gateway.networking.k8s.io/v1
        kind: HTTPRoute
        metadata:
          name: ${schema.spec.name}
        spec:
          parentRefs: [{ name: public, namespace: gateways }]
          rules:
            - backendRefs: [{ name: "${service.metadata.name}", port: 80 }]
```

```yaml
# What a developer writes - a real, typed, namespaced API.
apiVersion: kro.run/v1alpha1
kind: WebApp
metadata:
  name: checkout
  namespace: team-payments
spec:
  name: checkout
  image: ghcr.io/example/checkout:1.4.2
  exposed: true
```

```text
The same bundle as a Helm chart:
  $ helm install checkout ./webapp -n team-payments \
      --set image=ghcr.io/example/checkout:1.4.2 --set exposed=true
  -> renders Deployment, Service, HTTPRoute; records release "checkout"
  $ kubectl get webapps -n team-payments
  error: the server doesn't have a resource type "webapps"
         ^ no API exists; delete the Service by hand and nothing restores it
           until someone runs helm upgrade or a GitOps tool re-syncs

As a Crossplane v2 composition, the XRD defines kind App and a function
pipeline renders the same three objects - plus, if needed, an S3 bucket
through a native provider in the same reconcile.
```

## Interview tips

- The distinguishing question is "does it create a new API and reconcile it?" Helm does not; kro and Crossplane do.
- Describe kro precisely: ResourceGraphDefinition, CEL references that form a dependency graph, a generated CRD and controller, `readyWhen` and `includeWhen`. Mention that its API is still alpha.
- Position Crossplane as the heavier, more capable option: function pipelines in several languages, native cloud providers, packaging - and since v2, composition of any Kubernetes resource.
- Say they combine: Helm often installs the other two, and GitOps applies the instances.
- Frame the choice around the developer experience you want to offer and the operational cost the platform team accepts. That is the platform-engineering answer rather than a feature list.

---

[⬅ Back to Control Planes and Abstractions](./README.md) · [All topics](../README.md)
