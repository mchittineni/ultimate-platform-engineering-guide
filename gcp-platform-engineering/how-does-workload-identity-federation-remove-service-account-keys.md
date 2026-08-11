---
title: "How does Workload Identity Federation remove service account keys?"
id: 94
category: "GCP Platform Engineering"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - gcp-platform-engineering
  - interview-questions
---

# How does Workload Identity Federation remove service account keys?

**Short answer:** An external identity provider's signed token is exchanged for a short-lived Google credential, so no key file ever exists. Inside GKE this is Workload Identity, where a Kubernetes service account is bound to a Google service account; outside GKE it is Workload Identity Federation with a workload identity pool trusting an external issuer such as your CI provider. The organisation policy `iam.disableServiceAccountKeyCreation` is what turns this from a recommendation into a guarantee.

## Detail

**Why service account keys are the problem worth solving.** A downloaded JSON key is a long-lived credential with no expiry that grants everything the service account can do. It ends up in repositories, CI variables, laptops, and shared drives, and it is the single most common route to a serious GCP compromise. Federation replaces it with a token that expires in an hour and cannot be copied off the workload in a useful form.

**Inside GKE: Workload Identity.** Enable it on the cluster, annotate the Kubernetes service account with the Google service account's email, and grant the Kubernetes service account the `roles/iam.workloadIdentityUser` role on the Google service account, with the member expressed as the cluster's workload identity pool plus the exact namespace and service account name. The client library then obtains tokens through the metadata server automatically. GKE Autopilot has Workload Identity enabled by default, which is one of its quiet advantages.

**The binding names one namespace and one service account.** That principal string is the security boundary, and it should map one Kubernetes service account to one Google service account - not a namespace-wide or cluster-wide binding. Sharing a Google service account across workloads collapses your authorisation model and makes an incident's blast radius unknowable.

**Outside GKE: Workload Identity Federation.** Create a workload identity pool, add a provider for the external issuer - your CI's OIDC issuer, another cloud's identity provider, or an on-premises OIDC service - map claims to attributes, and grant access either by impersonating a service account or, better, directly to the federated principal. The attribute condition on the provider is what stops any repository in your organisation obtaining credentials, and leaving it loose is the standard misconfiguration.

**Prefer direct resource access over service account impersonation** where it is supported. Granting IAM roles to the federated principal itself removes the intermediate service account entirely, which means there is no service account that could later have a key created for it.

**Then remove the ability to create keys at all.** With federation in place, enforce `iam.disableServiceAccountKeyCreation` at the organisation or folder level. Existing keys must be found and deleted separately - the constraint prevents new ones. This is the step that converts good practice into a property of the environment.

**Extend it beyond API access.** Cloud SQL and AlloyDB support IAM database authentication, so database access uses the same identity rather than a password. Service-to-service calls can use identity tokens. The goal is that the workload's identity, not a stored secret, grants everything.

**Audit for what remains.** Existing keys and their age, service accounts shared across workloads, loose attribute conditions on federation providers, and any use of the default compute service account - which is over-privileged by default and is a common quiet finding.

## Example

```bash
# GKE Workload Identity - the binding names ONE namespace and ONE service account.
gcloud iam service-accounts add-iam-policy-binding \
  sa-checkout@checkout-prod.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:checkout-prod.svc.id.goog[team-payments/checkout]"
#                                                     ^ namespace  ^ KSA name
#           the security boundary - not namespace-wide, not cluster-wide
```

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: checkout
  namespace: team-payments
  annotations:
    iam.gke.io/gcp-service-account: sa-checkout@checkout-prod.iam.gserviceaccount.com
---
apiVersion: apps/v1
kind: Deployment
metadata: { name: checkout, namespace: team-payments }
spec:
  template:
    spec:
      serviceAccountName: checkout
      containers:
        - name: checkout
          image: europe-docker.pkg.dev/artifacts/example/checkout@sha256:9f2c8b1d...
          # No GOOGLE_APPLICATION_CREDENTIALS, no key file. The library obtains
          # short-lived tokens via the metadata server.
```

```bash
# Outside GKE - federating a CI provider. The attribute CONDITION is the boundary.
gcloud iam workload-identity-pools create ci-pool \
  --location global --display-name "CI"

gcloud iam workload-identity-pools providers create-oidc github \
  --location global --workload-identity-pool ci-pool \
  --issuer-uri "https://token.actions.githubusercontent.com" \
  --attribute-mapping "google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref" \
  # WITHOUT this condition, ANY repository in the org can obtain credentials.
  # Leaving it off is the standard misconfiguration.
  --attribute-condition "assertion.repository_owner == 'example' && assertion.repository == 'example/checkout' && assertion.ref == 'refs/heads/main'"

# Better than impersonating a service account: grant the federated principal
# directly, so no service account exists that could later be given a key.
gcloud storage buckets add-iam-policy-binding gs://example-checkout-artifacts \
  --role roles/storage.objectAdmin \
  --member "principalSet://iam.googleapis.com/projects/<num>/locations/global/workloadIdentityPools/ci-pool/attribute.repository/example/checkout"
```

```text
The step that makes it a guarantee rather than a practice:

  $ gcloud resource-manager org-policies set-policy \
      --folder <workloads-folder-id> disable-sa-keys.yaml

    constraint: constraints/iam.disableServiceAccountKeyCreation
    booleanPolicy: { enforced: true }

  New keys become impossible to create. Existing keys are NOT removed by this -
  find and delete them separately:

  $ platform gcp audit service-account-keys

    KEYS STILL PRESENT ......................................... 6
      sa-legacy-uploader@...    age 803d   last used 214d ago   -> DELETE
      sa-ci-deploy@...          age 412d   last used 2h ago     -> migrate to
                                                                   federation first
      4 more
    SHARED SERVICE ACCOUNTS .................................... 2
      sa-team-search@... used by 4 workloads  -> split, one per workload
    LOOSE FEDERATION CONDITIONS ................................ 1
      pool ci-pool provider github: condition checks repository_owner only
      -> ANY repo in the org can obtain credentials. Narrow to the repository
         and ref.
    DEFAULT COMPUTE SERVICE ACCOUNT IN USE ..................... 3 projects
      over-privileged by default; replace with a purpose-made account
```

## Interview tips

- Start with why keys are the problem: no expiry, full authority, and they end up in repositories and CI variables. That framing motivates everything else.
- Distinguish GKE Workload Identity from Workload Identity Federation clearly - same idea, different entry point - and note that Autopilot enables it by default.
- The principal string naming one namespace and one Kubernetes service account is the security boundary; say that sharing a Google service account across workloads collapses the authorisation model.
- The attribute condition on a federation provider is the specific misconfiguration to call out - without it, any repository in the organisation can obtain credentials.
- Granting the federated principal directly rather than impersonating a service account is the stronger design, because no service account exists that could later be given a key.
- `iam.disableServiceAccountKeyCreation` is the closing move that turns practice into a guarantee - and be precise that it prevents new keys rather than removing existing ones.
- The default compute service account being over-privileged and still in use is a realistic audit finding worth mentioning.

---

[⬅ Back to GCP Platform Engineering](./README.md) · [All topics](../README.md)
