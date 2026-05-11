from strands.models.bedrock import BedrockModel


def load_model() -> BedrockModel:
    """Get Bedrock model client using IAM credentials.

    Mirrors the foundation model from Bedrock Agent VFYEXNWH2I (Kap):
    Amazon Nova Lite via the us. cross-region inference profile.
    """
    return BedrockModel(model_id="us.amazon.nova-lite-v1:0")
