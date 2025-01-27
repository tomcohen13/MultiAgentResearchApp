"""Agents module"""

import os
from typing import List

from pydantic import BaseModel
from tavily import TavilyClient
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END, START
from langgraph.types import Send

# local imports
from agents.prompts import (
    CRITIQUE_PROMPT_TEMPLATE,
    FINAL_REVISION_PROMPT,
    RESEARCH_CRITIQUE_PROMPT,
    RESEARCH_PROMPT_TEMPLATE,
    WRITER_PROMPT_TEMPLATE,
)
from agents.constants import (
    ALL_TOPICS,
    SUBTOPICS_MAPPING,
    TOPIC_NAMES_MAPPING,
)
from agents.states import ResearchState, TopicState
from agents.llm import call_model


class SearchQueries(BaseModel):
    """a model representing the output we want to get from the model"""
    queries: List[str]


tavily = TavilyClient(os.environ.get("TAVILY_API_KEY"))


class TopicAgent:
    def __init__(self, model, task_id: str=None):
        self.model = model
        self.task_id = task_id
        self.workflow = self.build()

    def run_research(self, state: TopicState):
        """
        Runs the topic agent end-to-end.
        *NOTE: I ended up not going forward with this implementation
        as it provides less visibility into the agent state.*
        """
        workflow = self.build()
        chain = workflow.compile()
        config = {"configurable": {"thread_id": self.task_id}}

        final_draft = chain.invoke(
            dict(state, **{"topic": state['topic']}),
            config=config,
        )
        return {
            "reports": {state['topic']: final_draft['draft']},
            "task_status": {state['topic']: "complete"},
        }

    def build(self) -> StateGraph:
        """Create workflow for topic agent"""
        workflow = StateGraph(TopicState)
        workflow.add_node(self.node_name("research"), self.research_node)
        workflow.add_node(self.node_name("generate"), self.generate_node)
        workflow.add_node(self.node_name("critique"), self.critique_node)
        workflow.add_node(self.node_name("refine"), self.refine_node)
        workflow.add_node(self.node_name("to_parent"), self.to_parent_graph)

        workflow.set_entry_point(self.node_name("research"))

        workflow.add_edge(self.node_name("research"), self.node_name("generate"))
        workflow.add_conditional_edges(
            self.node_name("generate"),
            self.is_ready,
            {True: self.node_name("to_parent"), False: self.node_name("critique")},
        )
        workflow.add_edge(self.node_name("critique"), self.node_name("refine"))
        workflow.add_edge(self.node_name("refine"), self.node_name("generate"))
        workflow.add_edge(self.node_name("to_parent"), END)

        return workflow

    def node_name(self, node: str) -> str:
        """Helper function to generate node names from topic and node function"""
        return node + "_node"

    async def research_node(self, state: TopicState):
        """Generate search queries and gathers relevant documents using Tavily"""

        prompt = RESEARCH_PROMPT_TEMPLATE.invoke(
            {
                "topic": TOPIC_NAMES_MAPPING[state['topic']],
                "subtopics": SUBTOPICS_MAPPING[state['topic']],
            }
        )
        messages = [
            SystemMessage(content=prompt.text),
            HumanMessage(content=state["company"]),
        ]
        search_queries = await call_model(
            model=self.model,
            messages=messages,
            output_type=SearchQueries,
        )

        documents = state.get("docs", [])
        for query in search_queries.queries:
            # Normally I'd make the search tool configurable,
            # but since we're using Tavily, I just hardcode it here
            response = tavily.search(
                query=query,
                max_results=3,
                topic="news" if state['topic'] == "recent_news" else "general",
            )
            for result in response["results"]:
                documents.append(result["content"])

        return {"docs": documents, "topic": state['topic']}

    async def generate_node(self, state: TopicState):
        """Generates a draft based on the documents collected by Tavily."""

        # Join the docs gathered in the previous step
        docs = "\n\n".join(state.get("docs", []))
        prompt = WRITER_PROMPT_TEMPLATE.invoke(
            {
                "topic": TOPIC_NAMES_MAPPING[state['topic']],
                "subtopics": SUBTOPICS_MAPPING[state['topic']],
                "content": docs,
            }
        )

        messages = [
            SystemMessage(content=prompt.text),
            HumanMessage(content=state["company"]),
        ]
        response = await call_model(
            messages=messages,
            model=self.model,
        )
        return {
            "topic": state.get("topic"),
            "draft": response.content,
            "draft_number": state.get("draft_number", 0) + 1,
        }

    def is_ready(self, state: TopicState) -> bool:
        """Checks if the draft numbder has reached its max"""
        return state.get("draft_number") == state.get("max_drafts")
    
    def to_parent_graph(self, state: TopicState):
        """Passes relevant TopicAgent output to parent graph"""

        return {
            "reports": {state['topic']: state['draft']},
            "task_status": {state['topic']: "complete"},
        }

    async def critique_node(self, state: TopicState):
        """Generates a critique for the draft"""

        prompt = CRITIQUE_PROMPT_TEMPLATE.invoke(
            {"topic": TOPIC_NAMES_MAPPING[state['topic']]}
        )

        messages = [
            SystemMessage(content=prompt.text),
            HumanMessage(content=state["draft"]),
        ]
        response = await call_model(messages=messages, model=self.model)
        return {"critique": response.content, "topic": state.get("topic"),}

    async def refine_node(self, state: TopicState):
        """Finds more relevant info based on notes from critique"""

        messages = [
            SystemMessage(content=RESEARCH_CRITIQUE_PROMPT),
            HumanMessage(content=state["critique"]),
        ]
        search_queries = await call_model(
            messages=messages,
            model=self.model,
            output_type=SearchQueries,
        )
        documents = state["docs"] or []
        for query in search_queries.queries:
            response = tavily.search(query=query, max_results=2)
            for result in response["results"]:
                documents.append(result["content"])

        return {"docs": documents, "topic": state.get("topic")}


