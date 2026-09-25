---
title: "What is container image signing?"
id: 121
category: "Platform Security"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-security
  - interview-questions
---

# What is container image signing?

**Short answer:** Image signing attaches a cryptographic signature to a container image's digest, so anyone running it can verify who produced it and that it has not changed since. On modern platforms this is usually keyless: the CI job signs with its own short-lived OIDC identity through Sigstore, the signature is recorded in a public transparency log, and the cluster's admission policy refuses to run images that are not signed by the expected pipeline. Signing only protects anything when something verifies it.

## Detail

**What problem it solves.** A container registry is just storage. Anyone with push access can upload an image, and a tag like `checkout:v1.4` can be repointed to different content at any time. Without signing, a cluster has no way to tell an image your CI built from one an attacker, or a developer's laptop, pushed. A signature is a verifiable statement: "this identity vouches for exactly this content".

**Why it signs the digest, not the tag.** An image digest (`sha256:...`) is a hash of the image's content, so it changes if a single byte changes. Tags are mutable pointers. Signing the digest means the signature is bound to the exact bytes; if the content is altered, the digest changes and the signature no longer matches. This is also why production workloads should reference images by digest.

**The mechanism, keyless style (Sigstore):**

1. The CI job requests an OIDC token from its CI provider, which says "I am the release workflow of repository `example/checkout`, running on `main`".
2. Sigstore's certificate authority (Fulcio) checks that token and issues a signing certificate valid for about ten minutes, with that identity written into it.
3. `cosign` signs the image digest with an ephemeral key, and the signature and certificate are recorded in Sigstore's transparency log (Rekor), a tamper-evident public record.
4. The signature is stored in the registry next to the image. The ephemeral private key is thrown away.

Verification later checks three things: the signature matches the digest, the certificate was valid when the signature was logged, and the identity in the certificate is the one you expect. There is no long-lived private key to steal, rotate, or leak - the trust anchor is the CI identity.

**Key-based signing still exists.** You can sign with a key pair held in a KMS or HSM, and air-gapped environments often must. The trade-off is that the key becomes a critical secret with its own rotation and access control. The Notary Project (`notation`) is the other widely used signing standard, common in some cloud registries; the concepts are the same.

**Verification is where the value is.** A signature nobody checks is decoration. The platform adds an admission policy - Kyverno, Sigstore's policy-controller, or a similar engine - that rejects any Pod whose images are not signed by the expected identity and issuer. That is what turns "our CI signs images" into "only images from our CI can run".

**Signatures and attestations.** A signature says who vouches for the image. An attestation is a signed statement _about_ the image: its SBOM, its build provenance (which commit, which workflow built it), or a scan result. They use the same machinery and are the next step once basic signing works.

**Who uses it.** Application teams usually never touch it: the platform's build template signs every image and the cluster verifies every Pod. What teams notice is the rare rejection, so the error message must say exactly which check failed and how to fix it.

**Trade-offs.** Verification adds a dependency to the deploy path; if the verifier or registry is slow, admission slows too. Third-party images are rarely signed by an identity you trust, so you need an allowlist-by-digest process for them. And a signature only proves origin, not safety: a signed image built from vulnerable code is still vulnerable.

## Example

```bash
# In CI, after pushing. Always sign by digest, never by tag.
# The job needs permission to mint an OIDC token (id-token: write in GitHub Actions).
IMAGE="ghcr.io/example/checkout@sha256:4b1f0c...e9"
cosign sign --yes "$IMAGE"

# Anyone can verify - and must say WHICH identity they expect, not just "signed".
cosign verify "$IMAGE" \
  --certificate-identity "https://github.com/example/checkout/.github/workflows/release.yml@refs/heads/main" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com"
```

```yaml
# The cluster side: no Pod in tenant namespaces runs unless its image was signed
# by the release workflow of a repository in our organisation.
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-signed-images
spec:
  webhookTimeoutSeconds: 10
  rules:
    - name: signed-by-our-ci
      match:
        any:
          - resources:
              kinds: [Pod]
              namespaces: ["team-*"]
      verifyImages:
        - imageReferences: ["ghcr.io/example/*"]
          failureAction: Audit # measure first; switch to Enforce later
          attestors:
            - entries:
                - keyless:
                    subject: "https://github.com/example/*/.github/workflows/release.yml@refs/heads/main"
                    issuer: "https://token.actions.githubusercontent.com"
```

```text
What a developer sees when an image built on a laptop is deployed:

  admission webhook "mutate.kyverno.svc-fail" denied the request:
  policy require-signed-images/signed-by-our-ci:
    ghcr.io/example/checkout@sha256:77ac...: no signature matching
    subject https://github.com/example/*/.github/workflows/release.yml@refs/heads/main

  -> Build through the release pipeline. Images pushed by hand cannot run.
```

## Interview tips

- Lead with the problem - registries accept anything and tags are mutable - then explain that signing binds an identity to a digest.
- Describe keyless signing precisely: short-lived certificate from the CI's OIDC identity, transparency log, no stored private key. That is the current default and interviewers expect it.
- Say that verification at admission is where the value is realised. "Signing without verifying is paperwork" is a line worth using.
- When verifying, always pin the identity and issuer. `cosign verify` with a wildcard identity only proves someone, somewhere, signed it.
- Name the user: teams get signing for free in the build template; the platform owns verification and clear rejection messages.
- Expect follow-ups on provenance and third-party images - see [securing the supply chain](./how-do-you-secure-the-software-supply-chain-for-everything-the-platform-builds.md) and [admission control](../kubernetes-platform/what-is-admission-control-and-how-do-you-use-it-as-a-platform-lever.md).

---

[⬅ Back to Platform Security](./README.md) · [All topics](../README.md)
