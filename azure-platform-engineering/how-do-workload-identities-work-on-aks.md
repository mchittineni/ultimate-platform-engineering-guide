---
title: "How do workload identities work on AKS?"
id: 89
category: "Azure Platform Engineering"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - azure-platform-engineering
  - interview-questions
---

# How do workload identities work on AKS?

**Short answer:** The cluster exposes an OIDC issuer, a Kubernetes service account is annotated with a client ID, and a federated identity credential on a managed identity or app registration trusts that specific issuer, subject, and audience. The Pod receives a projected token and exchanges it for an Entra ID token - no secret is stored. This replaced the older pod-managed identity approach, which intercepted the instance metadata endpoint and is deprecated.

## Detail

**The pieces, and all four must line up.** The AKS cluster must have the OIDC issuer and workload identity features enabled. A managed identity or app registration must have a federated identity credential naming the cluster's issuer URL, the subject in the form `system:serviceaccount:<namespace>:<name>`, and the audience `api://AzureADTokenExchange`. The service account carries the `azure.workload.identity/client-id` annotation. And the Pod must be labelled `azure.workload.identity/use: "true"` so the mutating webhook injects the token volume and environment variables.

**That label is the most common reason it silently does not work.** Everything else can be configured correctly and the Pod will still fall back to whatever other credential it can find, because without the label nothing is injected. It is the first thing to check when a workload gets an authentication error that looks like a permissions problem.

**The federated credential's subject is the security boundary.** It names one namespace and one service account. Because Azure's federated identity credentials require an exact subject rather than allowing wildcards, this design is somewhat harder to misconfigure into a cluster-wide trust than a hand-written cloud trust policy elsewhere - but you should still confirm that each identity maps to one workload rather than being shared across a namespace.

**Prefer user-assigned managed identities for workloads.** They exist independently of any resource, so the same identity survives cluster replacement and can be created and role-assigned by your provisioning path before the workload exists. System-assigned identities are tied to a resource lifecycle, which makes them awkward for workloads that outlive a cluster.

**Role assignments are where least privilege lives.** The identity itself grants nothing; Azure RBAC role assignments scoped to a resource group, a specific resource, or with a condition are what determine reach. Scope to the narrowest resource that works, and prefer a resource-scoped assignment over a subscription-scoped one - a `Contributor` assignment at subscription scope is the Azure equivalent of a wildcard policy.

**Know what this replaces.** AAD Pod Identity worked by intercepting requests to the instance metadata endpoint, which required a privileged component and had race conditions at Pod startup. It is deprecated in favour of workload identity, and being able to say why - no metadata interception, no privileged daemon, standard OIDC federation - is a useful signal that you are current.

**Extend the same identity to other Azure services.** Key Vault access via the CSI driver using the workload identity, Azure SQL and PostgreSQL with Entra authentication instead of passwords, and Service Bus and Storage with RBAC rather than connection strings. The goal is that the workload's identity, not a stored secret, is what grants everything.

**The platform should generate all of it.** The managed identity, the federated credential, the role assignments, the service account, and the Pod label from the service declaration. Hand-assembling four coupled pieces across forty teams guarantees some are wrong, and the failure mode is a confusing authentication error rather than an obvious one.

## Example

```bash
# The four pieces. All must line up or the workload silently uses another credential.

# 1. Cluster: OIDC issuer + workload identity enabled
az aks update --resource-group rg-platform --name aks-prod-eu \
  --enable-oidc-issuer --enable-workload-identity

ISSUER=$(az aks show -g rg-platform -n aks-prod-eu \
  --query oidcIssuerProfile.issuerUrl -o tsv)

# 2. A user-assigned managed identity - survives cluster replacement
az identity create -g rg-team-payments -n id-checkout
CLIENT_ID=$(az identity show -g rg-team-payments -n id-checkout --query clientId -o tsv)

# 3. The federated credential. Subject names ONE namespace and ONE service
#    account - this is the security boundary.
az identity federated-credential create \
  --identity-name id-checkout \
  --resource-group rg-team-payments \
  --name checkout-federated \
  --issuer "$ISSUER" \
  --subject "system:serviceaccount:team-payments:checkout" \
  --audience "api://AzureADTokenExchange"

# 4. Role assignment scoped to the narrowest resource that works -
#    NOT Contributor at subscription scope.
az role assignment create \
  --assignee-object-id "$(az identity show -g rg-team-payments -n id-checkout --query principalId -o tsv)" \
  --assignee-principal-type ServicePrincipal \
  --role "Storage Blob Data Reader" \
  --scope "/subscriptions/<sub-id>/resourceGroups/rg-team-payments/providers/Microsoft.Storage/storageAccounts/stcheckoutreceipts"
```

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: checkout
  namespace: team-payments
  annotations:
    azure.workload.identity/client-id: "<client-id>"
---
apiVersion: apps/v1
kind: Deployment
metadata: { name: checkout, namespace: team-payments }
spec:
  template:
    metadata:
      labels:
        app: checkout
        # THE LABEL. Without it, the webhook injects nothing and the SDK falls
        # back to some other credential - producing an authentication error that
        # looks like a permissions problem. First thing to check.
        azure.workload.identity/use: "true"
    spec:
      serviceAccountName: checkout
      containers:
        - name: checkout
          image: ghcr.io/example/checkout@sha256:9f2c8b1d...
          # No connection strings, no client secret. The SDK finds
          # AZURE_CLIENT_ID, AZURE_TENANT_ID, and AZURE_FEDERATED_TOKEN_FILE,
          # all injected by the webhook.
```

```text
Diagnosing the usual failures, in the order they occur:

  symptom: "DefaultAzureCredential failed to retrieve a token"
    1. Is the pod labelled azure.workload.identity/use: "true"?   <-- 60% of cases
    2. Is AZURE_FEDERATED_TOKEN_FILE present in the container env?
         kubectl exec ... -- env | grep AZURE
       absent -> the webhook did not act; the label is missing or the mutating
       webhook is not running.
    3. Does the federated credential's subject exactly match
       system:serviceaccount:<ns>:<sa>?   A typo here fails closed, correctly.
    4. Does the issuer in the federated credential match the CURRENT cluster's
       issuer URL?  <-- breaks after a cluster is replaced. Reason to keep the
       identity user-assigned and re-point the credential rather than recreate.
    5. Only then look at role assignments - a token issued but no permission
       gives a different, clearer error.

  Audit points:
    ✗ any role assignment of Contributor/Owner at subscription scope
    ✗ one managed identity shared across several workloads
    ✗ any remaining client secret or connection string in a namespace secret
```

## Interview tips

- Name all four pieces - cluster OIDC issuer, federated identity credential, service account annotation, Pod label - and stress that all must line up.
- The Pod label being the most common silent failure is the detail that reads as hands-on. Interviewers who have debugged this will recognise it immediately.
- Prefer user-assigned managed identities because they survive cluster replacement. Tie that to the cluster-replacement model rather than in-place upgrades.
- Least privilege lives in the role assignment, not the identity, and a subscription-scoped `Contributor` is the Azure equivalent of a wildcard policy.
- Knowing that AAD Pod Identity is deprecated, and why - metadata interception, a privileged daemon, startup race conditions - signals you are current.
- Extending the same identity to Key Vault, Entra database authentication, and Service Bus RBAC shows you think of it as an identity strategy rather than one integration.
- The platform generating all four coupled pieces is the closing point: hand-assembly across many teams guarantees confusing failures.

---

[⬅ Back to Azure Platform Engineering](./README.md) · [All topics](../README.md)
