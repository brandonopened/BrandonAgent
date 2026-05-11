# FERPA

A compliance-reviewer agent. Given an implementation plan, design doc, or
technical proposal, FERPA evaluates it against the Family Educational Rights
and Privacy Act (20 U.S.C. § 1232g; 34 CFR Part 99) and returns a structured
findings report.

FERPA does not write product plans — it only reviews them. It is designed to
be invoked directly, or as a sub-agent inside `ComplianceTeam`.

## Layout

- `main.py` — AgentCore entrypoint; defines the Strands `Agent` and the FERPA
  evaluation system prompt.
- `model/load.py` — Bedrock model loader (Claude Sonnet 4.5).

## Local dev

```
agentcore dev
agentcore invoke --dev "Review this plan for FERPA compliance: <paste plan>"
```

## Deployment

Registered as a runtime in `../../agentcore/agentcore.json`. Deploy with
`agentcore deploy`.

## Reference

- https://studentprivacy.ed.gov/ferpa
- 34 CFR Part 99
