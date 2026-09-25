---
title: "How do you use Azure Policy as a platform guardrail?"
id: 164
category: "Azure Platform Engineering"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - azure-platform-engineering
  - interview-questions
---

# How do you use Azure Policy as a platform guardrail?

**Short answer:** Assign policy at the management group so it inherits everywhere, use the effects deliberately - `Deny` for what must never exist, `DeployIfNotExists` and `Modify` to fix things automatically rather than blocking, and `Audit` while you measure - and roll out with `enforcementMode: DoNotEnforce` first. Azure Policy's distinguishing strength is that it can remediate rather than only reject, which makes it a guardrail rather than a gate.

## Detail

**Where it sits, and why that matters.** Azure Policy evaluates at resource creation and modification through Azure Resource Manager, and also continuously evaluates existing resources for compliance. That second property is genuinely useful and is missing from admission-control-style enforcement: it covers everything that predates the policy, not only new changes.

**The effects, and choosing between them is the real skill:**

| Effect              | Behaviour                                                  | Use for                                   |
| ------------------- | ---------------------------------------------------------- | ----------------------------------------- |
| `Deny`              | Rejects the request                                        | States that must never exist              |
| `Audit`             | Records non-compliance, allows it                          | Measuring before enforcing                |
| `Modify`            | Adds or changes properties, including tags                 | Applying a convention without blocking    |
| `DeployIfNotExists` | Deploys a missing related resource                         | Diagnostic settings, backup configuration |
| `AuditIfNotExists`  | Flags a missing related resource                           | Measuring the above before deploying      |
| `DenyAction`        | Blocks a specific action (delete)                          | Protecting critical resources from delete |
| Remediation task    | Applies `Modify`/`DeployIfNotExists` to existing resources | Backfilling after a policy lands          |

**`DeployIfNotExists` is the effect that makes Azure Policy distinctive.** Rather than rejecting a resource without diagnostic settings, it deploys the diagnostic settings. Telemetry, backup configuration, and endpoint protection become properties of existing rather than things a team must remember - which is exactly the guardrail-over-gate principle. It requires a managed identity with permission to deploy, which is worth mentioning because forgetting it is the usual reason a policy appears to do nothing.

**`Modify` is how you enforce a tagging convention without friction.** Inheriting a cost centre tag from the resource group, or adding an owner tag, applies the convention automatically instead of failing a deployment over a missing label. Since cost attribution depends entirely on tags being present, this is high-value.

**Initiatives group policies into something manageable.** Assigning eighty individual policies is unmaintainable; grouping them into an initiative with parameters, assigned once per management group, is. Regulatory compliance initiatives also map directly to framework controls, which makes them useful evidence for a compliance programme.

**Roll out with `enforcementMode: DoNotEnforce` first.** It evaluates and reports without acting, so you learn how many resources would fail before anything breaks. Then remediate what you can with remediation tasks, exempt the rest with expiry, and switch to enforcing. Turning on a `Deny` across a management group without this step is a reliable way to break other teams' deployments.

**Exemptions are first-class here, and that is a strength.** Azure Policy has a native exemption object with a scope, a category of waiver or mitigation, and an expiry date. Use it rather than narrowing the policy - narrowing weakens the control for everyone, whereas an exemption is visible, bounded, and expires.

**The non-compliance message is part of the policy.** A denial that says only "disallowed by policy" generates a support ticket. One that names the requirement and the supported alternative resolves itself. This is the cheapest possible improvement to how policy is received.

**Know the limitations.** Evaluation of existing resources is periodic rather than instant, so compliance state lags. Policy operates on the Resource Manager representation, so it cannot see inside a workload - what happens within an AKS cluster needs Kubernetes-side admission control, and the Azure Policy add-on for AKS exists to bridge that gap by translating policy into in-cluster enforcement through Gatekeeper. AKS deployment safeguards build on the same add-on to apply a curated set of Kubernetes best-practice policies, and they are switched on in enforce mode by default in AKS Automatic.

## Example

