---
title: "What does AWS Control Tower set up for a platform?"
id: 147
category: "AWS Platform Engineering"
difficulty: "Beginner"
tags:
  - platform-engineering
  - aws-platform-engineering
  - interview-questions
---

# What does AWS Control Tower set up for a platform?

**Short answer:** Control Tower is AWS's managed service for building and running a **landing zone**: a governed multi-account environment on top of AWS Organizations. It sets up the organisation structure and central accounts for logging and audit, wires in centralised CloudTrail and AWS Config, integrates IAM Identity Center for sign-in, applies a catalogue of **controls** (preventive, detective, and proactive), and provides an **Account Factory** for creating new accounts that arrive already governed. It then detects drift from that baseline. It does not design your networking, your workload runtime, or your developer interface - those are still the platform's job.

## Detail

**What "landing zone" means.** Before any team deploys anything, a multi-account AWS estate needs the same foundations: somewhere logs go that workload accounts cannot tamper with, an account security teams can use to inspect everything, a way for humans to sign in without IAM users, baseline guardrails, and a repeatable way to add accounts. Control Tower automates that foundation and keeps it consistent, using AWS services underneath - Organizations, CloudTrail, Config, IAM Identity Center, CloudFormation StackSets, and Service Catalog.

**What it creates.**

| Piece                  | What you get                                                                      |
| ---------------------- | --------------------------------------------------------------------------------- |
| Organisation structure | OUs registered with Control Tower; a set of hub accounts for shared services      |
| Log archive account    | Central, restricted storage for CloudTrail and Config history                     |
| Audit account          | Cross-account read access for security tooling and reviewers                      |
| Identity               | IAM Identity Center configured, so people sign in with federated, temporary roles |
| Controls               | Mandatory controls plus a catalogue of optional ones you enable per OU            |
| Account Factory        | New accounts created into an OU with the baseline applied                         |
| Drift detection        | Visibility of non-compliant resources and of changes made outside Control Tower   |

**Controls come in three behaviours.** **Preventive** controls stop an action before it happens and are implemented as SCPs or RCPs - for example, disallowing changes to the log archive's retention. **Detective** controls find non-compliant resources after the fact using AWS Config rules - for example, S3 buckets without versioning. **Proactive** controls check resources at deployment time through CloudFormation hooks, before they are created. Each control has a guidance level (mandatory, strongly recommended, or elective), and the Control Catalog maps them to frameworks such as PCI DSS and NIST, which helps when an auditor asks how a requirement is met.

**It has become much less rigid.** Earlier versions imposed a fixed shape: a Security OU, mandatory Config and CloudTrail integrations, and a full baseline on every enrolled account. Landing zone version 4.0 (November 2025) made the Config, CloudTrail, security roles, and Backup integrations optional, dropped the requirement for a Security OU, and added a controls-only mode for organisations that already have a mature multi-account setup and want only the managed control catalogue. Automatic enrolment now applies an OU's baseline and controls when an account is moved into it. If someone tells you Control Tower "forces its structure on you", that was truer in 2022 than it is now.

**Account Factory, and how platforms extend it.** The console Account Factory is backed by Service Catalog and suits low volumes. Platform teams usually drive account creation from code instead: **Account Factory for Terraform (AFT)** lets you commit an account request to a Git repository and have a pipeline create the account and apply your own Terraform customisations, and Customizations for Control Tower does a similar job with CloudFormation. That extension point is where the platform adds what Control Tower does not - VPCs from a managed address pool, transit gateway attachments, budgets, and registration in the platform's inventory.

**Who uses it.** The direct users are the platform and security teams who own the landing zone. The indirect users are every product team: they get an account that is already logged, audited, and guarded, and they never have to know how. That is the value proposition to state in an interview.

**The trade-offs.**

- **Opinionated baseline.** You accept AWS's naming, StackSets, and roles. Changing Control Tower-managed resources by hand causes drift, which you then have to repair.
- **Upgrades are yours.** Landing zone versions are released by AWS but applied by you, and some updates require re-registering OUs or resetting controls. Budget time for them.
- **Not the whole platform.** Networking beyond a basic per-account VPC, workload identity, runtime choice, cost allocation, and the developer interface are all outside its scope.

The sensible default for a new AWS estate is to adopt Control Tower and extend it, and to build your own only if you can name a specific requirement it blocks.

## Example

```hcl
# An AFT account request. Committing this file is the whole request; the
# AFT pipeline creates the account in Control Tower, then runs the
# "workload-baseline" customisations (VPC, TGW attachment, budgets).
module "checkout_prod" {
  source = "./modules/aft-account-request"

  control_tower_parameters = {
    AccountEmail              = "aws+checkout-prod@example.com"
    AccountName               = "checkout-prod"
    ManagedOrganizationalUnit = "Prod (ou-ab12-3example)"
    SSOUserEmail              = "platform-admins@example.com"
    SSOUserFirstName          = "Platform"
    SSOUserLastName           = "Admins"
  }

  account_tags = {
    owner       = "team-payments"
    cost-centre = "eng-payments"
    environment = "production"
  }

  change_management_parameters = {
    change_requested_by = "team-payments"
    change_reason       = "New production account for the checkout service"
  }

  custom_fields = {
    tier = "1"
  }

  account_customizations_name = "workload-baseline"
}
```

```bash
# Enabling an optional control on an OU through the API rather than the console.
aws controltower enable-control \
  --control-identifier arn:aws:controlcatalog:::control/<control-id> \
  --target-identifier arn:aws:organizations::<management-account-id>:ou/o-exampleorgid/ou-ab12-3example

# Checking which accounts have drifted from their OU's baseline.
aws controltower list-enabled-baselines --include-children
```

```text
What a product team sees when their account is ready:

  sign in via IAM Identity Center      -> team-payments-admin (non-prod)
                                          team-payments-readonly (prod)
  CloudTrail + Config already on       -> delivered to log-archive
  preventive controls in force         -> e.g. cannot disable CloudTrail
  platform customisations applied      -> VPC 10.42.16.0/20, TGW attached,
                                          budget alerts to #team-payments
  time from merge to usable account    -> minutes, not a ticket queue
```

## Interview tips

- Define a landing zone first, then say Control Tower is the managed way to build one. It frames the answer.
- Know the three control behaviours - preventive (SCP/RCP), detective (Config), proactive (CloudFormation hooks) - and give one example of each.
- Mention landing zone 4.0's flexibility (optional integrations, no mandatory Security OU, controls-only mode). It shows your knowledge is current and defuses the "too rigid" objection.
- Be clear about the boundary: Control Tower governs accounts; it does not build networking, runtimes, or the developer interface. AFT customisations are where the platform plugs in.
- Take a position: adopt and extend unless a named requirement rules it out. See [account vending](./what-is-account-vending-and-how-do-you-automate-it.md) for the automation that sits on top.

---

[⬅ Back to AWS Platform Engineering](./README.md) · [All topics](../README.md)
