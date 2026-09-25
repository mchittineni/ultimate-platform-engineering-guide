---
title: "How do you manage Terraform at platform scale?"
id: 76
category: "Control Planes and Abstractions"
difficulty: "Advanced"
tags:
  - platform-engineering
  - control-planes-and-abstractions
  - interview-questions
---

# How do you manage Terraform at platform scale?

**Short answer:** Split state so blast radius is small, version and publish modules as products with their own tests, run plan and apply only through automation with the plan reviewed on the pull request, and never let a human apply from a laptop. The failure that defines "at scale" is the monolithic state file: one workspace containing everything means every change plans slowly, locks everyone out, and risks destroying unrelated infrastructure.

## Detail

**State layout is the decision that matters most.** Split along blast radius and change frequency: account and organisation foundations change rarely and should be isolated; network foundations similarly; per-environment and per-service resources change often and should each have their own state. A useful rule is that a state file should contain resources you would be willing to `destroy` together. If the answer is "never all of these", split it. Every state needs a locking backend; on S3 that is now native (`use_lockfile = true`), so the separate DynamoDB lock table is no longer needed.

**Cross-state references should be loose.** Reading another state directly with a remote state data source couples them tightly - the consumer breaks when the producer's internals change. Prefer passing identifiers explicitly, or discovering them by tag or from a parameter store, so the contract between layers is a small set of named values rather than someone else's whole state.

**Modules are products with consumers.** Version them with tags, pin consumers to versions - never a branch - and treat a breaking change the way you would any platform interface change: a new major version, a migration path, and pull requests raised for consumers. Give each module tests, ideally ones that provision and destroy real resources in a sandbox account - the built-in `terraform test` (or `tofu test`) framework now covers this without extra tooling - plus static checks for security and cost. A module without tests silently breaks forty consumers.

**Automation, always, with the plan on the pull request.** The workflow is: change opened, plan runs automatically, the plan is posted as a comment for review, approval merges, apply runs from the main branch. This gives you the reviewable diff that is Terraform's main advantage over reconciling controllers, an audit trail, and no drift between what was reviewed and what was applied. Local applies are how state gets corrupted and how changes reach production unreviewed.

**Authenticate the runner with federated identity, not stored keys.** The CI job should exchange its workload identity token for short-lived cloud credentials. A long-lived cloud key in CI secrets is the highest-value credential in most organisations, because it usually has broad infrastructure permissions.

**Detect drift on a schedule, because Terraform will not tell you otherwise.** A nightly plan across all workspaces, reporting any non-empty diff, is how you find console changes before they collide with a real deployment. Without it, drift surfaces as a surprising destroy in an unrelated change - which is how teams learn to distrust the tool.

**Protect against the plans that destroy things.** Require explicit approval for any plan containing a destroy or replace of a stateful resource, use `prevent_destroy` lifecycle rules on databases and buckets, and make destructive plans visibly different in review rather than a line buried in 400 lines of output.

**Pick the binary deliberately.** Since the 2023 licence change, Terraform (BSL, owned by IBM since 2025) and OpenTofu (MPL, a CNCF project) share HCL and providers but are diverging on features. At platform scale, standardise on one, pin its version in CI images, and keep shared modules to the common subset if consumers may use either.

**Where Terraform should stop.** At platform scale, Terraform is usually best for foundations - accounts, networks, clusters, the things that must exist before anything else - while the high-frequency, per-team resource requests are better served by a reconciling control plane with a self-service interface. Keeping Terraform for the bootstrap layer and putting a claims-based API in front of the rest avoids building a pipeline-plus-portal wrapper to make Terraform self-service.

## Example

```text
State layout by blast radius and change frequency. Each cell is one state file.

  LAYER 0  organisation           changes: yearly     destroy together? yes
    accounts, SCPs, org policy, billing
    state: s3://tfstate/org/terraform.tfstate

  LAYER 1  per-account foundation changes: quarterly  destroy together? yes
    VPC, subnets, transit gateway, DNS zones, KMS keys
    state: s3://tfstate/foundation/<account>/<region>/terraform.tfstate

  LAYER 2  per-cluster            changes: monthly    destroy together? yes
    EKS cluster, node groups, IAM for the cluster, platform bootstrap
    state: s3://tfstate/clusters/<cluster>/terraform.tfstate

  LAYER 3  per-service resources  changes: weekly     destroy together? yes,
    databases, queues, buckets for ONE service                    for one service
    state: s3://tfstate/services/<env>/<service>/terraform.tfstate

  ...or better, for Layer 3: a reconciling control plane with claims, so teams
  self-serve without a Terraform pipeline per service. Terraform's advantage is
  the reviewable plan for foundations; it is not a self-service interface.

  Anti-pattern: one state file for all four layers. Every service change plans
  the whole organisation, holds a global lock, and can propose destroying a VPC.
```

````yaml
# The only place apply happens. Federated identity, plan on the PR, no local applies.
name: terraform
on:
  pull_request:
    paths: ["infra/**"]
  push:
    branches: [main]
    paths: ["infra/**"]

permissions:
  id-token: write # OIDC token for the cloud role - no stored keys
  contents: read
  pull-requests: write # to post the plan for review

jobs:
  plan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: aws-actions/configure-aws-credentials@v5
        with:
          role-to-assume: arn:aws:iam::<account-id>:role/terraform-plan # read-only
          aws-region: eu-west-1
      - run: terraform init && terraform plan -out=tfplan -no-color
      - run: |
          terraform show -json tfplan > plan.json
          terraform show -no-color tfplan > plan.txt
      # Fail the check on destructive changes so they cannot be merged casually;
      # a labelled override exists for the cases where a destroy is intended.
      - name: Block undeclared destroys
        run: |
          python3 scripts/check_plan.py plan.json \
            --deny-destroy-of aws_db_instance,aws_s3_bucket,aws_rds_cluster
      - name: Post the plan for review
        uses: actions/github-script@v8
        with:
          script: |
            const fs = require("fs");
            const plan = fs.readFileSync("plan.txt", "utf8").slice(0, 60000);
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: "```terraform\n" + plan + "\n```",
            });
````

```text
Nightly drift detection - the thing Terraform will never tell you unprompted:

  $ terraform-drift-report --all-workspaces

  WORKSPACE                          DRIFT   DETAIL
  foundation/prod/eu-west-1          clean
  clusters/prod-eu-1                 clean
  services/prod/checkout             2       aws_db_instance.main
                                             instance_class t4g.small -> t4g.medium
                                             (console change, 2026-08-09, alice)
                                             backup_retention 7 -> 1  <-- SERIOUS
  services/prod/search               clean

  The retention change is exactly the kind of drift that is invisible until a
  restore is needed. Found in a nightly plan; would otherwise have surfaced as
  a confusing diff in an unrelated pull request weeks later.
```

## Interview tips

- Lead with state layout and give the test - a state file should hold resources you would destroy together. It is concrete and immediately shows you have dealt with a monolithic workspace.
- "No local applies, plan posted on the pull request" is the operational rule; the reviewable plan is Terraform's main advantage and losing it to laptop applies wastes it.
- Federated identity for the runner rather than stored cloud keys is the security point interviewers listen for, because a CI key with infrastructure permissions is usually the crown jewel.
- Scheduled drift detection is what most candidates omit. Give an example of drift that matters - a backup retention change nobody would notice.
- The strongest close is knowing where Terraform should stop: foundations in Terraform, high-frequency team requests behind a reconciling self-service API rather than a pipeline wrapper.

---

[⬅ Back to Control Planes and Abstractions](./README.md) · [All topics](../README.md)
