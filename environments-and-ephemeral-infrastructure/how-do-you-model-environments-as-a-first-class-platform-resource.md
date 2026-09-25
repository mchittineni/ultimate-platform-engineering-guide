---
title: "How do you model environments as a first-class platform resource?"
id: 118
category: "Environments and Ephemeral Infrastructure"
difficulty: "Advanced"
tags:
  - platform-engineering
  - environments-and-ephemeral-infrastructure
  - interview-questions
---

# How do you model environments as a first-class platform resource?

**Short answer:** Give the platform an explicit `Environment` API object with an owner, a class that fixes its policies, a lifecycle, a position in a promotion order, and a status - and make everything else reference it. Namespaces, cloud accounts, databases, DNS, credentials, and deployments are then _derived_ from environments by controllers, instead of an environment being an informal name that happens to appear in a dozen tools. The payoff is that creating, auditing, promoting into, costing, and deleting an environment become single operations on one object.

## Detail

**The problem with implicit environments.** In most organisations "staging" is a convention: a namespace here, a Terraform workspace there, a values file, a secrets path, a dashboard folder, a column in the deploy tool. Nobody can answer "what exists in staging, who owns it, and what does it cost?" without archaeology, creating a new environment is a multi-week project, and deleting one leaves orphans in every system that was not remembered. Preview environments make this acute, because they multiply the count by a hundred.

**Separate the class from the instance.** An `EnvironmentClass` is written by the platform team and encodes policy: lifecycle rules, tenancy model, placement, which dependencies are shared, security posture, allowed data classification, and cost controls. An `Environment` is an instance - `production`, `staging-eu`, `pr-4821`, `sandbox-alice` - that names its class and supplies only what legitimately varies. This mirrors `StorageClass` and `PersistentVolumeClaim`: the platform decides what kinds exist, consumers ask for one. It is also where the parity invariants live, so a preview cannot quietly disable TLS - see [what environment parity actually requires](./what-does-environment-parity-actually-require.md).

**What the object must carry:**

| Field           | Why it has to be on the object                                                |
| --------------- | ----------------------------------------------------------------------------- |
| Owner           | Every environment has a team that is paged, billed, and asked before deletion |
| Class           | Policy by reference, not by copy-paste                                        |
| Lifecycle       | TTL, reap triggers, and deletion protection for long-lived ones               |
| Promotion order | Which environment feeds which; what gates the move                            |
| Data class      | Whether real data may exist here - drives access and network controls         |
| Placement       | Cluster, region, account or subscription                                      |
| Status          | Ready conditions, endpoints, what is deployed at which digest, cost to date   |

**Controllers derive the rest.** A reconciler turns an `Environment` into its concrete parts, each carrying an owner reference or an ownership label back to it: a namespace or a cluster, an account or project for cloud resources, network policy, quota, a wildcard hostname, secret store paths, observability tenants, and cost allocation labels. Deletion then cascades from one object, with finalisers blocking removal until external resources are really gone. The implementation can be a custom controller, Crossplane v2 compositions - which can now be namespaced and compose any Kubernetes resource, not only managed cloud resources - or a kro `ResourceGraphDefinition` that generates the `Environment` API and its dependency graph. The mechanics are covered in [how to model a platform API with Kubernetes custom resources](../control-planes-and-abstractions/how-do-you-model-a-platform-api-with-kubernetes-custom-resources.md).

**Workloads target environments, not infrastructure.** A deployment says "service `checkout` at digest X into environment `staging-eu`", and the platform resolves that to a cluster and namespace. Workload specifications such as [Score](../control-planes-and-abstractions/what-problem-does-a-workload-specification-like-score-solve.md) are built on this split - the workload declares what it needs, the environment decides how that is satisfied. The same `postgres` dependency resolves to a schema on a shared instance in a preview and a dedicated managed database in production, which is exactly how environment-specific behaviour should enter the system: through the environment, not through `if env == "prod"` in a pipeline.

**Promotion becomes a relationship between objects.** With a declared order - `dev` to `staging` to `production`, each with gates - a GitOps promotion tool can read it rather than having it hard-coded in pipeline YAML. Kargo models this as stages and freight; Argo CD's ApplicationSet generators can fan one application out to every environment matching a label. The environment object is the thing both tools select on.

**Make it visible where developers look.** Environments belong in the service catalogue next to the services deployed into them, with status and cost, and in the CLI. Managed products converge on the same idea: Azure Deployment Environments has environment types and definitions in a catalogue, and most internal developer platforms expose environment types as a core concept. AI agents consuming the platform - for example through an MCP server - benefit particularly, because "create a preview environment for this branch" becomes one well-typed call with policy enforced, rather than a sequence of raw infrastructure operations.

