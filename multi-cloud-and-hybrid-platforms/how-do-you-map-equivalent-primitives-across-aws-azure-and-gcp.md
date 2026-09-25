---
title: "How do you map equivalent primitives across AWS, Azure, and GCP?"
id: 191
category: "Multi-Cloud and Hybrid Platforms"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - multi-cloud-and-hybrid-platforms
  - interview-questions
---

# How do you map equivalent primitives across AWS, Azure, and GCP?

**Short answer:** Map by role rather than by name, and be explicit that several of the most important mappings are approximate rather than equivalent - particularly the organisational hierarchy, the identity model, and networking. Compute and storage map cleanly; IAM does not. The value of the exercise is not a lookup table but knowing which rows you can rely on and which will bite you during a migration or a design review.

## Detail

**Where the mapping is genuinely clean:** container orchestration, serverless containers, object storage, managed relational databases, queues, and secret storage all have close counterparts with comparable roles. Someone who knows one provider's version can reason about another's, and the differences are features rather than concepts.

**Where it is approximate and the differences matter:**

- **The account hierarchy.** An AWS account, an Azure subscription, and a GCP project all serve as an isolation and billing boundary, but their groupings differ: organisational units, management groups, and folders each have different inheritance and policy semantics. A design that assumes one behaves like another produces a structure that cannot enforce what you intended.
- **Identity.** AWS IAM evaluates policies attached to principals and resources with explicit deny precedence. Azure separates Entra ID authentication from Azure RBAC role assignments on a resource hierarchy. GCP binds roles to principals at a resource level with inheritance down the hierarchy. These are three different mental models, not three syntaxes for the same one, and this is where multi-cloud designs most often go wrong.
- **Networking.** VPCs, VNets, and GCP's global VPC differ in fundamentals - GCP's VPC is global with regional subnets, while the others are regional constructs. Peering transitivity, private connectivity to managed services, and egress control all work differently.

**The mapping worth carrying, by role:**

| Role                     | AWS                        | Azure                       | GCP                          |
| ------------------------ | -------------------------- | --------------------------- | ---------------------------- |
| Isolation / billing unit | Account                    | Subscription                | Project                      |
| Grouping for policy      | Organisational unit        | Management group            | Folder                       |
| Guardrail mechanism      | SCP / RCP                  | Azure Policy                | Organisation policy          |
| Managed Kubernetes       | EKS                        | AKS                         | GKE                          |
| Serverless containers    | Fargate / ECS Express Mode | Container Apps              | Cloud Run                    |
| Functions                | Lambda                     | Functions                   | Cloud Run functions          |
| Object storage           | S3                         | Blob Storage                | Cloud Storage                |
| Managed relational       | RDS / Aurora               | Azure SQL / PostgreSQL      | Cloud SQL / AlloyDB          |
| Queue                    | SQS                        | Service Bus / Storage Queue | Pub/Sub                      |
| Secret storage           | Secrets Manager            | Key Vault                   | Secret Manager               |
| Workload identity        | EKS Pod Identity / IRSA    | Entra Workload ID           | Workload Identity Federation |
| Private service access   | VPC endpoints              | Private endpoints           | Private Service Connect      |
| Private DNS              | Route 53 private zones     | Private DNS zones           | Cloud DNS private zones      |
| Managed observability    | CloudWatch                 | Azure Monitor               | Google Cloud Observability   |

Two rows have moved recently: AWS App Runner stopped accepting new customers on 30 April 2026 (existing users keep it, with no new features), and AWS points new simple container workloads at Amazon ECS Express Mode instead; and Google renamed Cloud Functions to Cloud Run functions, which now run on the Cloud Run platform.

**Use the mapping for reasoning, not for design.** It is genuinely useful for transferring knowledge, for a comparative interview answer, and for scoping a migration. It is dangerous as the basis of an abstraction layer, because the rows that look equivalent hide the semantic differences that actually break applications.

**The guardrail row is the one people misjudge most.** Service control policies bound the maximum available permissions of principals and grant nothing; resource control policies (RCPs) apply the same idea to resources, capping what can be done to them regardless of who asks - for example, blocking access from identities outside the organisation. Azure Policy can deny, audit, and also remediate by deploying or modifying resources. GCP organisation policies constrain resource configuration. These are three different capabilities - Azure Policy's ability to fix rather than reject has no direct counterpart, and designing as though they are the same mechanism leads to a guardrail strategy that does not translate.

**Be honest about what does not map at all.** Higher-level managed platform services - analytics, machine learning, data warehousing - have no adequate equivalents, and pretending otherwise is how migration estimates go badly wrong. Those are rebuilds, not ports.

## Example

```text
The same platform requirement, expressed natively three ways. Note that the
STRUCTURE differs, not just the names.

REQUIREMENT  "production workloads must not have public IP addresses, must be in
              approved regions, and must not permit long-lived credentials"

AWS
  boundary   one account per workload per environment
  grouping   OU: Workloads/Prod
  guardrail  Service control policy on the OU:
               Deny ec2:RunInstances with AssociatePublicIpAddress
               Deny NotAction[global services] when aws:RequestedRegion not in [...]
               (no direct equivalent for "no long-lived keys" - use IAM policy
                plus detection, or deny iam:CreateAccessKey)
  identity   IAM roles + OIDC federation from the cluster

AZURE
  boundary   one subscription per workload per environment
  grouping   MG: Landing Zones/Corp
  guardrail  Azure Policy on the management group:
               Deny public IP resources
               Deny locations not in allowed list
               Deny/Modify to prevent credential-based auth on PaaS
             PLUS DeployIfNotExists to REMEDIATE, which has no direct
             counterpart on the other two - a real capability difference.
  identity   Entra ID + Azure RBAC role assignments + workload identity federation

GCP
  boundary   one project per workload per environment
  grouping   folder: workloads/prod
  guardrail  Organisation policies on the folder:
               compute.vmExternalIpAccess = denyAll
               gcp.resourceLocations = allowed regions
               iam.disableServiceAccountKeyCreation = true
             The third one is a single boolean that makes long-lived keys
             impossible - cleaner than either equivalent above.
  identity   IAM role bindings with hierarchy inheritance + Workload Identity

  Same requirement, three genuinely different mechanisms. The guardrail row is
  where they diverge most: Azure can remediate, GCP has a purpose-built
  constraint for keys, AWS bounds maximum permissions. An abstraction over these
  three would have to be the intersection, which loses the best feature of each.
```

## Interview tips

- Map by role rather than by name, and say up front that some rows are approximate. Presenting the table as a set of equivalences is the weak version.
- Identity is the row to single out as genuinely non-equivalent - three different mental models, not three syntaxes. That is where multi-cloud designs fail.
- The guardrail row is the second: Azure Policy remediates, GCP has purpose-built constraints, AWS bounds maximum permissions. Naming those as capability differences shows real comparative knowledge.
- GCP's global VPC versus regional constructs elsewhere is a concrete networking difference worth having ready.
- Say the mapping is for reasoning and migration scoping, not for building an abstraction layer - because the rows that look equivalent hide the semantics that break applications.
- Be clear that higher-level analytics and machine learning services do not map at all, and that treating them as ports rather than rebuilds is how migration estimates go wrong.

---

[⬅ Back to Multi-Cloud and Hybrid Platforms](./README.md) · [All topics](../README.md)
