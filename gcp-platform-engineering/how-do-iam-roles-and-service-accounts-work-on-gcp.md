---
title: "How do IAM roles and service accounts work on GCP?"
id: 173
category: "GCP Platform Engineering"
difficulty: "Beginner"
tags:
  - platform-engineering
  - gcp-platform-engineering
  - interview-questions
---

# How do IAM roles and service accounts work on GCP?

**Short answer:** GCP IAM answers "who can do what on which resource" with an allow policy attached to a resource: each binding in it grants a role - a named bundle of permissions - to one or more principals. Policies inherit down the hierarchy from organisation to folder to project to resource. A service account is the identity a workload uses instead of a person, and it is unusual in being both a principal that holds roles and a resource that other principals need permission to use.

## Detail

**The three nouns.** A **principal** is who: a Google account, a Google group, a service account, a whole Workspace or Cloud Identity domain, or a federated identity from an external provider. A **permission** is one action, such as `storage.objects.get`. A **role** is a collection of permissions, and you never grant permissions directly - only roles.

**The three kinds of role.**

| Kind       | Examples                                            | Use                                                         |
| ---------- | --------------------------------------------------- | ----------------------------------------------------------- |
| Basic      | `roles/owner`, `roles/editor`, `roles/viewer`       | Almost never in production - far too broad                  |
| Predefined | `roles/storage.objectViewer`, `roles/run.developer` | The default choice; maintained by Google as services change |
| Custom     | `organizations/123/roles/platformDeployer`          | When no predefined role is narrow enough; you maintain it   |

`roles/editor` deserves a special warning: it grants write access to most services in a project, and it is the role Google historically gave the default Compute Engine service account. Seeing it on a workload identity is one of the most common findings in any GCP review.

**How a policy is evaluated.** An allow policy is a list of bindings, each saying "these principals have this role", attached to an organisation, folder, project, or individual resource such as a bucket. The effective access on a resource is the union of its own policy and every ancestor's - so a role granted on a folder applies to every project beneath it, and you cannot remove an inherited grant lower down. Two tools narrow this: **IAM Conditions** attach an expression to a binding (for example, only resources with a given name prefix, or only until a date), and **deny policies** explicitly block permissions regardless of what is allowed, which is how a platform protects things like "nobody but the security team may delete audit log sinks".

**Grant to groups, not people.** Binding roles to a group such as `team-payments@example.com` means joiners and leavers are handled in the identity provider, not by editing IAM across dozens of projects. Individual user bindings are how access quietly outlives employment.

**Service accounts are workload identities.** A workload - a Cloud Run service, a GKE Pod, a VM, a CI job - runs as a service account, and the service account's roles decide what that workload may do. Best practice is one service account per workload, granted only the roles it needs on only the resources it touches, which keeps the blast radius of a compromise knowable.

**Why a service account is also a resource.** Other principals need permission to use it. `roles/iam.serviceAccountUser` lets someone attach the account to a resource they deploy - so a developer who can deploy Cloud Run and holds this role on a powerful account can run code with that account's authority. `roles/iam.serviceAccountTokenCreator` lets someone mint tokens for it directly, which is impersonation. Both are privilege-escalation paths and should be granted on specific service accounts, never across a whole project.

**Three kinds of service account you will meet.** User-managed accounts you create for workloads. Default service accounts that some services create automatically - over-privileged historically, and on organisations created since May 2024 no longer given Editor automatically. And service agents, which Google manages so that a service can act in your project on your behalf; you rarely touch them, but deleting their bindings breaks the service.

**Keys are the anti-pattern.** A service account can have a downloadable JSON key, which is a long-lived secret with no expiry. Workloads on GCP should get short-lived tokens from the metadata server, and workloads elsewhere should use Workload Identity Federation - see [How does Workload Identity Federation remove service account keys?](./how-does-workload-identity-federation-remove-service-account-keys.md).

**Who uses this, and what the platform gives them.** Application developers rarely want to write IAM. A good platform creates the per-workload service account during vending, grants a small set of well-known roles from a declared list of dependencies ("reads this bucket, publishes to this topic"), and uses IAM recommender findings to trim unused permissions over time. Humans who need elevated access get it just in time through Privileged Access Manager rather than holding standing admin roles.

**The trade-off.** Least privilege costs effort: narrow roles mean more bindings, more "permission denied" moments during development, and more custom roles to maintain. Platforms usually accept slightly broader predefined roles scoped to one project in non-production, and insist on resource-level grants in production where the risk justifies the work.

## Example

```bash
# One service account per workload.
gcloud iam service-accounts create sa-checkout \
  --project=checkout-prod \
  --display-name="checkout service"

# Grant a narrow predefined role on ONE resource - this bucket - rather than the project.
gcloud storage buckets add-iam-policy-binding gs://checkout-prod-receipts \
  --member="serviceAccount:sa-checkout@checkout-prod.iam.gserviceaccount.com" \
  --role="roles/storage.objectCreator"

# Let the CI deployer attach THIS service account to Cloud Run, and no other.
gcloud iam service-accounts add-iam-policy-binding \
  sa-checkout@checkout-prod.iam.gserviceaccount.com \
  --member="serviceAccount:sa-deployer@ci-prod.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Deploy the workload running AS that identity.
gcloud run deploy checkout --project=checkout-prod --region=europe-west1 \
  --image=europe-docker.pkg.dev/artifacts-prod/containers/checkout:1.14.2 \
  --service-account=sa-checkout@checkout-prod.iam.gserviceaccount.com
```

```yaml
# The project's allow policy as `gcloud projects get-iam-policy` returns it.
bindings:
  - role: roles/viewer
    members:
      - group:team-payments@example.com # a group, not individuals
  - role: roles/run.developer
    members:
      - serviceAccount:sa-deployer@ci-prod.iam.gserviceaccount.com
  - role: roles/cloudsql.admin
    members:
      - user:priya@example.com
    # A rare individual grant, acceptable only because it expires. Privileged
    # Access Manager does this properly, with approval and audit.
    condition:
      title: incident-4821-temporary
      expression: request.time < timestamp("2027-01-31T00:00:00Z")
```

## Interview tips

- Define the three nouns - principal, permission, role - and say that you only ever grant roles. Then explain inheritance down the hierarchy and that inherited grants cannot be removed lower down.
- Call out basic roles, especially `roles/editor`, as too broad for production, and mention the default Compute Engine service account as the classic place it appears.
- The standout point is that a service account is both a principal and a resource. `roles/iam.serviceAccountUser` and `roles/iam.serviceAccountTokenCreator` are privilege-escalation paths; interviewers often probe this.
- Mention deny policies and IAM Conditions as the tools for exceptions - they show you know IAM is more than allow bindings.
- Say "groups, not people" and "one service account per workload" as the two operating rules a platform enforces.
- Close on keys being the anti-pattern and federation being the replacement. For comparison with AWS, see [What is the difference between an IAM user and an IAM role?](../aws-platform-engineering/what-is-the-difference-between-an-iam-user-and-an-iam-role.md).

---

[⬅ Back to GCP Platform Engineering](./README.md) · [All topics](../README.md)
