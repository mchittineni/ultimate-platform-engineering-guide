---
title: "What is the Gateway API and why is it replacing Ingress?"
id: 56
category: "Kubernetes Platform"
difficulty: "Beginner"
tags:
  - platform-engineering
  - kubernetes-platform
  - interview-questions
---

# What is the Gateway API and why is it replacing Ingress?

**Short answer:** The Gateway API is the Kubernetes project's successor to Ingress: a set of resources - `GatewayClass`, `Gateway`, and route types such as `HTTPRoute` and `GRPCRoute` - for describing how traffic gets into and around a cluster. It replaces Ingress because Ingress was too small to express real routing without vendor-specific annotations, and it had one resource for what are really three roles. The Gateway API splits infrastructure, the shared entry point, and per-team routes into separate resources owned by separate people, which maps almost exactly onto how a platform team and its tenants divide the work.

## Detail

**What was wrong with Ingress.** The Ingress resource can say "this host and path go to that Service" and configure TLS - and very little else. Header-based routing, traffic splitting, timeouts, retries, redirects, and rewrites were all left to each controller, which exposed them as annotations: free-form strings, different for every implementation, unvalidated, and non-portable. Moving from one controller to another meant rewriting every annotation. And because a single Ingress object mixed the listener, TLS, and routing, there was no clean way to let a team own its routes without also letting it touch the shared entry point.

**The role-oriented model.** The Gateway API separates concerns into resources that match who owns them:

| Resource       | Owned by                | Says                                                                                     |
| -------------- | ----------------------- | ---------------------------------------------------------------------------------------- |
| `GatewayClass` | Infrastructure provider | "Gateways of this class are implemented by this controller"                              |
| `Gateway`      | Platform team           | "Listen on these ports and hostnames, with this TLS, allow routes from these namespaces" |
| `HTTPRoute`    | Application team        | "Requests for my hostname and paths go to my Services"                                   |

A route attaches to a Gateway by reference (`parentRefs`), and the Gateway decides which namespaces may attach. That is the property a platform needs: tenants self-serve their routing in their own namespace, and the platform keeps control of the listeners, certificates, and load balancer. `ReferenceGrant` handles the remaining cross-namespace case, such as a route pointing at a Service in another namespace, which must be explicitly permitted by the target namespace.

**Expressive and typed.** Traffic splitting by weight, header and query-parameter matching, redirects, URL rewrites, request and response header modification, and timeouts are fields in the spec rather than annotations, validated by the API server. That also makes routes a natural substrate for canaries - progressive delivery tools such as Argo Rollouts and Flagger can shift weights on an `HTTPRoute` directly (see [progressive delivery](../progressive-delivery-and-feature-flags/what-is-progressive-delivery.md)).

**Beyond HTTP, and beyond the edge.** `GRPCRoute` and `TLSRoute` are in the Standard channel; `TCPRoute` and `UDPRoute` remain experimental. Since v1.5, `ListenerSet` is also standard, which lets tenants attach their own listeners and certificates to a shared Gateway. The same route resources are used for service-mesh (east-west) traffic through the GAMMA initiative, so one API can describe both ingress and in-mesh routing.

**Why "replacing" is now urgent.** The Ingress API is still GA and is not being removed, but it is frozen - no new features. What changed the timeline for many platforms is that the community `ingress-nginx` controller, the most widely deployed Ingress implementation, was retired, with best-effort maintenance ending in March 2026. Anyone still on it is running an unpatched edge component. The realistic choices are to migrate to a Gateway API implementation (Envoy Gateway, Cilium, Istio, Contour, NGINX Gateway Fabric, cloud-provider gateway controllers, and others) or to a different maintained Ingress controller as a stepping stone. `ingress2gateway` translates existing Ingress objects and common annotations into Gateway API resources, which removes most of the mechanical work.

**The trade-offs.** More resources to understand, and implementations differ in which extended features they support - check conformance reports rather than assuming. Some controller-specific behaviour still needs implementation-specific policy resources. And migration is a traffic change on your most critical path, so it should be done per hostname with a parallel Gateway, not as a cut-over.

**The user of the platform.** Developers should get a simple experience: they declare a hostname and paths, and the platform either lets them write an `HTTPRoute` attached to the shared Gateway or generates one from the service specification. They should never provision their own load balancer or manage certificates.

## Example

```yaml
# Owned by the platform team: one shared Gateway, TLS terminated here,
# routes accepted only from namespaces labelled as tenants.
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata: { name: public, namespace: platform-gateway }
spec:
  gatewayClassName: envoy-gateway
  listeners:
    - name: https
      protocol: HTTPS
      port: 443
      hostname: "*.apps.example.com"
      tls:
        mode: Terminate
        certificateRefs: [{ name: wildcard-apps-example-com }]
      allowedRoutes:
        namespaces:
          from: Selector
          selector: { matchLabels: { platform.example.com/tenant: "true" } }
---
# Owned by the application team, in their own namespace.
# A canary split that used to need controller-specific annotations.
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata: { name: checkout, namespace: team-payments }
spec:
  parentRefs:
    - { name: public, namespace: platform-gateway, sectionName: https }
  hostnames: ["checkout.apps.example.com"]
  rules:
    - matches: [{ path: { type: PathPrefix, value: /v1 } }]
      timeouts: { request: 5s }
      backendRefs:
        - { name: checkout-stable, port: 8080, weight: 90 }
        - { name: checkout-canary, port: 8080, weight: 10 }
```

```text
Migration off a retired Ingress controller, per hostname:

  1. Install a Gateway API implementation alongside the old controller.
  2. ingress2gateway print --providers=ingress-nginx  -> review generated routes
  3. For one hostname: apply the HTTPRoute, test via the new Gateway's address.
  4. Move DNS for that hostname; watch error rate and latency.
  5. Delete the old Ingress for that hostname. Repeat.
  6. Remove the old controller only when no Ingress objects remain.
```

## Interview tips

- Lead with the role split - GatewayClass for infrastructure, Gateway for the platform, routes for application teams. That is the design idea, and it is exactly the platform/tenant boundary.
- Explain the annotation problem concretely: unvalidated, vendor-specific, non-portable. It is why Ingress could not simply be extended.
- Be precise: Ingress is frozen, not removed. The urgency comes from the retirement of the community ingress-nginx controller, not from the API disappearing.
- Mention `allowedRoutes` and `ReferenceGrant` as the multi-tenancy controls, and GAMMA for mesh traffic - both show you know more than the headline.
- For migration, say per hostname with a parallel Gateway and `ingress2gateway` for the translation. A big-bang cut-over of the edge is the answer interviewers are testing you to avoid.

---

[⬅ Back to Kubernetes Platform](./README.md) · [All topics](../README.md)
