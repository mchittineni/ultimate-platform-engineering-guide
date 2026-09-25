---
title: "What is a GCP project and why is it the unit of isolation?"
id: 172
category: "GCP Platform Engineering"
difficulty: "Beginner"
tags:
  - platform-engineering
  - gcp-platform-engineering
  - interview-questions
---

# What is a GCP project and why is it the unit of isolation?

**Short answer:** A project is the container every GCP resource lives in - each VM, bucket, database, and cluster belongs to exactly one. It is also where APIs are enabled, quotas are counted, billing is attributed, and IAM is most commonly granted, so putting two workloads in separate projects separates almost everything about them at once. That is why a platform gives each workload its own project per environment, rather than trying to divide one project with permissions.

## Detail

**What a project actually is.** A project is a node in the resource hierarchy - organisation, then folders, then projects - and the parent of every resource inside it. It has three identifiers worth knowing: a **project ID** you choose (globally unique, lowercase, and permanent once set), a **project number** Google assigns and uses internally in many resource names and service accounts, and a **display name** you can change freely. Scripts and policies should use the ID or number, never the display name.

**Why "unit of isolation" is literal, not a figure of speech.** Look at what is scoped to the project:

| Scoped to the project | What separation buys you                                                      |
| --------------------- | ----------------------------------------------------------------------------- |
| Enabled APIs          | A workload can only use services switched on in its own project               |
| Quotas                | One team exhausting CPUs or IP addresses does not starve another              |
| Billing               | Costs attribute cleanly to one workload and one owner                         |
| IAM                   | A role granted on the project covers its resources and nothing else           |
| Audit logs            | Each project has its own admin activity trail                                 |
| Deletion              | Deleting the project removes everything in it, after a recovery window        |
| Service accounts      | Created inside a project, so a workload's identities travel with the workload |

If two teams share a project, they share every row in that table. You can try to separate them with fine-grained IAM on individual resources, but the quotas, API enablement, and billing remain shared, and one over-broad role grant exposes both teams. Separate projects make the boundary structural instead of something maintained by careful review.

**Folders sit above projects to carry policy.** A project inherits IAM bindings and organisation policies from its folder and organisation. That is why placement matters: a project created under `workloads/prod` automatically gets the production guardrails - no public IPs, no service account keys, approved regions only - while one created in the wrong folder gets none of them. The hierarchy design is covered in [How do you structure a GCP platform with folders, projects, and organisation policies?](./how-do-you-structure-a-gcp-platform-with-folders-projects-and-organisation-policies.md).

**What a project does not isolate.** Networking is the notable exception. With Shared VPC, many service projects deliberately use subnets owned by one host project, so the network boundary is set by firewall rules and subnet permissions rather than by project lines. Data can also be shared across projects on purpose - a BigQuery dataset readable by another project, a Pub/Sub subscription in a different project from its topic. The project draws a strong default boundary, and cross-project access is something you grant explicitly.

**Deletion is a clean offboarding primitive.** Shutting down a project stops its resources and schedules it for deletion after a recovery period of roughly thirty days, during which it can be restored. That makes "delete the project" a realistic way to retire a workload completely - something that is hard to do when workloads share. A lien can be placed on a critical project to block accidental deletion.

**Who uses this, and what the platform gives them.** The users are product teams. They should not create projects by hand; they request one - by filling in a small form or a YAML file - and the platform's project vending creates it in the right folder, links billing, enables the APIs they declared, attaches the network, and binds their group. What that saves them is days of tickets and the class of "works in dev, fails in the new project" surprises. See [How do you automate project vending on GCP?](./how-do-you-automate-project-vending-on-gcp.md).

**The trade-off.** More projects means more things to manage: more budgets, more quota requests, more IAM bindings, more places for a baseline to drift. That cost is only acceptable because it is automated. A platform that preaches one project per workload per environment but vends projects by hand ends up with teams quietly sharing projects to avoid the wait - and the isolation model stops being true.

## Example

```bash
# Create a project in the production workloads folder. The project ID is
# permanent; choose a naming convention before the first one.
gcloud projects create checkout-prod \
  --folder=482093415560 \
  --name="Checkout (production)" \
  --labels=tenant=team-payments,environment=production,cost-centre=eng-payments

# Link billing - a project without billing fails in confusing ways.
gcloud billing projects link checkout-prod --billing-account=01A2B3-C4D5E6-F7A8B9

# APIs are off until enabled per project: the classic "works in dev" surprise.
gcloud services enable run.googleapis.com sqladmin.googleapis.com \
  secretmanager.googleapis.com --project=checkout-prod

# Grant the owning team's GROUP (never individuals) a role on this project only.
gcloud projects add-iam-policy-binding checkout-prod \
  --member="group:team-payments@example.com" \
  --role="roles/viewer"
```

```text
One workload per environment per project - what isolation looks like in practice:

  folder workloads/prod
    checkout-prod     quota: 400 vCPU (europe-west1)   billing: eng-payments
    search-prod       quota: 900 vCPU (europe-west1)   billing: eng-search

  search runs a runaway batch job and hits its CPU quota:
    search-prod       -> new instances fail with QUOTA_EXCEEDED
    checkout-prod     -> unaffected; its quota is its own

  the same incident in one shared project:
    shared-prod       -> BOTH teams fail to scale, during checkout's peak
```

## Interview tips

- Open with the list of what is project-scoped - APIs, quotas, billing, IAM, audit logs, deletion. That list is the whole argument for why the project is the unit of isolation.
- Distinguish the project ID, number, and display name, and note the ID is permanent. It is a small detail that shows you have created projects rather than read about them.
- Explain that folders exist to attach policy, so placement determines guardrails. A project in the wrong folder is a project without guardrails.
- Name the exception: networking under Shared VPC deliberately crosses project lines, so the project is a strong default boundary rather than an absolute one.
- Expect the follow-up "doesn't that create a lot of projects?" The answer is yes, which is why vending must be automated - manual vending is how teams end up sharing.
- Compare briefly if asked: the project plays the role an AWS account plays in a [multi-account design](../aws-platform-engineering/how-do-you-structure-a-multi-account-aws-platform.md), and an [Azure subscription](../azure-platform-engineering/what-is-an-azure-subscription-and-why-is-it-the-unit-of-a-landing-zone.md) plays in a landing zone - though a GCP project is much lighter-weight to create.

---

[⬅ Back to GCP Platform Engineering](./README.md) · [All topics](../README.md)
