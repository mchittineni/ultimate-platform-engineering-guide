---
title: "How do you give teams self-service pipelines without maintaining 200 of them?"
id: 51
category: "GitOps and Continuous Delivery"
difficulty: "Advanced"
tags:
  - platform-engineering
  - gitops-and-continuous-delivery
  - interview-questions
---

# How do you give teams self-service pipelines without maintaining 200 of them?

**Short answer:** Ship one versioned, parameterised pipeline that every repository references rather than copies, so a change to it reaches every consumer when they update the reference - and pin the reference so nobody is broken without warning. The failure mode to avoid is the pipeline template: copied once into each repository, immediately divergent, and impossible to improve without two hundred pull requests.

## Detail

**Reference, do not copy.** Every major CI system supports composition: reusable workflows and composite actions in GitHub Actions, `include` in GitLab CI, shared libraries in Jenkins, orbs in CircleCI. The repository's pipeline file should be a handful of lines - which shared workflow, at which version, with which parameters. If a team's pipeline file is two hundred lines, you have shipped a template and you now maintain divergence rather than a pipeline.

**Versioning is what makes it safe.** Consumers pin to a tag. A change lands in a new version, is adopted by a canary set of repositories, then rolled out. Referencing a moving branch means your Tuesday change breaks fifty teams' builds simultaneously - which happens once and then nobody trusts the shared pipeline again. Version it exactly as you would any platform interface, with automated upgrade pull requests when a new version is released.

**Parameterise narrowly, and resist the pressure to widen.** Language, test command, target environments, whether it publishes an image. Every parameter you add is a combination you must support, and a shared pipeline with forty parameters has become a programming language with worse ergonomics. When a team needs something genuinely unusual, the honest options are a second shared pipeline for that workload shape, or a documented escape.

**Make the shared pipeline carry the non-negotiables.** Because every repository routes through it, it is a strong enforcement point for image signing, SBOM generation, vulnerability scanning, provenance attestation, and secretless authentication. Those steps should not be parameterisable off. This is why the reference model matters beyond maintenance: it is how supply-chain controls actually reach every service.

**Pipelines should get their credentials from federation, not secrets.** The shared pipeline requests an OIDC token and exchanges it for short-lived cloud credentials, scoped by the repository and environment it is running for. Teams therefore never handle a registry or cloud credential, and there is no long-lived secret in any repository - which is also what makes the shared pipeline safe to run on behalf of everyone.

**Test the pipeline like software.** It is code with two hundred consumers. It needs its own test suite - a set of fixture repositories exercising each language and each parameter combination - run before any version is tagged. Platform teams that ship pipeline changes untested break builds fleet-wide, and build outages are the most visible possible failure.

**Measure adoption and divergence.** Report which repositories are on which version, and which have local steps that duplicate or override shared ones. A long tail on an old version is a migration backlog; duplicated local steps are a signal that the shared pipeline is missing something, and that is product feedback rather than misbehaviour.

## Example

```yaml
# What a team's repository contains. Nine lines, pinned, no CI logic.
# .github/workflows/ci.yml
name: ci
on:
  push: { branches: [main] }
  pull_request:

permissions:
  contents: read
  id-token: write # OIDC for federated credentials - no stored secrets
  packages: write

jobs:
  build-and-deploy:
    uses: example/platform-pipelines/.github/workflows/service.yml@v4.2.1 # PINNED
    with:
      language: go
      service_name: checkout
      environments: "staging,production"
```

```yaml
# The shared pipeline. Non-negotiable supply-chain steps are not parameterisable.
# example/platform-pipelines/.github/workflows/service.yml
name: platform service pipeline
on:
  workflow_call:
    inputs:
      language: { required: true, type: string } # go | node | python | java
      service_name: { required: true, type: string }
      environments: { required: false, type: string, default: "staging" }
      # Deliberately NOT parameterisable: scanning, signing, SBOM, provenance.

jobs:
  build:
    runs-on: ubuntu-latest
    permissions: { contents: read, id-token: write, packages: write, attestations: write }
    steps:
      - uses: actions/checkout@v5
      - uses: ./.github/actions/setup-${{ inputs.language }} # per-language, shared
      - run: make test

      # --- mandatory, every service, no opt-out -------------------------------
      - name: Build with reproducible metadata
        id: build
        run: |
          IMAGE="ghcr.io/example/${{ inputs.service_name }}"
          docker build -t "$IMAGE:${{ github.sha }}" .
          DIGEST=$(docker push "$IMAGE:${{ github.sha }}" | awk '/digest:/ {print $3}')
          echo "digest=$DIGEST" >> "$GITHUB_OUTPUT"
      - name: SBOM
        run: syft "ghcr.io/example/${{ inputs.service_name }}@${{ steps.build.outputs.digest }}" \
          -o cyclonedx-json > sbom.json
      - name: Vulnerability scan (fails on critical)
        run: grype "ghcr.io/example/${{ inputs.service_name }}@${{ steps.build.outputs.digest }}" \
          --fail-on critical
      - name: Sign (keyless, CI identity)
        run: cosign sign --yes \
          "ghcr.io/example/${{ inputs.service_name }}@${{ steps.build.outputs.digest }}"
      - uses: actions/attest-build-provenance@v3
        with:
          subject-name: ghcr.io/example/${{ inputs.service_name }}
          subject-digest: ${{ steps.build.outputs.digest }}
      # -----------------------------------------------------------------------

      - name: Open the deployment change by digest
        run: ./scripts/bump-deploy-ref.sh \
          "${{ inputs.service_name }}" "${{ steps.build.outputs.digest }}"
```

```text
Fleet view - adoption and divergence, which is where the product feedback lives.

  $ platform pipelines report

  VERSION   REPOS   NOTE
  v4.2.1    168     current
  v4.1.0     34     one minor behind; auto-bump PRs open
  v3.8.2     14     BEHIND A MAJOR - migration backlog, 2 have failing bump PRs
  none        4     not using the shared pipeline at all  <-- investigate

  LOCAL STEP DIVERGENCE (repos adding steps that duplicate or override shared ones)
    custom integration-test step ........ 19 repos   <-- MISSING CAPABILITY.
                                                        19 teams solved the same
                                                        problem. Add it as a
                                                        parameter, do not close it.
    custom notification step .............  8 repos
    overriding the scan step .............  2 repos  <-- POLICY VIOLATION, not
                                                        feedback. Escalate.
```

## Interview tips

- "Reference, do not copy" is the thesis, with the test being how many lines a team's pipeline file has. Nine lines is right; two hundred means you shipped a template.
- Versioning with pinned consumers plus automated bump pull requests is what makes it safe. Say what happens without it: one change breaks fifty teams at once, and trust never recovers.
- Narrow parameterisation, with the warning that a pipeline with forty parameters has become a badly designed programming language.
- The supply-chain argument is the strongest reason for the reference model beyond maintenance: signing, SBOM, and scanning reach every service because every service routes through it, and those steps are not optional.
- Testing the pipeline with fixture repositories, and reporting adoption plus local divergence, are the two operational details that mark experience. Distinguishing divergence that is feedback from divergence that is a policy violation is the senior touch.

---

[⬅ Back to GitOps and Continuous Delivery](./README.md) · [All topics](../README.md)
