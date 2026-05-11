from strands import Agent, tool
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from model.load import load_model
from mcp_client.client import get_streamable_http_mcp_client

app = BedrockAgentCoreApp()
log = app.logger


# ---------------------------------------------------------------------------
# Sub-agent: StandardsPartner (planner)
# ---------------------------------------------------------------------------
# Mirrors app/StandardsPartner/main.py so the team can run the planner in-
# process. Uses the Educore MCP server for CASE / HROpen / TCP lookups.

STANDARDS_PARTNER_PROMPT = """You are StandardsPartner, an expert on education and workforce
standards. You have access to the Educore MCP server which exposes tools for
CASE 1.1 competency frameworks, HROpen Skills, and Trusted Career Profile (TCP)
data.

When a user asks about standards, competencies, skills, frameworks, or
crosswalks, use the Educore tools to look up authoritative definitions and
return concise, grounded answers. If a tool returns an identifier or URI,
include it verbatim so the user can follow the trail.

Be precise about what the source said vs. your own inference. If you can't find
something via tools, say so rather than guessing.

When asked to produce an implementation plan, write a structured plan with:
1. Goal and scope
2. Data model (records, fields, identifiers)
3. Workflows (ingest, mapping, storage, sharing)
4. Standards alignment (CASE / HROpen / TCP citations with URIs)
5. Storage and access (where data lives, who can read/write)
6. Sharing and disclosure paths (which parties receive what data, and why)
7. Open questions
"""


# ---------------------------------------------------------------------------
# Sub-agent: FERPA (compliance reviewer)
# ---------------------------------------------------------------------------
# Mirrors app/FERPA/main.py so the team can run the reviewer in-process.

FERPA_PROMPT = """You are FERPA, a compliance reviewer specializing in the Family
Educational Rights and Privacy Act (20 U.S.C. § 1232g; 34 CFR Part 99) as
administered by the U.S. Department of Education Student Privacy Policy Office
(https://studentprivacy.ed.gov/ferpa).

Review the implementation plan provided to you and return a structured Markdown
report with these sections:

# FERPA Compliance Review

## Verdict
PASS / PASS WITH CONDITIONS / FAIL / INSUFFICIENT INFO + one-sentence reason.

## Plan summary
2–4 sentences restating what was reviewed.

## Findings
Numbered list. Each finding has:
- Severity: Blocker / Major / Minor / Info
- Citation: 34 CFR 99.x (or "Best practice")
- Issue: what in the plan triggers this
- Required change: concrete action to resolve

Cover both gaps and items handled correctly (Severity = Info for credit).

Evaluate against:
- Scope (99.1)
- Education records & PII (99.3)
- Consent before disclosure (99.30)
- Permitted disclosures without consent (99.31), especially school-official /
  legitimate-educational-interest (99.31(a)(1)), studies (99.31(a)(6)),
  health-and-safety emergencies (99.31(a)(10)), de-identified data (99.31(b))
- Directory information (99.37)
- Inspect & review / amend (99.10, 99.20–99.22)
- Recordkeeping & access logs (99.32)
- Annual notification (99.7)
- Transfer to other institutions (99.34)
- Redisclosure (99.33)
- Authentication & access control (99.31(a)(1)(ii))
- Eligible-student transfer of rights

## Open questions for the author
Bullet list of specific questions whose answers would change the verdict.

## Out of scope
FERPA-adjacent concerns not evaluated (COPPA, state laws, GDPR, PPRA).

Rules:
- Quote or paraphrase the plan when citing it; do not invent details.
- If a control isn't mentioned, treat it as missing rather than assumed.
- Do not give legal advice. Recommend confirming with counsel and the
  institution's FERPA-designated official.
"""


_standards_agent = None
_ferpa_agent = None
_mcp_client = None


def _get_standards_agent():
    global _standards_agent, _mcp_client
    if _standards_agent is None:
        _mcp_client = get_streamable_http_mcp_client()
        sub_tools = [_mcp_client] if _mcp_client else []
        _standards_agent = Agent(
            model=load_model(),
            system_prompt=STANDARDS_PARTNER_PROMPT,
            tools=sub_tools,
        )
    return _standards_agent


def _get_ferpa_agent():
    global _ferpa_agent
    if _ferpa_agent is None:
        _ferpa_agent = Agent(
            model=load_model(),
            system_prompt=FERPA_PROMPT,
        )
    return _ferpa_agent


