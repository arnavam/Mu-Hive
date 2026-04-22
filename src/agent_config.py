from src.config import load_config

def get_agent_settings(agent_name):
    """
    Returns specific configuration for an agent persona.
    Used for routing and tier management.
    """
    pipeline_cfg = load_config("pipeline")
    routing = pipeline_cfg.get("ig_routing", {})
    return routing

# Agents can also store their system prompts here for easier management
AGENT_PROMPTS = {
    "classifier": "You are a classifier agent...",
    "validater": "You are a validater agent...",
    "summarizer": "You are a summarizer agent..."
}
