---
title: "How do you handle a live infrastructure-as-code exercise?"
id: 258
category: "Platform Engineering Interviews"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-engineering-interviews
  - interview-questions
---

# How do you handle a live infrastructure-as-code exercise?

**Short answer:** Treat it as designing an interface other engineers will consume, not as typing resources from memory. Clarify who calls the module and what must never be configurable, sketch the inputs and outputs first, build the smallest version that plans cleanly, then add validation, secure defaults, and a test - narrating each decision and its trade-off. The exercise is checking whether you write infrastructure code that is safe to hand to forty teams, and whether you can reason about state, change, and failure, far more than whether you remember every argument name.

## Detail

**Know the common formats.** A blank-editor task ("write a module for a standard bucket", "a VPC with public and private subnets"), a review task ("here is a module, what would you change?"), a debugging task (a failing plan, a state problem, a drift surprise), or an extension task ("add support for a second region without breaking existing callers"). Most are Terraform or OpenTofu; some use Pulumi, CDK, Bicep, or Kubernetes manifests and Helm. Ask which tool, and whether you will run real `plan` commands or work on paper, before the day.

**Clarify the consumer first.** Who calls this module, how many of them, and what do they care about? Which settings are policy - encryption, public access, tagging - and must not be exposed? This is the platform-specific move and it takes two minutes: a module with no encryption toggle cannot be used to create an unencrypted bucket, which is a stronger control than a policy that rejects one.

**Write the interface before the resources.** Variables with types, descriptions, and `validation` blocks; outputs that callers will actually need. Saying "I am starting with the interface because that is the contract every caller encodes" is a strong opening and it also keeps you from sprawling.

**Get to a clean plan early.** Build the minimum that validates and plans, then iterate. A half-finished ambitious module scores worse than a small complete one, and running `fmt`, `validate`, and `plan` as you go shows a working habit rather than a performance.

**Know the current idioms.** Since AWS provider 4, S3 bucket settings are separate resources (`aws_s3_bucket_versioning`, `aws_s3_bucket_server_side_encryption_configuration`, `aws_s3_bucket_public_access_block`). New buckets are encrypted and block public access by default, so explicitly setting them is about making intent visible and resisting later change, and it is worth saying so. Use `moved`, `import`, and `removed` blocks rather than hand-edited state for refactors. Use native `terraform test` / `tofu test` with `.tftest.hcl` files, and mock providers so tests run without credentials. Recent Terraform and OpenTofu releases lock S3-backend state with a lock file in the bucket, making the separate DynamoDB lock table unnecessary.

**Talk about state and change, even if not asked.** Where state lives, how it is locked, who can read it (it can contain secrets), what happens when two people apply, and which changes force replacement. Pointing out that renaming a resource address would destroy and recreate a bucket without a `moved` block is exactly the kind of experience-derived remark that lifts an answer.

**Handle the AI policy deliberately.** If assistants are banned, do not use one, and do not keep one running in another window - many interviewers can tell, and it is usually disqualifying. If they are allowed, use them for boilerplate and say so, then review the output out loud: generated infrastructure code frequently uses deprecated inline arguments, invents attributes, or omits the security settings that matter. Catching that is the skill being assessed.

**Work well in a remote setting.** Share the editor and terminal at a readable font size, say what you are about to do before doing it, and do not go silent for long stretches while you read documentation - say what you are looking up. Looking up an argument name is fine; everyone does it.

**Trade-offs worth naming.** Exposing more variables makes a module flexible and makes it harder to guarantee policy; fewer variables make it safer and push edge cases to an escape hatch. Wrapping every resource in a module adds indirection; not wrapping duplicates policy. Tests against mocks are fast and catch interface mistakes, but only a real apply in a sandbox catches provider behaviour.

## Example

```hcl
# modules/standard-bucket/main.tf
# Consumer: product teams needing an artefact or data bucket.
# Policy is not configurable: encryption, versioning, and public access block
# are always on. Callers choose a name, an owner, and a retention class.

terraform {
  required_version = ">= 1.7"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

variable "name" {
  type        = string
  description = "Bucket name; must be globally unique."
  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{2,62}$", var.name))
    error_message = "Use 3-63 lowercase letters, digits, or hyphens."
  }
}

variable "owner_team" {
  type        = string
  description = "Owning team, used for cost allocation and alert routing."
}

resource "aws_s3_bucket" "this" {
  bucket = var.name
  tags = {
    owner      = var.owner_team
    managed-by = "platform-standard-bucket"
  }
}

resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "this" {
  bucket                  = aws_s3_bucket.this.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

output "bucket_arn" {
  value = aws_s3_bucket.this.arn
}
```

```hcl
# modules/standard-bucket/tests/standard_bucket.tftest.hcl
# Runs with `terraform test` (1.7+) or `tofu test` (1.8+); the mock provider
# means no cloud credentials are needed.

mock_provider "aws" {}

run "versioning_is_always_on" {
  command = plan
  variables {
    name       = "checkout-artefacts"
    owner_team = "checkout"
  }
  assert {
    condition     = aws_s3_bucket_versioning.this.versioning_configuration[0].status == "Enabled"
    error_message = "Versioning must be enabled on every standard bucket."
  }
}

run "rejects_invalid_names" {
  command = plan
  variables {
    name       = "Checkout_Artefacts"
    owner_team = "checkout"
  }
  expect_failures = [var.name]
}
```

```text
What to say while writing it - the narration is half the score.

  "Interface first: two inputs. Note there is no encryption or public-access
   variable. That is deliberate - a caller cannot create a non-compliant bucket."
  "S3 already encrypts and blocks public access by default for new buckets. I
   still set both explicitly so the intent is visible in review and a console
   change shows up as drift."
  "Trade-off: a team with a genuine need for a public bucket cannot use this.
   That is what an escape hatch with a recorded exception is for; I would not
   add a toggle."
  "If I later rename aws_s3_bucket.this, I would add a moved block. Without it
   the plan destroys and recreates the bucket, and versioning will not save
   you from that."
  "Next, with more time: a lifecycle rule per retention class, and a sandbox
   apply in CI, because mocks will not catch provider behaviour."
```

## Interview tips

- Ask who consumes the module before writing anything. Designing for forty callers is the platform lens, and it is what separates this from a generic IaC test.
- Write variables, validation, and outputs first. The interface is the contract, and starting there keeps the scope sensible.
- Get to a clean `validate` and `plan` early, then iterate. Small and complete beats ambitious and broken.
- Volunteer state and change: locking, secrets in state, forced replacement, and `moved` blocks. These are the areas that reveal real experience.
- Use current idioms - split S3 resources, native tests with mock providers, `import` and `removed` blocks - and mention OpenTofu compatibility if the team uses it.
- Follow the AI policy exactly. If assistants are allowed, review their output out loud, because spotting deprecated or insecure generated code is the skill being tested.
- Look things up openly and narrate while you do. Silent searching on a video call reads as being stuck; "checking the argument name for the key alias" does not.
- Related reading: [How do you manage Terraform at platform scale?](../control-planes-and-abstractions/how-do-you-manage-terraform-at-platform-scale.md)

---

[⬅ Back to Platform Engineering Interviews](./README.md) · [All topics](../README.md)
