from botocore.config import Config
from strands.models.bedrock import BedrockModel


_BOTO_CONFIG = Config(
    read_timeout=500,
    connect_timeout=30,
    retries={"max_attempts": 5, "mode": "adaptive"},
)


def load_model() -> BedrockModel:
    """Get Bedrock model client using IAM credentials.

    The default botocore read_timeout is 60s, which is too short for
    multi-agent runs where the orchestrator re-prompts Bedrock with large
    tool outputs (e.g. a full implementation plan). Bump it to 5 minutes.
    """
    return BedrockModel(
        model_id="global.anthropic.claude-sonnet-4-5-20250929-v1:0",
        boto_client_config=_BOTO_CONFIG,
    )
