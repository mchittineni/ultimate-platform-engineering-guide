---
title: "What is the difference between Terraform and OpenTofu?"
id: 69
category: "Control Planes and Abstractions"
difficulty: "Beginner"
tags:
  - platform-engineering
  - control-planes-and-abstractions
  - interview-questions
---

# What is the difference between Terraform and OpenTofu?

**Short answer:** OpenTofu is an open-source fork of Terraform, created in 2023 after HashiCorp moved Terraform from the Mozilla Public License to the Business Source License (BSL). OpenTofu stayed under MPL 2.0 and is governed by the Linux Foundation, and it has since joined the CNCF. The two share the same language (HCL), workflow, and provider ecosystem, so most configurations run on either, but they are now separate projects adding different features - and the choice is mainly about licensing, governance, and which features and commercial services you need.

## Detail

**Why the fork happened.** In August 2023 HashiCorp relicensed Terraform (from version 1.6 onwards) under the BSL, which permits most use but restricts offering a competing product. Companies building on Terraform - and many users worried about depending on a single vendor's licence decisions - forked the last MPL release (1.5.x) as OpenTofu. HashiCorp itself was later acquired by IBM, a deal completed in 2025. For most organisations that simply _use_ Terraform to manage their own infrastructure, the BSL does not stop them; the concern is more about long-term control and vendor neutrality.

**What is the same.** Both read `.tf` files written in HCL. Both have `init`, `plan`, and `apply`. Both use providers - the plugins that talk to AWS, Azure, Google Cloud, GitHub, and so on - and the same providers generally work with both, because providers are separate projects. OpenTofu runs its own registry that mirrors the public providers and modules. State files from Terraform 1.5 onwards can be migrated to OpenTofu, and for most setups switching is a matter of replacing the binary and re-running `init`.

**What has diverged.** Each project now ships features the other does not, or ships them differently:

| Area                       | Terraform                                             | OpenTofu                                                               |
| -------------------------- | ----------------------------------------------------- | ---------------------------------------------------------------------- |
| Licence                    | BSL 1.1 (source-available)                            | MPL 2.0 (open source)                                                  |
| Governance                 | HashiCorp, an IBM company                             | Linux Foundation, CNCF project, community steering                     |
| CLI binary                 | `terraform`                                           | `tofu`                                                                 |
| State encryption           | Relies on backend encryption                          | Built-in client-side state encryption                                  |
| Distinctive features       | Stacks and other HCP Terraform integrations           | Provider `for_each`, `-exclude` targeting, the `enabled` meta-argument |
| Shared, shipped separately | Ephemeral values and write-only arguments (1.10-1.11) | Ephemeral values and write-only arguments (1.11)                       |
| Commercial platform        | HCP Terraform and Terraform Enterprise                | Third-party services (Spacelift, env0, Scalr and others)               |

**The practical risk of divergence.** As the two drift apart, a configuration that uses a feature only one of them has will not run on the other. If a team adopts OpenTofu's state encryption or a Terraform feature OpenTofu has not matched, they have effectively chosen a side. Even features both sides now have - ephemeral values and write-only arguments, for instance - arrived at different versions, so the minimum version you pin matters. Module authors who want to support both have to stick to the common subset and test against both binaries.

**How organisations choose.** Teams already invested in HCP Terraform or Terraform Enterprise - for policy, private registries, and run management - usually stay. Teams that want an open-source licence, vendor-neutral governance, or specific OpenTofu features such as state encryption often move. Many platform teams also consider the people angle: "Terraform" is the familiar name on CVs, but HCL skills transfer directly, so hiring is rarely the deciding factor.

**Who the user is.** For application teams consuming the platform's modules, the difference is often invisible - they call the same module with the same inputs. The choice mostly affects the platform team, who own the runner, the pipeline, the module library, and any commercial platform around them.

## Example

```hcl
# versions.tf - written to run on either tool.
terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws" # resolves on both registries
      version = "~> 6.0"
    }
  }
}
```

```text
Switching a workspace from Terraform to OpenTofu:

  $ terraform plan              # confirm no pending changes first
  No changes.

  $ tofu init                   # same backend, same state file
  $ tofu plan
  No changes. Your infrastructure matches the configuration.

Things to check before switching:
  - Terraform version the state was written by (fork point is 1.5.x;
    newer state generally migrates, but read the migration guide
    for your exact version)
  - any Terraform-only features in use (e.g. HCP Terraform Stacks)
  - CI images and pipeline steps that call `terraform` by name
  - policy or run tooling tied to HCP Terraform
```

```hcl
# An OpenTofu-only feature: client-side state encryption.
# This file will NOT work with the terraform binary.
terraform {
  encryption {
    key_provider "aws_kms" "main" {
      kms_key_id = "a4f791e1-0d46-4c8e-b489-917e0bec05ef" # a dedicated state key
      region     = "eu-west-1"
      key_spec   = "AES_256"
    }
    method "aes_gcm" "main" {
      keys = key_provider.aws_kms.main
    }
    state {
      method = method.aes_gcm.main
    }
  }
}
```

## Interview tips

- Get the history right: BSL change in 2023, OpenTofu forked from 1.5.x under MPL 2.0, Linux Foundation governance. IBM owning HashiCorp is worth a mention.
- Stress what is shared - HCL, the plan/apply workflow, and providers - so it is clear this is not a different tool to learn.
- Then explain divergence as the real long-term risk: using a feature only one side has locks you in.
- Avoid framing it as good versus bad. A balanced answer names who should stay (HCP Terraform users) and who might move (licence or neutrality concerns, state encryption).
- A likely follow-up is how you would migrate safely: a clean plan first, one workspace at a time, pinned binary versions in CI.

---

[⬅ Back to Control Planes and Abstractions](./README.md) · [All topics](../README.md)