class CoordinatorAgent:
    def __init__(self, model, task: str, task_id: str):

        self.task = task
        self.model = model
        self.task_id = task_id
        self.workflow = self.build()

    def build(self) -> StateGraph:
        """Builds CoordinatorAgent workflow"""
        topic_agent = TopicAgent(self.model, self.task_id)

        # Add nodes
        workflow = StateGraph(ResearchState)
        workflow.add_node("router", self.router_node)
        workflow.add_node("topic_agent", topic_agent.workflow.compile())
        workflow.add_node("aggregate", self.aggregate_node)
        workflow.add_node("polish", self.formatting_node)

        # Add edges
        workflow.add_edge(START, "router")
        workflow.add_conditional_edges("router", self.parent_fanout, ["topic_agent"])
        workflow.add_edge("topic_agent", "aggregate")
        workflow.add_edge("aggregate", "polish")
        workflow.add_edge("polish", END)
        return workflow

    def parent_fanout(self, state: ResearchState):
        """Sends relevant information to topic agents given user topics"""
        return [
            Send(
                "topic_agent",
                {
                    "company": state['company'],
                    "topic": topic,
                    "max_drafts": state['max_drafts']
                },
            ) for topic in state["topics"]
        ]

    def router_node(self, state: ResearchState):
        """Sends initial input to all topic agents"""
        return {
            "company": state["company"],
            "max_drafts": state["max_drafts"],
            "task_id": self.task_id,
        }

    def aggregate_node(self, state: ResearchState):
        """Aggregates results from topic agents"""

        sections = "\n\n".join(state["reports"].values())
        return {"final_report": sections}

    async def formatting_node(self, state: ResearchState):
        """Polishes the aggregataed report for publishing"""
        prompt = FINAL_REVISION_PROMPT

        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content=state["final_report"]),
        ]
        response = await call_model(
            messages=messages, model=self.model,
        )
        return {"final_report": response.content}
