---
title: "What is Terraform state and why does it need protecting?"
id: 70
category: "Control Planes and Abstractions"
difficulty: "Beginner"
tags:
  - platform-engineering
  - control-planes-and-abstractions
  - interview-questions
---

# What is Terraform state and why does it need protecting?

**Short answer:** Terraform state is a JSON file that records which real-world resources Terraform manages and what their attributes were at the last apply - the mapping from `aws_db_instance.main` in your code to a specific database ID in your account. Terraform needs it to work out what to create, change, or destroy. It needs protecting for three reasons: it often contains secrets in plain text, losing or corrupting it makes Terraform forget what it owns, and two people writing it at once can corrupt it - so it belongs in a locked, encrypted, versioned remote backend with tightly restricted access.

## Detail

**Why state exists at all.** Your `.tf` files say what you want; the cloud says what exists. Terraform needs a third record linking the two, because cloud APIs do not know that a particular bucket "belongs" to `aws_s3_bucket.receipts`. State stores that link, plus each resource's attributes and the dependencies between resources. On every `plan`, Terraform reads the state, refreshes it against the real APIs, and compares the result with your code.

**What goes wrong without protection:**

- **Secrets in plain text.** Database passwords, generated keys, and connection strings end up in state as ordinary values. Marking a variable `sensitive` hides it from command output, not from the state file. Anyone who can read the state can read the secrets.
- **Loss or corruption.** If the state is deleted, Terraform believes nothing exists. The next `apply` tries to create everything again, colliding with the real resources, and recovering means importing each one by hand.
- **Concurrent writes.** Two applies running at once can each write their own version of state, and the last writer wins, losing the other's changes. This is exactly what locking prevents.
- **Tampering.** Someone who can edit state can make Terraform believe a resource is different from reality, causing it to destroy or replace things on the next apply.

**The standard protections:**

- **Remote backend, never local.** Store state in a backend such as an S3 bucket, Azure Blob Storage, Google Cloud Storage, or HCP Terraform - not on a laptop and never in Git.
- **Locking.** The backend must lock state during a write. The S3 backend now supports native locking with a lock file (`use_lockfile = true`), which replaces the older DynamoDB table approach.
- **Encryption.** Encrypt at rest with a managed key, and restrict who can use that key. OpenTofu can also encrypt state client-side before it reaches the backend.
- **Versioning.** Turn on bucket versioning so a bad write or accidental deletion can be rolled back to the previous version.
- **Least-privilege access.** Only the CI runner's role should write production state. Humans get read access at most, and ideally not even that for workspaces holding secrets.
- **Keep secrets out where possible.** Generate database passwords in a secrets manager and let the database read them, or use Terraform's ephemeral values and write-only arguments so the secret is never stored.

**Change state through commands, not editors.** When resources need renaming or moving between files, use `moved` blocks, `import` blocks, and `removed` blocks in code, or `terraform state mv` as a last resort. Editing the JSON by hand is how state gets corrupted.

**Split state to limit damage.** One huge state file for everything means one mistake or one leaked file affects everything. Separate state per environment and per layer - network, cluster, service - keeps the blast radius small and lets you give different teams different access.

**Who the user is.** Application teams rarely touch state directly; they open pull requests and the platform's pipeline runs Terraform for them. The platform team owns the backend, the locking, the access policy, and the recovery procedure. A good platform makes it impossible for anyone to apply from a laptop, which removes most of the ways state goes wrong.

## Example

```hcl
# backend.tf - remote, locked, encrypted state.
terraform {
  backend "s3" {
    bucket       = "example-tfstate-prod"
    key          = "services/checkout/terraform.tfstate"
    region       = "eu-west-1"
    encrypt      = true
    kms_key_id   = "arn:aws:kms:eu-west-1:111122223333:key/0a1b2c3d-4e5f-6789-abcd-ef0123456789"
    use_lockfile = true # native S3 locking; no DynamoDB table needed
  }
}
```

```text
Why the state file itself is sensitive - an excerpt:

  {
    "type": "aws_db_instance",
    "name": "main",
    "instances": [{
      "attributes": {
        "id": "checkout-prod",
        "endpoint": "checkout-prod.abc123.eu-west-1.rds.amazonaws.com:5432",
        "username": "app",
        "password": "Xk9!vQ2...",      <- plain text, despite sensitive = true
        ...

What locking prevents:

  alice$ terraform apply
  Acquiring state lock. This may take a few moments...

  ci$    terraform apply
  Error: Error acquiring the state lock
    Lock Info:
      Path:      example-tfstate-prod/services/checkout/terraform.tfstate
      Operation: OperationTypeApply
      Who:       alice@laptop
  ^ the second writer is refused instead of silently overwriting state
    (and the fix is to stop applying from laptops at all)
```

## Interview tips

- Define state by its job: the mapping between resources in code and real resource IDs, used to compute every plan.
- Lead with the secrets point. Many candidates do not know that `sensitive = true` does not keep a value out of state, and interviewers like hearing it.
- List the protections as a set - remote backend, locking, encryption, versioning, restricted access - and mention that S3 now locks natively with `use_lockfile`.
- Mention `moved`, `import`, and `removed` blocks as the safe way to change state, rather than editing JSON.
- A common follow-up is how to structure state at scale; the short answer is split by blast radius, covered in [managing Terraform at platform scale](./how-do-you-manage-terraform-at-platform-scale.md).

---

[⬅ Back to Control Planes and Abstractions](./README.md) · [All topics](../README.md)
