---
title: "How do you secure the software supply chain for everything the platform builds?"
id: 69
category: "Platform Security"
difficulty: "Advanced"
tags:
  - platform-engineering
  - platform-security
  - interview-questions
---

# How do you secure the software supply chain for everything the platform builds?

**Short answer:** Establish an unbroken chain of custody from source to running container - build only on trusted infrastructure, generate provenance describing how the artefact was produced, sign it, produce an SBOM, and then verify the signature and the provenance at admission so nothing unsigned or unattested can run. The verification step is what makes the rest meaningful; signing without verifying is paperwork.

## Detail

**What you are defending against.** Not only a malicious dependency. The realistic threats are a compromised build system injecting code, a mutable tag repointed to a different image, an image built on a developer's laptop reaching production, a typosquatted package, and a dependency that was fine at build time and has a critical vulnerability today. Each has a different control, and a good answer maps them.

**The chain, and what each link contributes:**

| Stage        | Control                                             | What it prevents                              |
| ------------ | --------------------------------------------------- | --------------------------------------------- |
| Source       | Protected branches, required review, signed commits | Unreviewed code entering the build            |
| Dependencies | Pinned lockfiles, an internal proxy, allowlisting   | Typosquatting, dependency confusion           |
| Build        | Hosted, ephemeral, no external network              | Build-time injection, non-reproducible builds |
| Provenance   | Signed attestation of how it was built              | An artefact built somewhere untrusted         |
| SBOM         | Component inventory, attached and signed            | Not knowing where a vulnerability is          |
| Publish      | Immutable digests, no mutable tags in production    | A tag being repointed                         |
| Admit        | **Verify signature and provenance at admission**    | Anything unverified running                   |
| Run          | Continuous rescanning of what is deployed           | A dependency that became vulnerable later     |

**Provenance is the link people skip.** A signature says someone signed this. Provenance says which source commit, which builder, which workflow, and which parameters produced it - so you can require that production images come from your CI, from your repository, on a protected ref. That is a much stronger statement than "signed by someone with access to the key".

**Keyless signing removes the key problem.** Signing with the CI workload's OIDC identity, recorded in a transparency log, means there is no signing key to steal or rotate, and verification asserts the identity and the issuer rather than a key you must distribute.

**Admission verification is where the value is realised.** An admission policy that rejects images without a valid signature and provenance from the expected identity is what converts your build controls into a guarantee. Without it, all the signing is advisory and an image built anywhere can still run.

**The SBOM is only useful if it is queryable.** Generating one per build and attaching it to the image is the easy part. The value comes from an index you can query - "which running services contain this library at this version" - answered in minutes rather than days. That is the capability you will want the day a critical vulnerability is published.

**Scan continuously, not only at build.** An image clean at build time becomes vulnerable when a new advisory lands. Rescanning the SBOMs of everything currently deployed, and alerting the owning team, is what closes the window between disclosure and detection.

**Roll it out in audit mode.** Turning on strict admission verification without first measuring what would fail is a self-inflicted outage - base images, third-party charts, and vendor images are the usual casualties. Audit, publish the list, fix or exempt with expiry, then enforce.

## Example

```yaml
# Build: provenance and SBOM produced and attached, signed with the CI identity.
# No signing key exists.
- name: Build and publish with attestations
  run: |
    IMAGE=ghcr.io/example/checkout
    docker build -t "$IMAGE:$GITHUB_SHA" .
    DIGEST=$(docker push "$IMAGE:$GITHUB_SHA" | awk '/digest:/ {print $3}')
    echo "digest=$DIGEST" >> "$GITHUB_OUTPUT"

- name: SBOM, attached to the image and signed
  run: |
    syft "ghcr.io/example/checkout@${DIGEST}" -o cyclonedx-json > sbom.json
    cosign attest --yes --predicate sbom.json \
      --type cyclonedx "ghcr.io/example/checkout@${DIGEST}"

- name: Keyless signature - identity is the CI workload, recorded in a log
  run: cosign sign --yes "ghcr.io/example/checkout@${DIGEST}"

- uses: actions/attest-build-provenance@v3 # SLSA provenance
  with:
    subject-name: ghcr.io/example/checkout
    subject-digest: ${{ steps.build.outputs.digest }}
```

