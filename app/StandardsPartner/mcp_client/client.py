import os
import logging
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp.mcp_client import MCPClient

logger = logging.getLogger(__name__)

EDUCORE_MCP_ENDPOINT = "https://educore.tqtmp.org/mcp"

def get_streamable_http_mcp_client() -> MCPClient:
    """MCP client for Educore standards (CASE frameworks, HROpen skills, competencies)."""
    return MCPClient(lambda: streamablehttp_client(EDUCORE_MCP_ENDPOINT))
