"""Main app module"""
import os
import time
import secrets
import asyncio

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles

from pymongo import AsyncMongoClient
from pymongo.server_api import ServerApi

from langchain.callbacks.streaming_aiter import AsyncIteratorCallbackHandler
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.mongodb.aio import AsyncMongoDBSaver

from agents.agents import CoordinatorAgent
from agents.constants import (
    DEFAULT_MAX_REVISIONS,
    MONGO_CHECKPOINTS_COLLECTION_NAME,
    MONGO_DB_NAME,
    MONGO_WRITES_COLLECTION_NAME,
    NODE_TO_TEXT,
    TOPIC_NAMES_MAPPING,
)


from dotenv import load_dotenv
load_dotenv()

# Define app middleware
middleware = [
    Middleware(
        SessionMiddleware,
        secret_key=os.environ.get("SECRET_KEY", secrets.token_urlsafe(16)),
    )
]

app = FastAPI(middleware=middleware)

# html/css
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Connect to mongo client
client = AsyncMongoClient(
    os.environ.get("MONGO_URI"),
    server_api=ServerApi("1"),
    uuidRepresentation="standard",
)

# Send a ping to confirm a successful connection
try:
    client.admin.command("ping")
    print("Successfully connected to MongoDB!")
except Exception as e:
    print(e)

# Create a checkpointer for the agent
db = client.get_database(MONGO_DB_NAME)
mongo_checkpointer = None


model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.1,
    streaming=True,
)

@app.on_event("startup")
async def startup_event():
    global mongo_checkpointer
    mongo_checkpointer = AsyncMongoDBSaver(
        client,
        db_name=MONGO_DB_NAME,
        checkpoint_collection_name=MONGO_CHECKPOINTS_COLLECTION_NAME,
        writes_collection_name=MONGO_WRITES_COLLECTION_NAME,
    )
    print("AsyncMongoDBSaver initialized.")


@app.get("/")
def root(request: Request):
    return templates.TemplateResponse(name="index.html", context={"request": request})


@app.get("/research")
async def research(request: Request):
    """
    When a user makes a GET request, passing in a company and search criteria,
    the team of agents will initialize and begin streaming events back to the client.
    Up until the final node, intermediate events will flash to the UI 
    to update the user on the status of the task. Once the final step is reached,
    the agent will stream its output token-by-token for better user experience.

    Parameters
        request: a get request send from the client with 'company' and 'criteria' params.
    """
    company = request.query_params.get("company")
    criteria = request.query_params.get("criteria").split(";")

    # build agent for task
    task_id = int(time.time())
    agent = CoordinatorAgent(
        model=model,
        task=company,
        task_id=task_id,
    )
    # Early-stopping at "polish" which is the final node
    graph = agent.workflow.compile(
        checkpointer=mongo_checkpointer,
        interrupt_before=["polish"],
    )
    initial_input = {
        "company": company,
        "topics": criteria,
        "max_drafts": DEFAULT_MAX_REVISIONS,
    }
    config = {"configurable": {"thread_id": task_id}}

    # Stream events to UI for better user experience
    async def stream_events():
        async for event in graph.astream(input=initial_input, config=config, subgraphs=True):
            # get node name
            node = next(iter(event[1]))
            # yield a user-facing description of the current status
            try:
                # stream a description of the current node
                topic = event[1][node].get("topic", "")
                topic_name = TOPIC_NAMES_MAPPING.get(topic, "")
                status_description = NODE_TO_TEXT.get(node, node)
                yield status_description.format(topic=topic_name)
            except:
                continue

        # Switch to token-streaming using special token
        yield "<REPORT_STREAM>"
        # stream the final node of the graph
        async for msg, metadata in graph.astream(input=None, config=config, stream_mode="messages"):
            yield msg.content
            await asyncio.sleep(0.05)
    
    return StreamingResponse(stream_events(), media_type="text/html")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
