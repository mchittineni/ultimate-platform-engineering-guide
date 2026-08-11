---
title: "How do you run a secretless CI/CD pipeline?"
id: 67
category: "Platform Security"
difficulty: "Advanced"
tags:
  - platform-engineering
  - platform-security
  - interview-questions
---

# How do you run a secretless CI/CD pipeline?

**Short answer:** The pipeline authenticates with an OIDC token the CI system mints for that specific job, exchanged for short-lived credentials by whatever it needs to reach - the cloud, the registry, the artefact store. The trust policy pins the repository, the branch or tag, and the environment, so a token from one repository cannot be used to deploy another. Combined with a pull-based deployment agent, no long-lived credential exists in CI at all.

## Detail

**Why CI is the credential to worry about most.** A CI system with a stored cloud key is usually the highest-value target in an organisation: it has broad permissions, it runs code from pull requests, and its logs and environment are visible to many people. A single leaked key there is more damaging than most application vulnerabilities, and it is the standard route in real supply-chain incidents.

**The mechanism.** The CI provider acts as an OIDC identity provider. For each job it mints a token containing claims about the run - repository, ref, workflow, environment, actor. The cloud provider trusts that issuer and its trust policy asserts conditions on those claims before issuing temporary credentials. The credential lives for the job and expires; there is nothing to rotate and nothing to leak.

**The claim conditions are the security boundary, and being loose here defeats the whole design.** A trust policy conditioned only on the organisation lets any repository in that organisation assume the role, including a new one someone created. Pin the repository, and for anything privileged pin the ref or the environment as well, so a pull request branch cannot obtain production credentials.

| Claim          | Why you condition on it                                      |
| -------------- | ------------------------------------------------------------ |
| `repository`   | Only this repository, not anything in the organisation       |
| `ref`          | Only `refs/heads/main` or a tag - not a pull-request branch  |
| `environment`  | Ties the credential to a protected environment with approval |
| `aud`          | Prevents replay of the token at another system               |
| `workflow_ref` | Only a specific reviewed workflow can assume the role        |

**Environment protection rules are where the approval gate lives.** Bind the production role to a CI environment that requires reviewers and restricts which branches may deploy to it. The credential is then only obtainable after the approval, which is a much stronger control than a check inside a script.

**Pull-based deployment removes the largest permission entirely.** If an in-cluster agent reconciles from Git, CI never needs cluster credentials - its job ends at publishing a signed artefact and opening a change. That single architectural choice eliminates the credential people most often mishandle.

**Registry and package publishing federate too.** Container registries, package registries, and cloud artefact stores increasingly accept OIDC, and signing can be keyless using the CI identity - so even the signing key does not exist as a secret.

**What legitimately remains, and how to shrink it.** A third-party service with no OIDC support is the usual holdout. Contain it: scope the token as narrowly as the vendor allows, keep it in a secret store fetched at job time rather than as a CI variable, restrict it to a specific job, rotate it automatically, and record it on a list of remaining secrets with an owner. Then push the vendor - "does it support OIDC" is now a reasonable procurement question.

**Protect against untrusted code paths.** A workflow triggered by a pull request from a fork must never receive privileged credentials. Split workflows so the privileged parts run only from trusted refs, and treat any workflow that both runs untrusted code and holds credentials as a vulnerability.

## Example

```yaml
# No secrets. The id-token permission is what mints the OIDC token; every
# credential in this job is short-lived and job-scoped.
name: release
on:
  push:
    tags: ["v*"]

permissions:
  contents: read
  id-token: write # mint the OIDC token
  packages: write # registry via the same token
  attestations: write # keyless signing with the CI identity

jobs:
  build-and-publish:
    runs-on: ubuntu-latest
    # Binds this job to a protected environment: reviewers required, and only
    # tags may deploy to it. The credential is unobtainable before approval.
    environment: production
    steps:
      - uses: actions/checkout@v5

      # Cloud credentials by federation - no stored key
      - uses: aws-actions/configure-aws-credentials@v5
        with:
          role-to-assume: arn:aws:iam::<account-id>:role/ci-publish
          aws-region: eu-west-1

      - name: Build and push
        id: build
        run: |
          IMAGE="ghcr.io/example/checkout"
          docker build -t "$IMAGE:${GITHUB_REF_NAME}" .
          docker push "$IMAGE:${GITHUB_REF_NAME}"

      # Keyless signing - the signing identity IS the CI identity. No key exists.
      - run: cosign sign --yes "ghcr.io/example/checkout:${GITHUB_REF_NAME}"

      # CI's job ends here. It does NOT hold cluster credentials: it opens a
      # change and an in-cluster agent reconciles it.
      - run: ./scripts/open-deploy-pr.sh "${GITHUB_REF_NAME}"
```

```json
// The trust policy. Every condition below removes a real attack path.
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<account-id>:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          // Environment, not just repo - ties the credential to the approval gate
          "token.actions.githubusercontent.com:sub": "repo:example/checkout:environment:production"
        }
      }
    }
  ]
}
```

```text
The conditions that matter, from weakest to strongest:

  sub: "repo:example/*"                          <- ANY repo in the org. A new
                                                    repo someone creates today
                                                    can deploy production.
  sub: "repo:example/checkout:*"                 <- any ref, including a PR
                                                    branch. An attacker who can
                                                    open a PR can get the role.
  sub: "repo:example/checkout:ref:refs/heads/main"  <- better
  sub: "repo:example/checkout:environment:production" <- best: requires the
                                                    protected environment, so
                                                    approval has already happened

Remaining-secret register - the honest part of any secretless claim:

  SECRET                    WHY IT REMAINS          MITIGATION            OWNER
  legacy-vendor-api-token   no OIDC support         store-fetched at job  alice
                                                    time, rotated 30d,
                                                    scoped to one job
  smtp-relay-password       no OIDC support         same                  bob
  ----------------------------------------------------------------------------
  2 secrets, both third-party, both with owners and rotation. Both raised with
  the vendors. "Secretless" means this list is short, owned, and shrinking -
  not that it is empty.
```

## Interview tips

- Start with why CI is the credential that matters most: broad permissions, runs untrusted code, visible logs. That framing justifies the whole design.
- The claim conditions are the answer's core. Walk the ladder from `repo:org/*` to `environment:production` and say what each step removes.
- Binding the role to a protected CI environment, so the credential is unobtainable before approval, is a strong control most candidates do not mention.
- "Pull-based deployment means CI never holds cluster credentials" is the architectural point, and it eliminates the single most dangerous permission rather than protecting it.
- Keyless signing using the CI identity is a good detail - even the signing key stops being a secret.
- Be honest about the remaining secrets and show the register with owners and rotation. Claiming a fully secretless pipeline is less credible than showing a short, managed list.
- Mention that a fork pull request must never receive privileged credentials. It is the specific vulnerability class in this area.

---

[⬅ Back to Platform Security](./README.md) · [All topics](../README.md)