```yaml
# Admission verification - the link that makes everything above meaningful.
# Note it asserts the IDENTITY and the ISSUER, not a key.
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata: { name: verify-image-provenance }
spec:
  validationFailureAction: Enforce # Audit first, for weeks, before this
  webhookTimeoutSeconds: 10
  rules:
    - name: signed-by-our-ci
      match:
        any: [{ resources: { kinds: [Pod], namespaces: ["team-*"] } }]
      verifyImages:
        - imageReferences: ["ghcr.io/example/*"]
          attestors:
            - entries:
                - keyless:
                    subject: "https://github.com/example/*/.github/workflows/*@refs/heads/main"
                    issuer: "https://token.actions.githubusercontent.com"
          # Provenance: built from our repo, on main, by our CI - not merely signed
          attestations:
            - predicateType: https://slsa.dev/provenance/v1
              attestors:
                - entries:
                    - keyless:
                        issuer: "https://token.actions.githubusercontent.com"
                        subject: "https://github.com/example/*"
              conditions:
                - all:
                    - key: "{{ buildDefinition.externalParameters.workflow.ref }}"
                      operator: Equals
                      value: "refs/heads/main"
    - name: no-mutable-tags
      match:
        any: [{ resources: { kinds: [Pod], namespaces: ["team-*"] } }]
      validate:
        message: "production images must be referenced by digest"
        pattern:
          spec:
            containers:
              - image: "*@sha256:*"
```

```text
The capability this buys, on the day it matters:

  $ platform sbom query --package "log4j-core" --version "<2.17.1"

  RUNNING SERVICES CONTAINING A MATCH ............ 7
    team-data/etl-runner        2.14.1   via  spark-core 3.3.0     tier 2
    team-data/warehouse-sync    2.14.1   via  spark-core 3.3.0     tier 2
    team-search/indexer         2.16.0   via  direct dependency    tier 1  <-- first
    ... 4 more

  images built but NOT running ................... 23  (registry cleanup)
  services with no SBOM attached .................  2  <-- BLIND SPOT. Both are
                                                          vendor images admitted
                                                          under an exemption.

  Answered in seconds because the SBOMs are indexed. Without the index this is
  a multi-day exercise across 40 teams, and the two blind spots would not be
  known at all.

Rollout that avoids an outage:
  wk 1-3  Audit mode. 218 workloads: 194 pass, 24 fail.
            18 x third-party images (ingress, cert-manager, vendor agents)
             4 x built before signing existed -> rebuilt
             2 x built locally by a developer  <-- exactly what this prevents
  wk 4    Allowlist the 18 third-party images by digest, each with an owner
          and a review date. Rebuild the 4. Block the 2.
  wk 5    Enforce.
```

## Interview tips

- Present it as a chain of custody and map each threat to its control. Reciting tool names without the threat model is the weak version of this answer.
- "Signing without verifying at admission is paperwork" is the sentence that matters most - the admission policy is where the value is realised.
- Distinguish signature from provenance clearly: a signature says someone signed it, provenance says which commit, which builder, which ref produced it. Requiring provenance is the stronger control.
- Keyless signing with the CI identity, recorded in a transparency log, removes the signing key as an asset to protect.
- The SBOM index is the capability that pays off during an incident. Give the query and the answer time - seconds versus days across forty teams.
- Continuous rescanning of deployed images, not just build-time scanning, addresses the vulnerability disclosed after the build.
- Always include the audit-then-enforce rollout with the third-party image casualties. It is what shows you have actually turned this on somewhere.

---

[⬅ Back to Platform Security](./README.md) · [All topics](../README.md)
