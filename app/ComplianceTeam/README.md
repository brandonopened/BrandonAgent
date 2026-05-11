# ComplianceTeam

Multi-agent orchestrator that runs an education-standards implementation plan
through a FERPA compliance review.

The team exposes two sub-agents as Strands tools:

- **`standards_partner`** — mirrors the `StandardsPartner` agent. Drafts /
  refines implementation plans, grounded in CASE 1.1, HROpen, and TCP data
  via the Educore MCP server (`https://educore.tqtmp.org/mcp`).
- **`ferpa_review`** — mirrors the `FERPA` agent. Evaluates a plan against
  20 U.S.C. § 1232g and 34 CFR Part 99, returning a structured findings
  report.

The orchestrator decides when to call which tool, can iterate (revise plan,
re-review), and delivers a combined response with three sections:
**Implementation Plan**, **FERPA Compliance Review**, **Team Summary**.

## Why "agent as tool"

Each sub-agent runs in-process as a Strands `Agent` wrapped in a `@tool`
function. This keeps the team a single deployable AgentCore runtime — no
inter-runtime calls — while letting the orchestrator decide when and how
often to invoke each role.

## Layout

- `main.py` — orchestrator agent + sub-agent definitions + `@tool` wrappers.
- `model/load.py` — Bedrock model loader (Claude Sonnet 4.5).
- `mcp_client/client.py` — Educore MCP client used by `standards_partner`.

## Local dev

```
agentcore dev
agentcore invoke --dev "We're building a system that ingests high-school transcripts and emits TCP records to colleges. Run it through the team."
```

## Deployment

Registered as a runtime in `../../agentcore/agentcore.json`. Deploy with
`agentcore deploy`.

## Reference

- StandardsPartner: `../StandardsPartner/`
- FERPA agent: `../FERPA/`
- FERPA reference: https://studentprivacy.ed.gov/ferpa
