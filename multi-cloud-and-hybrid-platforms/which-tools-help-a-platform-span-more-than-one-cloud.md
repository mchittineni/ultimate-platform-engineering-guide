---
title: "Which tools help a platform span more than one cloud?"
id: 187
category: "Multi-Cloud and Hybrid Platforms"
difficulty: "Beginner"
tags:
  - platform-engineering
  - multi-cloud-and-hybrid-platforms
  - interview-questions
---

# Which tools help a platform span more than one cloud?

**Short answer:** The tools that help are the ones that give you one workflow over many targets without pretending the targets are identical: Kubernetes as a common compute API, infrastructure as code with per-provider plugins (OpenTofu or Terraform, Pulumi, Crossplane), GitOps controllers (Argo CD, Flux) for delivery, OpenTelemetry for telemetry, one identity provider with federation, and policy engines (OPA, Kyverno) for guardrails. They unify the workflow and the team-facing interface; they do not make provider services, IAM, or networking equivalent, and a good answer says so.

## Detail

**Think in layers, and pick one tool per layer.** A multi-cloud platform is not one product. It is a set of layers, each with a portable option that works across providers:

| Layer                | Portable tools                                          | What it unifies                         | What it does not        |
| -------------------- | ------------------------------------------------------- | --------------------------------------- | ----------------------- |
| Compute              | Kubernetes (EKS, AKS, GKE, on-premises)                 | Deployment API, scheduling, manifests   | Storage classes, LBs    |
| Cluster lifecycle    | Cluster API, provider fleet tools                       | Creating and upgrading clusters         | Provider node features  |
| Infrastructure       | OpenTofu / Terraform, Pulumi, Crossplane, kro           | One language and workflow               | Resource semantics      |
| Delivery             | Argo CD, Flux                                           | Git as source of truth for every target | Per-cloud config values |
| Observability        | OpenTelemetry, Prometheus, Grafana                      | Instrumentation and collection          | Provider-native metrics |
| Identity             | One IdP (Entra ID, Okta), OIDC federation, SPIFFE/SPIRE | One human identity; workload trust      | Each cloud's IAM model  |
| Policy               | OPA / Gatekeeper, Kyverno, ValidatingAdmissionPolicy    | Cluster admission rules everywhere      | Cloud org guardrails    |
| Secrets              | Vault or OpenBao, External Secrets Operator             | One way to fetch secrets in clusters    | Provider KMS semantics  |
| Portal and catalogue | Backstage                                               | One front door for teams                | Anything underneath     |
| Cost                 | FOCUS-formatted billing data, OpenCost                  | Comparable cost data across providers   | Pricing models          |

**Infrastructure as code: one workflow, many providers.** OpenTofu (the Linux Foundation fork created after Terraform moved to the BSL licence in 2023) and Terraform use a provider plugin per cloud, so a platform team writes modules in one language and runs one plan-and-apply workflow. The modules themselves are still provider-specific - an `aws_db_instance` is not an `azurerm_postgresql_flexible_server` - and that is correct. Crossplane takes a different approach: it runs inside Kubernetes and continuously reconciles cloud resources, and since Crossplane v2 a composition can expose one team-facing resource (say, `Database`) backed by different managed resources per provider.

**Kubernetes is the practical common denominator for compute.** The same Deployment runs on EKS, AKS, GKE, or on-premises. Each provider also has a way to manage clusters it does not host: Azure Arc and Azure Kubernetes Fleet Manager, GKE fleets with attached clusters, and EKS Hybrid Nodes for on-premises capacity joined to an EKS control plane. These help if one provider is primary; they add a dependency if you want neutrality.

**GitOps makes delivery identical everywhere.** Argo CD or Flux pulls desired state from Git into every cluster. The workflow for a team - merge a pull request, watch it reconcile - is the same regardless of provider. Per-cloud differences live in overlays, not in a separate pipeline.

**Standards beat products for data that crosses boundaries.** OpenTelemetry for telemetry and the FinOps Foundation's FOCUS specification for billing data both exist to make multi-provider data comparable. Adopting them is cheap and helps even in a single cloud.

**The trade-off.** Every neutral tool is one more thing the platform team runs, upgrades, and secures, and neutral tools rarely match the provider-native option's depth on its home cloud. The honest selection rule is: use a neutral tool where the workflow genuinely spans providers, and use native services where only one provider is involved.

**Name the user.** Application engineers should see one portal, one service specification, one deployment workflow, and one set of dashboards. Platform engineers are the users of the tools in the table - they absorb the per-provider differences so product teams do not have to.

## Example

```yaml
# One Argo CD ApplicationSet deploys the same service to every production
# cluster, on any provider. Differences live in a per-provider overlay.
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: payments-api
  namespace: argocd
spec:
  goTemplate: true
  goTemplateOptions: ["missingkey=error"]
  generators:
    - clusters:
        selector:
          matchLabels:
            platform.example.com/environment: prod
  template:
    metadata:
      name: "payments-api-{{.name}}"
    spec:
      project: payments
      source:
        repoURL: https://github.com/example-org/payments-deploy.git
        targetRevision: main
        # overlays/aws, overlays/azure, overlays/gcp hold storage class,
        # load balancer annotations, and workload identity bindings
        path: 'overlays/{{index .metadata.labels "platform.example.com/provider"}}'
      destination:
        server: "{{.server}}"
        namespace: payments
      syncPolicy:
        automated: { prune: true, selfHeal: true }
```

```text
What the overlay has to carry - the honest list of per-provider differences:

  overlays/aws     storageClassName: gp3; Service annotations for the AWS Load
                   Balancer Controller; ServiceAccount bound via EKS Pod Identity
  overlays/azure   storageClassName: managed-csi; ServiceAccount annotated with
                   azure.workload.identity/client-id
  overlays/gcp     storageClassName: standard-rwo; ServiceAccount mapped through
                   Workload Identity Federation for GKE

  The Deployment, the HPA, the PodDisruptionBudget, and the team's workflow are
  identical. Storage, load balancing, and identity are not - and the overlay is
  where the platform, not the team, absorbs that.
```

## Interview tips

- Answer by layer - compute, infrastructure, delivery, observability, identity, policy, cost - and name one or two tools per layer rather than listing brands.
- For each tool, say what it unifies and what it does not. "Terraform gives one workflow, not portable resources" is the kind of precision interviewers look for.
- Mention OpenTofu as the open-source fork after the 2023 licence change, and Crossplane v2 compositions as a way to present one team-facing resource over different providers.
- Name the open standards (OpenTelemetry, FOCUS, OIDC) as cheap wins that help even in a single cloud.
- Likely follow-up: "Would you use the provider's multi-cluster tool or a neutral one?" - answer that it depends on whether one provider is clearly primary. See [What is Crossplane and how does it differ from Terraform?](../control-planes-and-abstractions/what-is-crossplane-and-how-does-it-differ-from-terraform.md) for the IaC comparison.

---

[⬅ Back to Multi-Cloud and Hybrid Platforms](./README.md) · [All topics](../README.md)
