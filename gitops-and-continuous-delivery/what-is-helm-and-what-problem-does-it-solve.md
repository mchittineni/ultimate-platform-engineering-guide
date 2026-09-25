---
title: "What is Helm and what problem does it solve?"
id: 81
category: "GitOps and Continuous Delivery"
difficulty: "Beginner"
tags:
  - platform-engineering
  - gitops-and-continuous-delivery
  - interview-questions
---

# What is Helm and what problem does it solve?

**Short answer:** Helm is a package manager for Kubernetes. A Helm chart bundles a set of templated Kubernetes manifests with a file of default values, so one chart can be installed many times with different settings - different replica counts, hostnames, or resource sizes per environment. It solves two problems: copying near-identical YAML for every environment and every service, and distributing third-party software (a database, an ingress controller, a monitoring stack) in a form users can install and configure without reading every manifest.

## Detail

**The problem it was built for.** A real application in Kubernetes is not one manifest; it is a Deployment, a Service, a ServiceAccount, a ConfigMap, a HorizontalPodAutoscaler, a PodDisruptionBudget, and more. Deploying it to three environments by copying those files means three copies that drift apart, and every fix has to be made three times. Distributing software is worse: a vendor cannot ship one set of YAML that fits every user's cluster.

**How a chart works.** A chart is a directory with a `Chart.yaml` (name, version, dependencies), a `values.yaml` (the defaults), and a `templates/` directory of manifests written with Go templating. At install time Helm merges the defaults with whatever values you supply, renders the templates into plain Kubernetes YAML, and applies the result to the cluster. Charts can depend on other charts, and a `values.schema.json` can validate the values a user passes so typos fail early rather than silently rendering a broken manifest.

**Releases give you lifecycle, not just templating.** When Helm installs a chart it records a _release_ - by default stored as a Secret in the target namespace - containing the rendered manifests and the values used. That is what makes `helm upgrade`, `helm rollback`, and `helm uninstall` possible: Helm knows exactly what it created last time. It also has hooks for running Jobs before or after an install or upgrade, which is how many charts run database migrations.

**Charts are distributed through registries.** Modern practice is to publish charts as OCI artefacts to the same container registry that holds your images (`helm push` and `oci://` references), which means the same access control, replication, and signing apply to both. Classic HTTP chart repositories with an `index.yaml` still exist but are no longer the default for new work.

**Helm 4 is current.** Helm 4.0 went GA in November 2025. The changes that matter most day to day are that new releases use Kubernetes server-side apply by default, so field ownership is tracked by the API server rather than guessed by the client; that `--wait` uses kstatus to judge readiness far more accurately; and that plugins now run in a sandboxed WebAssembly runtime. Charts written for Helm 3 (chart `apiVersion: v2`) install unchanged. Helm 3 has received its last feature release and gets security fixes only until 10 February 2027, so upgrade pipelines and tooling now rather than in a hurry then. A couple of flags were renamed - `--atomic` became `--rollback-on-failure` - with the old names still accepted with a warning.

**How Helm fits GitOps.** Both Argo CD and Flux consume charts, but differently. Argo CD renders a chart with the equivalent of `helm template` and applies the output itself, so there is no Helm release in the cluster and `helm list` shows nothing. Flux's helm-controller runs real Helm installs and upgrades through the Helm SDK (on Helm 4 since Flux 2.8), so releases, hooks, and rollback behave as they do from the CLI. Know which one you run before debugging a hook that "did not fire".

**The trade-offs.** Go templating inside YAML is hard to read, and a chart with thirty `if` blocks is difficult to review because a one-line values change can alter many objects - see [How do you keep templated manifests reviewable?](./how-do-you-keep-templated-manifests-reviewable.md). Charts also tempt authors to expose every field as a value, at which point the chart is just Kubernetes with extra indirection. Helm is at its best for packaging and distributing software to many consumers; for your own services, a small, opinionated chart or a Kustomize overlay is often easier to live with.

**The platform user.** For a platform team, Helm usually appears in two places: installing third-party components onto every cluster (cert-manager, an ingress or Gateway API controller, an OpenTelemetry collector), and publishing one shared, versioned "service" chart so product teams deploy a new microservice by writing twenty lines of values instead of four hundred lines of YAML. The product engineer gets probes, resource defaults, disruption budgets, and security context right without having to know they exist.

## Example

```text
checkout-chart/
  Chart.yaml            name, version, dependencies
  values.yaml           defaults
  values.schema.json    validates user-supplied values
  templates/
    deployment.yaml
    service.yaml
    hpa.yaml
    _helpers.tpl        shared template snippets
```

```yaml
# Chart.yaml - apiVersion v2 is the chart format for both Helm 3 and Helm 4.
apiVersion: v2
name: service
version: 3.2.0 # the chart's version
appVersion: "1.4.2" # the application's version, informational
dependencies:
  - name: platform-common # a library chart of shared helpers
    version: 1.x.x
    repository: oci://ghcr.io/example/charts
```

```yaml
# templates/deployment.yaml (excerpt) - values are interpolated at render time.
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}
spec:
  replicas: {{ .Values.replicaCount }}
  template:
    spec:
      containers:
        - name: app
          image: "{{ .Values.image.repository }}@{{ .Values.image.digest }}"
          resources: {{- toYaml .Values.resources | nindent 12 }}
```

```bash
# Render locally to see exactly what would be applied - do this before every review.
helm template checkout oci://ghcr.io/example/charts/service --version 3.2.0 \
  -f values-production.yaml

# Install or upgrade, waiting until resources are actually ready (kstatus in Helm 4).
helm upgrade --install checkout oci://ghcr.io/example/charts/service \
  --version 3.2.0 -n team-payments -f values-production.yaml \
  --wait --rollback-on-failure

helm history checkout -n team-payments   # every revision, with its values
helm rollback checkout 7 -n team-payments
```

## Interview tips

- Describe Helm as templating plus release lifecycle. Candidates who mention only templating miss upgrade, rollback, and hooks, which are why people use it over plain templating.
- Know the chart layout (`Chart.yaml`, `values.yaml`, `templates/`) and that the chart `version` and `appVersion` are different things.
- Show you are current: Helm 4 is GA, server-side apply is the default for new releases, charts from Helm 3 still work, and Helm 3 security support ends in February 2027.
- The Argo CD versus Flux distinction - rendered-and-applied versus a real Helm release - is a strong follow-up answer and explains many "my hook did not run" questions.
- Volunteer the downside: heavy templating hurts reviewability. Mention rendering in CI with `helm template` and reviewing the output. The natural next question is how Kustomize compares - see [What is Kustomize and how does it differ from Helm?](./what-is-kustomize-and-how-does-it-differ-from-helm.md).

---

[⬅ Back to GitOps and Continuous Delivery](./README.md) · [All topics](../README.md)
