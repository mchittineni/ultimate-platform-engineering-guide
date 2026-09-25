---
title: "What is cost allocation tagging and why does it fail?"
id: 226
category: "Platform FinOps"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-finops
  - interview-questions
---

# What is cost allocation tagging and why does it fail?

**Short answer:** Cost allocation tagging means attaching key-value metadata - `team`, `service`, `environment`, `cost-centre` - to cloud resources so the bill can be grouped by owner. It fails because tags are applied by people after the fact, many resources cannot be tagged or do not inherit tags, values drift through typos and reorganisations, and tags are not retroactive. The fix is to stop relying on people remembering: enforce tags at provisioning time, apply them automatically from the platform, and use account or project boundaries as the primary allocation key, with tags as a second layer.

## Detail

**How it works.** Every major cloud lets you attach tags (AWS, Azure) or labels (GCP) to resources. You then activate the chosen keys for billing - on AWS they must be activated as cost allocation tags before they appear in cost data - and the billing export gains a column per key. A report can then say "team-payments spent this much on compute". In Kubernetes the equivalent is labels on namespaces and workloads, which cost tools such as OpenCost read to split cluster cost.

**Why it fails, in the order it usually happens:**

- **Tagging is optional by default.** An engineer creating a resource in the console, or in infrastructure code without a module, simply leaves tags off. Nothing stops them.
- **Values drift.** `payments`, `Payments`, `team-payments`, and `paymnets` are four different teams to a billing report. A reorganisation renames teams and nobody retags.
- **Not everything can be tagged.** Some charges - support fees, some data transfer, taxes, certain marketplace items - carry no resource to tag. Some resources created indirectly (snapshots, volumes created by a controller, load balancers created by Kubernetes) do not inherit the tags of the thing that made them.
- **Tags are not retroactive.** Usage is attributed by the tags a resource carried at the time it was billed. AWS can backfill a newly _activated_ key for up to twelve months, but only where the tag was already on the resource - a tag first applied in June does not explain March.
- **Shared resources have no single owner.** A shared cluster, a transit gateway, or an observability pipeline cannot be tagged with one team, because it serves all of them.

**Tags should be the second layer, not the first.** An account (AWS), subscription (Azure), or project (GCP) per team and environment is a much more reliable allocation key, because every resource in it is attributed automatically and nobody can forget. Tags then subdivide within an account - by service or component - where the stakes of a missing tag are smaller.

**Enforce at the point of creation.** Preventive controls beat clean-up reports. AWS tag policies standardise keys and allowed values, and service control policies can deny creation without a required tag; Azure Policy can deny or append tags; GCP organisation policies and Terraform or OpenTofu modules can require labels. In Kubernetes, an admission policy can reject workloads without an owner label.

**Better still, let the platform apply them.** If every resource is created through a platform module, template, or service specification, the platform knows the owner already and stamps the tags itself. The user - a product engineer - never types a tag and cannot get one wrong. This is why tag compliance tends to be high on the paved road and poor everywhere else.

**Measure coverage and publish it.** The percentage of spend with a valid owner is the credibility number for every cost report you produce. Report it per account and chase the biggest untagged lines, not the longest list of untagged resources.

**The trade-off:** strict enforcement blocks people. A denial with no clear message at 5pm on a release day produces a support ticket and resentment. Roll out in audit mode first, give a clear error that says which tag is missing and what values are allowed, and provide the module that does it for them.

## Example

```hcl
# The platform's AWS provider configuration stamps owner tags on every resource
# the module creates. Product engineers never type a tag.
provider "aws" {
  region = "eu-west-2"

  default_tags {
    tags = {
      team        = var.team         # validated against the service catalogue
      service     = var.service
      environment = var.environment
      managed-by  = "platform"
    }
  }
}
```

```yaml
# Kubernetes: reject workloads that do not name an owning team.
# ValidatingAdmissionPolicy is GA since Kubernetes 1.30.
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata:
  name: require-team-label
spec:
  failurePolicy: Fail
  matchConstraints:
    resourceRules:
      - apiGroups: ["apps"]
        apiVersions: ["v1"]
        operations: ["CREATE", "UPDATE"]
        resources: ["deployments", "statefulsets"]
  validations:
    - expression: "has(object.metadata.labels) && 'team' in object.metadata.labels"
      message: "Add a 'team' label naming the owning team from the service catalogue."
---
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicyBinding
metadata:
  name: require-team-label
spec:
  policyName: require-team-label
  validationActions: ["Audit", "Warn"] # move to ["Deny"] once coverage is high
```

```text
Tag coverage report - the number that decides whether anyone trusts the rest.

  ACCOUNT                SPEND SHARE   VALID OWNER TAG   BIGGEST GAP
  payments-prod               22%            99%          -
  shared-networking           14%             0%          transit gateway (shared:
                                                          needs an allocation rule,
                                                          not a tag)
  data-platform-prod          18%            71%          EBS snapshots created by
                                                          backup controller
  legacy-sandbox               6%            12%          console-created instances
  ---------------------------------------------------------------------------
  Estate: 83% of spend has a valid owner. Target: 95%.
```

## Interview tips

- Define tagging in one sentence, then spend most of the answer on why it fails. That is what the interviewer is really asking.
- The strongest point is that accounts or projects should be the primary allocation key and tags the secondary one.
- Distinguish preventive controls (tag policies, deny-on-create, admission policies) from detective ones (reports), and say preventive wins.
- Mention that shared resources cannot be solved by tagging at all - they need an allocation rule. See [How do you attribute shared platform cost to teams?](./how-do-you-attribute-shared-platform-cost-to-teams.md).
- Name the user: when the platform stamps tags from the service catalogue, product engineers never touch them.
- A good follow-up to anticipate: "What about Kubernetes?" - labels on namespaces and workloads, read by a cost allocation tool. See [Why is Kubernetes cost allocation hard?](./why-is-kubernetes-cost-allocation-hard.md).

---

[⬅ Back to Platform FinOps](./README.md) · [All topics](../README.md)
