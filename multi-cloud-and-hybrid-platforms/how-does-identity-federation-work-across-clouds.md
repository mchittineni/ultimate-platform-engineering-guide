---
title: "How does identity federation work across clouds?"
id: 188
category: "Multi-Cloud and Hybrid Platforms"
difficulty: "Beginner"
tags:
  - platform-engineering
  - multi-cloud-and-hybrid-platforms
  - interview-questions
---

# How does identity federation work across clouds?

**Short answer:** Federation means one system vouches for an identity and another system trusts that vouching instead of holding its own password or key. For people, a single identity provider signs a SAML or OIDC assertion that each cloud accepts and maps to a role. For workloads, the platform where the code runs issues a short-lived signed token (usually an OIDC JWT), and the other cloud's security token service validates it against the issuer's public keys and exchanges it for its own short-lived credentials. The result is no long-lived keys copied between clouds and one place to revoke access.

## Detail

**The core mechanism is signed tokens plus trust configuration.** An identity provider (IdP) signs a statement - "this is `alice@example.com`, member of group platform-admins" or "this is service account payments/api in cluster prod-eu" - with a private key and publishes the matching public keys at a well-known URL. The receiving cloud is configured to trust that issuer, checks the signature, checks the claims (issuer, subject, audience, expiry), and hands back its own temporary credentials scoped to a role. Nothing secret crosses between clouds except a token that expires in minutes to an hour.

**Human federation: one IdP, many clouds.** An organisation picks one IdP - Microsoft Entra ID, Okta, Google, or similar - and federates each cloud to it:

- **AWS**: IAM Identity Center connected to the external IdP via SAML for sign-in and SCIM for provisioning users and groups; groups map to permission sets across accounts.
- **Azure**: Entra ID is itself the IdP; if another IdP is primary, Entra can federate to it or receive users via provisioning.
- **Google Cloud**: Cloud Identity synchronised from the IdP, or Workforce Identity Federation, which lets users from an external IdP access Google Cloud without creating Google accounts.

The payoff is one joiner-mover-leaver process. When someone leaves, disabling them in the IdP ends their access to every cloud - which is the control auditors care about most.

**Workload federation: short-lived tokens, not stored keys.** Code running in one cloud often needs to call another - a job on EKS writing to Azure Blob Storage, a GitHub Actions pipeline deploying to Google Cloud. Each cloud supports accepting an external OIDC token:

- **AWS**: `AssumeRoleWithWebIdentity` against an IAM OIDC identity provider, with the role's trust policy restricting the subject and audience. For on-premises machines with certificates, IAM Roles Anywhere exchanges an X.509 certificate for temporary credentials.
- **Azure**: a federated identity credential on a user-assigned managed identity or app registration, trusting a specific issuer and subject.
- **Google Cloud**: Workload Identity Federation with a workload identity pool and provider; it accepts OIDC tokens, SAML, and AWS credentials directly.

Every Kubernetes cluster has a service account token issuer, and managed clusters publish it as a public OIDC discovery URL - that is what makes cross-cloud workload federation practical.

**The subject claim is the security boundary.** Trusting an issuer is not enough; the trust must be pinned to a specific subject, such as `system:serviceaccount:payments:api`. A trust configuration that accepts any subject from a shared issuer lets any workload in that cluster - or any repository on a CI provider - assume the role. This is the most common federation misconfiguration.

**The trade-off.** Federation moves risk from key leakage to trust configuration. There are no keys to rotate or leak, but a single IdP outage now blocks sign-in everywhere, so you keep a small, audited set of break-glass accounts per cloud. And federation does not unify authorisation: each cloud still has its own IAM model, so "platform-admins" still needs a mapping to an AWS permission set, an Azure RBAC role, and a Google Cloud IAM role.

**Name the user.** Engineers benefit from single sign-on with one set of groups; application teams benefit because the platform wires workload federation into the service template, so a team asks for "read access to bucket X in the other cloud" and never handles a credential. Security teams benefit from one revocation point.

## Example

A pod on EKS writes to Azure Blob Storage with no stored secret. Azure trusts the EKS cluster's OIDC issuer for exactly one service account.

```bash
# Azure side: trust one service account in one EKS cluster.
az identity federated-credential create \
  --name eks-prod-eu-report-exporter \
  --identity-name id-report-exporter \
  --resource-group rg-reporting-prod \
  --issuer "https://oidc.eks.eu-west-1.amazonaws.com/id/EXAMPLED539D4633E53DE1B71EXAMPLE" \
  --subject "system:serviceaccount:reporting:report-exporter" \
  --audiences "api://AzureADTokenExchange"
```

```yaml
# Kubernetes side: project a token with the audience Azure expects.
apiVersion: v1
kind: Pod
metadata:
  name: report-exporter
  namespace: reporting
spec:
  serviceAccountName: report-exporter
  containers:
    - name: exporter
      image: registry.example.com/report-exporter@sha256:7d0f3a...
      env:
        # Read by the Azure SDK's WorkloadIdentityCredential
        - { name: AZURE_CLIENT_ID, value: "00000000-0000-0000-0000-000000000001" }
        - { name: AZURE_TENANT_ID, value: "00000000-0000-0000-0000-00000000000a" }
        - { name: AZURE_FEDERATED_TOKEN_FILE, value: /var/run/secrets/azure/token }
      volumeMounts:
        - { name: azure-token, mountPath: /var/run/secrets/azure, readOnly: true }
  volumes:
    - name: azure-token
      projected:
        sources:
          - serviceAccountToken:
              path: token
              audience: api://AzureADTokenExchange
              expirationSeconds: 3600
```

```text
What happens at runtime:

  1. kubelet writes a JWT signed by the EKS cluster issuer
       iss: https://oidc.eks.eu-west-1.amazonaws.com/id/EXAMPLED...
       sub: system:serviceaccount:reporting:report-exporter
       aud: api://AzureADTokenExchange      exp: +1h
  2. the Azure SDK sends it to Entra ID's token endpoint
  3. Entra ID fetches the issuer's public keys, verifies signature, iss, sub, aud
  4. Entra ID returns an access token for the managed identity
  5. the pod calls Blob Storage with that token; RBAC on the storage account decides
  No secret was stored anywhere. Deleting the federated credential revokes access.
```

## Interview tips

- Explain the mechanism in one line: an issuer signs a short-lived token, the other side verifies it against published public keys and exchanges it for its own temporary credentials.
- Separate human federation (one IdP, SAML or OIDC, SCIM provisioning) from workload federation (OIDC token exchange per cloud), and name each cloud's mechanism.
- Stress pinning the subject claim - trusting a whole issuer is the classic mistake.
- Say what federation does not solve: authorisation still differs per cloud, and a single IdP needs break-glass accounts.
- Related depth: [How does a platform provide workload identity without long-lived credentials?](../platform-security/how-does-a-platform-provide-workload-identity-without-long-lived-credentials.md) and [How does Workload Identity Federation remove service account keys?](../gcp-platform-engineering/how-does-workload-identity-federation-remove-service-account-keys.md).

---

[⬅ Back to Multi-Cloud and Hybrid Platforms](./README.md) · [All topics](../README.md)