```json
// DeployIfNotExists - the distinctive effect. Rather than rejecting a resource
// with no diagnostic settings, it deploys them.
{
  "properties": {
    "displayName": "Deploy diagnostic settings for Azure SQL to the central workspace",
    "mode": "Indexed",
    "parameters": {
      "logAnalytics": { "type": "String", "metadata": { "strongType": "omsWorkspace" } }
    },
    "policyRule": {
      "if": { "field": "type", "equals": "Microsoft.Sql/servers/databases" },
      "then": {
        "effect": "DeployIfNotExists",
        "details": {
          "type": "Microsoft.Insights/diagnosticSettings",
          "existenceCondition": {
            "allOf": [
              { "field": "Microsoft.Insights/diagnosticSettings/logs.enabled", "equals": "true" },
              { "field": "Microsoft.Insights/diagnosticSettings/workspaceId", "equals": "[parameters('logAnalytics')]" }
            ]
          },
          // The managed identity needs these roles, or the policy silently
          // does nothing - the most common reason it appears not to work.
          "roleDefinitionIds": [
            "/providers/Microsoft.Authorization/roleDefinitions/749f88d5-cbae-40b8-bcfc-e573ddc772fa",
            "/providers/Microsoft.Authorization/roleDefinitions/92aaf0da-9dab-42b6-94a3-d43ce8d16293"
          ],
          "deployment": { "properties": { "mode": "incremental", "template": {} } }
        }
      }
    }
  }
}
```

```json
// Modify - enforce the tagging convention by applying it, not by failing the
// deployment. Cost attribution depends entirely on these tags existing.
{
  "properties": {
    "displayName": "Inherit cost-centre tag from the resource group",
    "mode": "Indexed",
    "policyRule": {
      "if": {
        "allOf": [
          { "field": "tags['cost-centre']", "exists": "false" },
          { "value": "[resourceGroup().tags['cost-centre']]", "notEquals": "" }
        ]
      },
      "then": {
        "effect": "Modify",
        "details": {
          "roleDefinitionIds": ["/providers/Microsoft.Authorization/roleDefinitions/b24988ac-6180-42a0-ab88-20f7382dd24c"],
          "operations": [
            { "operation": "add", "field": "tags['cost-centre']", "value": "[resourceGroup().tags['cost-centre']]" }
          ]
        }
      }
    }
  }
}
```

```text
Rollout, and the exemption that keeps the control intact:

  WEEK 1  assign at MG: Landing Zones/Corp with enforcementMode: DoNotEnforce
          -> compliance report: 2,140 resources, 318 non-compliant
             276 missing diagnostic settings  -> DeployIfNotExists will fix these
              31 missing cost-centre tag      -> Modify will fix these
              11 have public IPs              -> genuine Deny candidates

  WEEK 2  run remediation tasks for the DeployIfNotExists and Modify policies
          -> 318 non-compliant becomes 11. The platform fixed 307 of them.

  WEEK 3  for the 11: 9 fixed by teams via the Application Gateway path;
          2 need a native exemption, not a weakened policy:
```

```json
// Exemption: scoped, categorised, and time-bound. Better than narrowing the
// policy, which would weaken the control for everyone.
{
  "properties": {
    "policyAssignmentId": "/providers/Microsoft.Management/managementGroups/corp/providers/Microsoft.Authorization/policyAssignments/deny-public-ip-corp",
    "exemptionCategory": "Mitigated",
    "displayName": "legacy-ftp-gateway: vendor requires a public endpoint",
    "expiresOn": "2027-03-31T00:00:00Z",
    "metadata": {
      "compensatingControl": "NSG restricts source to two vendor CIDRs; DDoS Standard enabled; reviewed monthly",
      "owner": "carol@example.com",
      "approvedBy": "security-lead@example.com"
    }
  }
}
```

## Interview tips

- Lead with assignment at the management group for inheritance, and with the effects. Choosing the right effect is the actual skill this question tests.
- `DeployIfNotExists` is the answer that distinguishes Azure Policy from admission control - it remediates rather than rejects, which is the guardrail-over-gate principle in a product feature.
- Mention the managed identity and role definition requirement. Forgetting it is the standard reason a policy silently does nothing, and knowing that reads as hands-on experience.
- `Modify` for tag inheritance is high value because cost attribution depends on tags, and it applies the convention without failing anyone's deployment.
- `enforcementMode: DoNotEnforce` for rollout, with numbers, then remediation tasks, then enforce. Give the ratio the platform fixed versus assigned.
- Native exemptions with expiry and a compensating control, rather than narrowing the policy, is the governance answer.
- Know the limitation that Azure Policy cannot see inside an AKS cluster, and that the add-on bridges to in-cluster admission control. It is a precise, current detail.

---

[⬅ Back to Azure Platform Engineering](./README.md) · [All topics](../README.md)