**Trade-offs.** It is a real piece of platform engineering: a controller, an API with versioning and compatibility obligations, and a migration of existing environments into the model, which is where most of the effort goes. The abstraction can also be too rigid - if every exception needs a new class, teams will route around it. Start with the fields that pay for themselves immediately (owner, class, lifecycle, placement, status), adopt existing long-lived environments by labelling their resources before you try to regenerate them, and treat production's object as read-only-by-default with deletion protection.

**Who the platform serves.** Application teams, who ask for an environment and get everything it implies; platform and security teams, who change policy once in a class; finance, who get cost per environment and owner for free; and reviewers, who get a URL and a status instead of a Slack thread.

## Example

```yaml
# Platform-owned policy. Instances reference it; they cannot override the invariants.
apiVersion: platform.example.com/v1
kind: EnvironmentClass
metadata: { name: preview }
spec:
  tenancy: namespace # production class uses: dedicated-cluster
  dataClassification: synthetic-only
  lifecycle: { ttl: 72h, idleTimeout: 8h, deletionProtection: false }
  invariants: { tls: required, auth: sso, networkPolicy: default-deny }
  dependencies:
    postgres: { provider: shared-pool, isolation: database-per-environment }
  cost: { maxConcurrentPerTeam: 5, nodePool: spot }
---
apiVersion: platform.example.com/v1
kind: Environment
metadata:
  name: pr-4821
  labels: { platform.example.com/owner: team-payments }
spec:
  class: preview
  promotesFrom: null # previews are leaves; staging promotesFrom: dev
  source: { pullRequest: { repo: example/checkout, number: 4821 } }
  placement: { cluster: previews-eu-1, region: eu-west-1 }
status:
  phase: Ready
  conditions:
    - { type: NamespaceReady, status: "True" }
    - { type: DatabaseReady, status: "True", message: "cloned from checkout-seed-v14" }
  endpoints: ["https://pr-4821.preview.example.internal"]
  deployed: [{ service: checkout, digest: "sha256:9f2c8b1d..." }]
  costToDate: { currency: EUR, amount: "0.38" }
```

```yaml
# One way to implement the API: kro generates the Environment CRD and reconciles
# its resource graph. Abbreviated to two resources.
apiVersion: kro.run/v1alpha1
kind: ResourceGraphDefinition
metadata: { name: environment }
spec:
  schema:
    apiVersion: v1alpha1
    kind: Environment
    spec:
      name: string
      owner: string
      cpuQuota: string | default="4"
    status:
      namespace: ${namespace.metadata.name}
  resources:
    - id: namespace
      template:
        apiVersion: v1
        kind: Namespace
        metadata:
          name: env-${schema.spec.name}
          labels: { platform.example.com/owner: "${schema.spec.owner}" }
    - id: quota
      template:
        apiVersion: v1
        kind: ResourceQuota
        metadata: { name: environment-quota, namespace: "${namespace.metadata.name}" }
        spec: { hard: { requests.cpu: "${schema.spec.cpuQuota}" } }
```

```text
What the model makes possible - questions that used to need archaeology:

  $ platform env list --owner team-payments
  NAME         CLASS       PHASE   AGE    COST TO DATE   PROMOTES FROM
  production   production  Ready   3y     -              staging
  staging      staging     Ready   3y     -              dev
  dev          dev         Ready   3y     -              -
  pr-4821      preview     Ready   2h     EUR 0.38       -
  pr-4790      preview     Idle    19h    EUR 2.10       -   (reap in 5h)

  $ platform env delete pr-4790
  deleting 11 owned resources: namespace, database, role, dns, secrets path,
  dashboards folder, cost labels ... done. No orphans.
```

## Interview tips

- Start from the pain of implicit environments - "staging" scattered across a dozen tools - and the questions nobody can answer. That motivates the design.
- The class-versus-instance split is the core idea; the `StorageClass` analogy lands quickly with Kubernetes-literate interviewers.
- List the fields the object must carry, and emphasise owner, lifecycle, and status - they are what make audit, cost, and cleanup single operations.
- Show that workloads target environments and dependencies resolve per environment. That is how you remove `if env == "prod"` from pipelines.
- Name implementation options (custom controller, Crossplane v2, kro) without making the answer about a tool, and be honest that adopting existing environments is most of the work.

---

[⬅ Back to Environments and Ephemeral Infrastructure](./README.md) · [All topics](../README.md)
