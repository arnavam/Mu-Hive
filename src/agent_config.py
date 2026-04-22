from src.config import load_config

def get_agent_settings(agent_name):
    """
    Returns specific configuration for an agent persona.
    Used for routing and tier management.
    """
    pipeline_cfg = load_config("pipeline")
    routing = pipeline_cfg.get("ig_routing", {})
    return routing

# Agents store their system prompts here for easier management and consistency
AGENT_PROMPTS = {
    "classifier": "You are a filtering agent. Your job is to remove items that are purely spam, ads, or completely unrelated to the technical field.",
    "validater": "You are a technical verifier for the {ig} Interest Group. Focus on these keywords: {keywords}. Relevant items include hackathons, internships, workshops, research papers, and significant technical news or breakthroughs. Reject spam, marketing fluff, and duplicates.",
    "summarizer": "You are a structuring agent for the {ig} Interest Group. Categorize items into: {categories}. Summarize in 2 sentences. Extract any deadlines found."
}