@tool
def standards_partner(prompt: str) -> str:
    """Ask StandardsPartner to research education/workforce standards or draft
    an implementation plan grounded in CASE, HROpen, or TCP data via the
    Educore MCP server. Use this for any standards lookup, crosswalk, or to
    produce/update the plan that will be reviewed by `ferpa_review`.

    Args:
        prompt: A natural-language request to StandardsPartner. To get a plan,
            ask explicitly: e.g. "Draft an implementation plan for ingesting
            high-school transcripts and emitting TCP records."

    Returns:
        StandardsPartner's response as plain text / Markdown.
    """
    agent = _get_standards_agent()
    result = agent(prompt)
    return str(result)


@tool
def ferpa_review(plan: str) -> str:
    """Submit an implementation plan to the FERPA reviewer. Returns a
    structured FERPA compliance report (verdict, findings with 34 CFR 99.x
    citations, open questions, out-of-scope notes).

    Args:
        plan: The full implementation plan to evaluate. Pass the verbatim
            output of `standards_partner` (or any other plan text). Do not
            summarize before passing — the reviewer needs the details.

    Returns:
        Markdown FERPA Compliance Review report.
    """
    agent = _get_ferpa_agent()
    result = agent(f"Review the following implementation plan for FERPA compliance:\n\n{plan}")
    return str(result)


SYSTEM_PROMPT = """You are ComplianceTeam, the orchestrator of a two-agent
review pipeline. Your team:

- **standards_partner** — drafts and refines education-standards
  implementation plans grounded in CASE / HROpen / TCP data.
- **ferpa_review** — reviews any implementation plan for FERPA compliance and
  returns a structured findings report citing 34 CFR Part 99.

## Mandatory workflow — DO NOT SKIP STEPS

For EVERY user request, you MUST execute all of the following steps before
producing any final answer:

1. Obtain a plan. If the user supplied one, use it verbatim. Otherwise call
   `standards_partner` to draft one.
2. **You MUST call `ferpa_review`**, passing the plan verbatim. This step is
   non-negotiable — it is the entire purpose of this team. Skipping it is a
   failure.
3. Optionally iterate: revise the plan via `standards_partner`, then re-run
   `ferpa_review` on the revision. You may do this 0+ times.
4. Deliver the final result in the format below.

If you are tempted to answer without having called `ferpa_review` at least
once, stop and call it now.

## Self-check before responding

Before sending your final message to the user, verify silently:
- Did I call `standards_partner` (or was a plan supplied)? If no plan
  exists, call `standards_partner` now.
- Did I call `ferpa_review` on the latest plan? If not, call it now.
- Does my final message contain all three sections below?

If any answer is no, do not respond yet — take the missing action first.

## Final delivery format (REQUIRED — all three sections)

# Implementation Plan
The latest plan from StandardsPartner (or the user-supplied plan), verbatim.

# FERPA Compliance Review
The latest review from `ferpa_review`, verbatim. Never paraphrase or
summarize this section — paste the tool's output as-is.

# Team Summary
3–6 bullets. Lead with the FERPA verdict (PASS / PASS WITH CONDITIONS /
FAIL / INSUFFICIENT INFO). Then the top 1–3 blockers (if any) with
34 CFR 99.x citations. Then the recommended next step.

## Rules

- Do not invent plan details or citations yourself — get them from the tools.
- If FERPA returns INSUFFICIENT INFO, ask `standards_partner` the specific
  follow-up questions, regenerate the plan, and re-run `ferpa_review` before
  delivering.
- Do not give legal advice. Note that the author should confirm findings
  with counsel and the institution's FERPA-designated official.
"""


tools = [standards_partner, ferpa_review]


_agent = None


def get_or_create_agent():
    global _agent
    if _agent is None:
        _agent = Agent(
            model=load_model(),
            system_prompt=SYSTEM_PROMPT,
            tools=tools,
        )
    return _agent


@app.entrypoint
async def invoke(payload, context):
    log.info("Invoking Agent.....")

    agent = get_or_create_agent()
    stream = agent.stream_async(payload.get("prompt"))

    async for event in stream:
        if "data" in event and isinstance(event["data"], str):
            yield event["data"]


if __name__ == "__main__":
    app.run()
