# FN-001 · Rate limiting when many legitimate users share one IP

**Field note · public-safe abstraction from a real product constraint**

Rate limiting often starts with a convenient assumption:

> one IP address is a reasonable proxy for one user.

Sometimes that assumption is the bug.

## The real constraint

The product had to support situations where many legitimate people could use the same application at roughly the same time from the same shared network.

A strict IP-only limiter would therefore turn normal group usage into something that looked like an attack.

The requirement was not “remove rate limiting.” It was:

> preserve brute-force, spam and abuse protection **without making a shared public IP the primary identity for every action**.

## Threat model first, limiter key second

Different kinds of abuse target different things.

| Action class | What is actually being protected? | Better primary key |
| --- | --- | --- |
| Authentication attempt | a specific account/identity | account identifier |
| Authenticated action | one signed-in actor | user identity |
| Anonymous action on one resource | that resource from one network | network + resource |
| Broad volumetric abuse | the application edge | network safety net |

The design therefore stopped asking:

> “What rate limit should this endpoint have?”

and started asking:

> **“Which identity best represents the thing an attacker is trying to abuse?”**

## Decision

Use **layered, context-specific rate-limit keys** instead of a universal IP bucket.

```text
account-targeted auth
    → account identifier
    → generous network safety net

signed-in action
    → user identity

anonymous resource action
    → network + resource

broad abuse / bot safety net
    → network
```

The network-level limiter remains useful, but as a coarse backstop rather than the first and only line of defense.

## Why this works better

### It protects the victim of brute force

If an attacker repeatedly targets one account, limiting by the account identifier constrains the attack even if the requests arrive from different networks.

### It stops one noisy user from punishing everyone else

Authenticated users receive independent buckets. Many people behind the same NAT can therefore use the product normally.

### Anonymous actions can be scoped to the resource being abused

A person interacting with one resource should not necessarily exhaust the allowance for unrelated resources used by other people on the same network.

### The IP still matters

A generous IP safety net can still catch obviously abnormal traffic or distributed abuse concentrated behind one origin without becoming the everyday user-level limiter.

## The failure mode that triggered the redesign

The original configuration used strict per-IP limits for actions where a shared IP was entirely plausible.

That meant a small number of people could consume the allowance and cause unrelated legitimate users on the same network to be rejected.

The important engineering move was not tuning the number upward. It was recognizing that **the key itself was wrong**.

A larger wrong bucket is still the wrong model.

## Verification strategy

The private implementation was tested around the behavioral requirement:

- separate users behind one network should not share authenticated limits;
- repeated attempts against one account should still be constrained;
- anonymous activity can be isolated by resource;
- the network safety net still blocks clearly abnormal aggregate traffic;
- fallback behavior remains safe when a stronger identity is unavailable.

Exact thresholds, endpoint names, internal configuration and private source are intentionally omitted. They are implementation details, not the reusable idea.

## Provenance

**Gianluca Cioni explicitly rejected strict IP-only limiting** for flows where legitimate groups may share one public connection. The behavioral requirement was to preserve account-, user-, resource- and network-level abuse protection without letting a shared IP become the primary identity for every action.

Most implementation work was performed in an **AI-assisted coding workflow** under those requirements, followed by code inspection and automated verification. This note therefore demonstrates threat-model correction, system requirements and architecture judgment — **not a claim of manually typing every line of the limiter**.

## General rule

A useful rate-limit key should approximate the **abuse identity**, not merely the easiest metadata available on the request.

Before choosing a threshold, ask:

1. What exactly is being protected?
2. Who or what is the attacker targeting?
3. Which legitimate users share this identifier?
4. What happens when that identifier is unavailable?
5. Which broader safety net should still exist?

That sequence often matters more than the numerical limit itself.
