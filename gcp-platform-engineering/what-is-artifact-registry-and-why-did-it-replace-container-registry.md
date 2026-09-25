---
title: "What is Artifact Registry and why did it replace Container Registry?"
id: 175
category: "GCP Platform Engineering"
difficulty: "Beginner"
tags:
  - platform-engineering
  - gcp-platform-engineering
  - interview-questions
---

# What is Artifact Registry and why did it replace Container Registry?

**Short answer:** Artifact Registry is GCP's managed store for build outputs - container images, Helm charts, and language and OS packages such as Maven, npm, Python, Go, apt, and yum - organised into repositories that each have a format, a location, and their own IAM policy. It replaced Container Registry because Container Registry only stored images, kept them in Cloud Storage buckets whose permissions were coarse and awkward, and had no regional control, remote caching, or cleanup policies. Container Registry was shut down for writes on 18 March 2025, and `gcr.io` addresses now resolve to Artifact Registry.

## Detail

**The mechanism: repositories, not buckets.** In Artifact Registry you create a **repository** with a format (for example `docker`), a location (a region such as `europe-west1` or a multi-region such as `europe`), and a mode. Images are then addressed as `LOCATION-docker.pkg.dev/PROJECT/REPOSITORY/IMAGE:TAG`. Access is granted on the repository itself - `roles/artifactregistry.reader` to pull, `roles/artifactregistry.writer` to push - so a CI pipeline can push to one repository without touching any other.

**What was wrong with Container Registry.** Container Registry stored each registry host (`gcr.io`, `eu.gcr.io`, and so on) in a Cloud Storage bucket inside your project. Permissions were bucket permissions, so "can push to this one image path" was impossible to express, and anyone with broad storage access in the project could reach every image. It supported only container images, offered a handful of multi-regional hosts rather than real regional placement, and had no built-in way to expire old images. Artifact Registry fixes each of these.

**Three repository modes that matter to a platform.**

| Mode     | What it does                                                      | Why a platform wants it                                                   |
| -------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------- |
| Standard | Stores artifacts you push                                         | Your own images and packages                                              |
| Remote   | Caches an upstream such as Docker Hub, Maven Central, or PyPI     | Faster, rate-limit-proof pulls and one controlled route to public sources |
| Virtual  | Presents several repositories behind one address, with priorities | One URL for developers, with internal packages taking precedence          |

The virtual-plus-remote combination is the important one for supply-chain safety: developers point their tools at one virtual repository, internal packages win over public ones with the same name, and public packages arrive only through a cache you control. That mitigates dependency-confusion attacks.

**Features that make it a platform component rather than a disk.**

- **Vulnerability scanning** through Artifact Analysis, covering OS packages and language packages in images.
- **Cleanup policies** that delete or keep versions by age, tag state, or count, so storage does not grow forever.
- **Immutable tags** on Docker repositories, so `1.4.2` cannot be silently repointed at different content.
- **Regional placement** for latency and data residency, and **image streaming** for faster Pod start on GKE.
- **Audit logs** on every push and pull, which matter when an incident asks "who deployed this image?"

**What happened to `gcr.io`.** To avoid breaking every manifest that referenced `gcr.io/project/image`, Artifact Registry offers **gcr.io repositories**: Docker repositories that serve the old hostnames. Migration tooling creates them and redirects traffic, so old references keep working while new work uses `pkg.dev` addresses. After the March 2025 shutdown, pushes to legacy Container Registry fail, so any pipeline still writing there broke unless it had been moved.

**Who uses this, and what the platform gives them.** Every developer and every CI pipeline uses the registry, usually without thinking about it. The platform typically runs a small number of shared repositories in a dedicated artifacts project: per-team or per-domain Docker repositories with writer access for that team's CI identity only, a remote repository caching public sources, and a virtual repository per language. Runtimes then pull by digest from those repositories only, often enforced with Binary Authorization or an admission policy. What developers save is configuration and rate-limit incidents; what the organisation gains is one place where every deployed artifact came from.

**The trade-off.** Centralising artifacts creates a dependency every deployment shares - a misconfigured IAM change or a location choice made in haste affects everyone - and cross-region pulls from a far-away repository add latency and egress charges. Most platforms answer with one repository location per major region and treat repository IAM as platform-owned configuration, changed through review.

## Example

```bash
# A regional Docker repository with immutable tags, owned by the platform.
gcloud artifacts repositories create containers \
  --project=artifacts-prod --location=europe-west1 \
  --repository-format=docker --immutable-tags \
  --description="Production images, pushed only by CI"

# A remote repository that caches Docker Hub - the ONLY route to public images.
gcloud artifacts repositories create dockerhub-cache \
  --project=artifacts-prod --location=europe-west1 \
  --repository-format=docker --mode=remote-repository \
  --remote-docker-repo=DOCKER-HUB

# The payments CI identity may push to THIS repository; nothing else.
gcloud artifacts repositories add-iam-policy-binding containers \
  --project=artifacts-prod --location=europe-west1 \
  --member="serviceAccount:sa-ci-payments@ci-prod.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

# Let Docker authenticate to the regional host, then push.
gcloud auth configure-docker europe-west1-docker.pkg.dev
docker push europe-west1-docker.pkg.dev/artifacts-prod/containers/checkout:1.15.0
```

```json
[
  {
    "name": "delete-untagged-after-14-days",
    "action": { "type": "Delete" },
    "condition": { "tagState": "untagged", "olderThan": "14d" }
  },
  {
    "name": "always-keep-latest-20",
    "action": { "type": "Keep" },
    "mostRecentVersions": { "keepCount": 20 }
  }
]
```

```bash
# Try the cleanup policy in dry-run first, then enforce it.
gcloud artifacts repositories set-cleanup-policies containers \
  --project=artifacts-prod --location=europe-west1 \
  --policy=cleanup.json --dry-run
```

## Interview tips

- Lead with the mechanism: repositories with a format, a location, a mode, and their own IAM. Repository-level IAM is the single biggest improvement over Container Registry's bucket permissions.
- Know the shutdown fact: Container Registry stopped accepting writes on 18 March 2025, and `gcr.io` repositories in Artifact Registry keep old image references working.
- Explain remote and virtual repositories and connect them to supply-chain security - one controlled route to public sources, and protection against dependency confusion.
- Mention cleanup policies and immutable tags as the features that stop a registry becoming an unbounded, untrustworthy pile.
- Name the user: every CI pipeline and every runtime. The platform owns the repositories and their IAM so teams only push and pull.
- A likely follow-up is signing and provenance - be ready to connect the registry to image signing, attestations, and admission checks that only allow images from it.

---

[⬅ Back to GCP Platform Engineering](./README.md) · [All topics](../README.md)
