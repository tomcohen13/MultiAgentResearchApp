"""Main app module"""
import os
import time
import secrets

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles

from pymongo import AsyncMongoClient
from pymongo.server_api import ServerApi

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

    company = request.query_params.get("company")
    criteria = request.query_params.get("criteria").split(";")

    # build agent for task
    task_id = int(time.time())
    agent = CoordinatorAgent(
        model=model,
        task=company,
        task_id=task_id,
    )
    graph = agent.workflow.compile(checkpointer=mongo_checkpointer)
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

            # if last node -- yield report
            if node == "polish":
                yield event[1][node]["final_report"]
                continue
            # yield a user-facing description of the current status
            topic = event[1][node].get("topic", "")
            yield NODE_TO_TEXT.get(node, node).format(
                topic=TOPIC_NAMES_MAPPING.get(topic, "")
            )
    return StreamingResponse(stream_events(), media_type="text/event-stream")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
