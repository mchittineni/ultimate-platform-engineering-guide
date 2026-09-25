---
title: "What is infrastructure as code?"
id: 66
category: "Control Planes and Abstractions"
difficulty: "Beginner"
tags:
  - platform-engineering
  - control-planes-and-abstractions
  - interview-questions
---

# What is infrastructure as code?

**Short answer:** Infrastructure as code (IaC) means describing servers, networks, databases, and permissions in text files that a tool reads and turns into real infrastructure, instead of clicking through a console or running one-off commands. Because the description is code, it can be version-controlled, reviewed, tested, and applied the same way every time. It is what makes a platform repeatable, since the definition of an environment becomes something you can copy, diff, and audit.

## Detail

**The problem it replaces.** Without IaC, infrastructure is built by hand: someone logs into the cloud console, creates a database, picks some settings, and moves on. Six months later nobody knows why that database has those settings, the staging copy was built slightly differently, and rebuilding it after a disaster means working from memory. IaC turns the knowledge in people's heads into a file that describes exactly what exists and why.

**Declarative versus imperative.** Most modern IaC is _declarative_: you describe the end state you want ("a bucket called `receipts` with versioning on") and the tool works out which API calls get there. _Imperative_ tools and scripts describe the steps ("create the bucket, then enable versioning"). Declarative definitions are easier to review and safer to re-run, because running the same file twice should change nothing the second time. That property, _idempotency_, is what lets you apply the same definition to ten environments with confidence.

**How a declarative tool works.** It reads your files, reads the current state of the real infrastructure, and computes the difference. Run-to-completion tools such as Terraform and OpenTofu show that difference as a _plan_, apply it when you approve, and then stop. Reconciling tools such as Crossplane keep running and correct differences continuously. Both are IaC; they differ in when the comparison happens.

**The main tool families:**

| Family                    | Examples                                              | Notes                                                         |
| ------------------------- | ----------------------------------------------------- | ------------------------------------------------------------- |
| Declarative, multi-cloud  | Terraform, OpenTofu                                   | HCL files, huge provider ecosystem, explicit plan             |
| Cloud-native declarative  | AWS CloudFormation, Azure Bicep, GCP Config Connector | One cloud only, deeply integrated with it                     |
| General-purpose languages | Pulumi, AWS CDK                                       | Loops and abstractions in TypeScript, Python, Go              |
| Kubernetes control planes | Crossplane, cloud controllers (ACK, ASO)              | Infrastructure as Kubernetes objects, reconciled continuously |

**What you gain.** Every change goes through a pull request, so there is review and a history of who changed what and why. Environments can be recreated from scratch. Standards - encryption on, backups on, tags present - can be written once into a shared module and inherited by every team. And automated checks can scan the definitions for security problems before anything is created.

**What it costs.** IaC is only as good as the discipline around it. If people still change things in the console, the real infrastructure _drifts_ from the code and the next apply may undo their fix or fail in confusing ways. Run-to-completion tools also need somewhere to keep track of what they created (Terraform's state file), and that record needs protecting. And a shared module that forty teams depend on is a product in its own right, needing versioning and tests.

**Who the user is.** In a platform, the platform team usually writes the IaC building blocks - the network, the clusters, the approved database module - and application teams consume them, either by calling a module with a few inputs or by requesting a resource through a self-service API that runs IaC underneath. The platform's job is to make the safe configuration the easiest one to ask for.

## Example

```hcl
# main.tf - a versioned, encrypted bucket declared as code.
terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.0" }
  }
}

provider "aws" {
  region = "eu-west-1"
}

resource "aws_s3_bucket" "receipts" {
  bucket = "example-payments-receipts-prod"
  tags = {
    team        = "payments"
    environment = "prod"
    managed-by  = "terraform"
  }
}

resource "aws_s3_bucket_versioning" "receipts" {
  bucket = aws_s3_bucket.receipts.id
  versioning_configuration {
    status = "Enabled"
  }
}
```

```text
$ terraform plan
  + aws_s3_bucket.receipts             will be created
  + aws_s3_bucket_versioning.receipts  will be created
Plan: 2 to add, 0 to change, 0 to destroy.

$ terraform apply     # after review; creates both resources

$ terraform plan      # run again with no edits
No changes. Your infrastructure matches the configuration.
                      ^ idempotency: the same file is safe to re-run
```

## Interview tips

- Define it by the mechanism: a declared desired state, a tool that compares it to reality, and an apply step. Then give the benefits - review, history, repeatability.
- Explain declarative versus imperative and use the word idempotent. It is the property that makes IaC safe to run repeatedly across environments.
- Name drift as the main failure mode: console changes that the code does not know about. Interviewers often follow up with "how would you detect it?" - scheduled plans, or a reconciling controller (see [configuration drift](../gitops-and-continuous-delivery/what-is-configuration-drift-and-how-does-a-platform-detect-it.md)).
- Say who uses it in a platform: the platform team builds modules and APIs, application teams consume them without needing to be cloud experts.
- Expect a follow-up on Terraform versus a reconciling control plane such as Crossplane; "run to completion versus continuous reconciliation" is the one-line answer.

---

[⬅ Back to Control Planes and Abstractions](./README.md) · [All topics](../README.md)
