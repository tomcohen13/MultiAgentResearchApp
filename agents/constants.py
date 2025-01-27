"""Application constants"""

from typing import Mapping, Sequence

DEFAULT_MAX_REVISIONS: int = 2

MONGO_DB_NAME = "tavily"
MONGO_COLLECTION_NAME = "agent_states"

BACKGROUND_INFO = "background"
FINANCIAL_HEALTH = "financial_health"
MARKET_POSITION = "market_position"
RECENT_NEWS = "recent_news"

ALL_TOPICS: Sequence[str] = {
    BACKGROUND_INFO,
    FINANCIAL_HEALTH,
    MARKET_POSITION,
    RECENT_NEWS
}

TOPIC_NAMES_MAPPING: Mapping[str, str] = {
    BACKGROUND_INFO: "Background Information",
    FINANCIAL_HEALTH: "Financial Health",
    MARKET_POSITION: "Market Position",
    RECENT_NEWS: "Recent News",
}

SUBTOPICS_MAPPING: Mapping[str, str] = {
    FINANCIAL_HEALTH: "revenue, profits, debt, stock performance",
    MARKET_POSITION: "Competitors, market share, industry trends,",
    RECENT_NEWS: "Mergers, acquisitions, product launches, controversies",
    BACKGROUND_INFO: "Mission, vision, history, leadership, company culture",
}

NODE_TO_TEXT: Mapping[str, str] = {
    "router": "Initializing search...",
    "research_node": "Drafting the {topic} section...",
    "generate_node": "Finished drafting the {topic} section...",
    "critique_node": "Revising the {topic} section...",
    "refine_node": "Redrafting {topic} section...",
    "topic_agent": "Finished the {topic} section...",
    "to_parent_node": "Finished the {topic} section...",
    "aggregate": "Final touches...",
    "polish": ""
}
