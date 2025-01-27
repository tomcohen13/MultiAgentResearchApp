"""LLM-related functions for all agents to use"""

from typing import List, Optional, TypedDict
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.messages import AnyMessage
from langchain_openai import ChatOpenAI


async def call_model(
    messages: List[AnyMessage],
    model: ChatOpenAI,
    output_type: Optional[BaseModel] = None,
) -> str:  # type: ignore
    """
    Calls OpenAI model with the given messages and returns (structured) output.

    Parameters:
        model (str): name of the model to use, from [...]
        temperature (float): temperature to use for model
        messages (list): list of LangGraph messages to send to the model
        output_type (TypedDict): type of structured output to return
    """
    if output_type is None:
        return await model.ainvoke(input=messages)
    else:
        return await model.with_structured_output(output_type).ainvoke(input=messages)
