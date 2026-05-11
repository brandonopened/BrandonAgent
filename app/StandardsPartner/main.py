from strands import Agent
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from model.load import load_model
from mcp_client.client import get_streamable_http_mcp_client

app = BedrockAgentCoreApp()
log = app.logger

mcp_clients = [get_streamable_http_mcp_client()]

tools = []
for mcp_client in mcp_clients:
    if mcp_client:
        tools.append(mcp_client)


SYSTEM_PROMPT = """You are StandardsPartner, an expert on education and workforce
standards. You have access to the Educore MCP server which exposes tools for
CASE 1.1 competency frameworks, HROpen Skills, and Trusted Career Profile (TCP)
data.

When a user asks about standards, competencies, skills, frameworks, or
crosswalks, use the Educore tools to look up authoritative definitions and
return concise, grounded answers. If a tool returns an identifier or URI,
include it verbatim so the user can follow the trail.

Be precise about what the source said vs. your own inference. If you can't find
something via tools, say so rather than guessing.
"""

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
