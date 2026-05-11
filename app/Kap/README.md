# Kap

Strands-based AgentCore runtime mirroring the Robert Kaplinsky persona from
Bedrock Agent `arn:aws:bedrock:us-east-2:650251696752:agent/VFYEXNWH2I`.

## Foundation model
`us.amazon.nova-lite-v1:0` (cross-region inference profile, mirroring the
source agent's `foundationModel`).

## Not ported from the source Bedrock Agent
- SUPERVISOR multi-agent collaboration
- Guardrail `fvq543jy79tz`
- Prompt-override templates (PRE/ORCH/POST processing, KB response gen)
- `$prompt_session_attributes$` injection (Bedrock-Agents-only template)
- Action groups / knowledge bases (none surfaced — re-check if expected)

## Run locally
```bash
agentcore dev -r Kap
```
