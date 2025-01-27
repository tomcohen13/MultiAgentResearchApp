# Multi-Agent Company Researcher

## Overview
This project is a multi-agent web application, built with LangGraph and Tavily, that executes comprehensive company research based on user-specified criteria. The agents collaborate to research, synthesize, and aggregate relevant information like financial health, market position, recent news, and background information

## Main Points

### 1. **Multi-Agent Collaboration**
- A parent CoordinatorAgent initializes and orchestrates ad-hoc, topic-focused agents based on user input.
- Each topic agent undertakes a specific research topic/section in the final report.
- The CoordinatorAgent aggregates and polishes the outputs of the topic agents into an HTML-formatted final report.

### 2. **Asynchronous Workflow & Streaming**
- Checkpoints are stored in MongoDB using `AsyncMongoClient` and `AsyncMongoDBSaver`, ensuring efficient state recovery and monitoring.
- Topic agents work in parallel to speed up research.
- Events are streamed as they happen to the client for smoother UX.


### 3. **Scalability and Flexibility**
- Configurable to support more topics.


## Setup Instructions

### 1. **Clone the Repository**
```bash
git clone https://github.com/tomcohen13/MultiAgentResearchApp.git
cd MultiAgentResearchApp
```

### 2. **Install Dependencies**
Ensure you have Python 3.10 or later.
```bash
pip install -r requirements.txt
```

### 3. **Environment Variables**
Create a `.env` file in the project root and add the following:
```
TAVILY_API_KEY=<your_tavily_api_key>
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=my_database
MONGO_COLLECTION_NAME=my_collection
```

### 4. **Run the Application Locally**
Start the FastAPI app:
```bash
python3 main.py
```
or (if you're making edits)
```bash
uvicorn main:app --reload
```
Access the app at `http://127.0.0.1:8000`.


## Usage

![alt ui](static/images/ui-screenshot.png "The UI")

1. Navigate to the web interface.
2. Enter a **company name** and select desired research criteria from the topics below the search bar.
3. Click **Start Research** to trigger the workflow.
4. Watch as results stream in real-time on the page.


## **Project Structure:**
```
app/
│
├── main.py   # Entry point for FastAPI, app logic
├── requirements.txt # Python dependencies
├── Procfile         # Specifies how to run the app on EB
├── agents/   # main backend logic
│   └── agents.py   # Core agents logic
│   └── constants.py   # Application-wide constants
│   └── llm.py   # llm-related functions
│   └── prompts.py   # agent prompts
│   └── states.py   # agent states
├── static/   # main backend logic
│   └── header-fade.js   # fade-in effect
│   └── script.js   # Client-side logic for streaming and UI updates
│   └── style.css   # main styling file
├── templates/   # HTML files
│   └── index.html   # Website HTML
└── README.md        # Documentation of the project
```

## Deployment

### AWS Elastic Beanstalk
1. Package the application into a zip file including:
   - `application.py` or `main.py`
   - `requirements.txt`
   - `Procfile`

2. Deploy the package to AWS Elastic Beanstalk:
   - Use the Elastic Beanstalk CLI or CodePipeline to automate deployments.

3. Enable multiple instances and auto-scaling to support collaborative agents.


## Monitoring and Scaling

- Use AWS CloudWatch to monitor metrics like CPU utilization and memory usage.
- Adjust auto-scaling settings in the Elastic Beanstalk console as needed.


## Future Enhancements
- Improved error handling for robust performance.
- Input validation.
- Architecture improvements.
- Enhanced visualizations of results.

## Thoughts & Disclaimer
- I initially hard-coded the architecture with the selected topics, adding designated subgraphs per user-specified topic. Although the graph as a whole was not too overwhelming for 4 topics, it didn't feel very elegant for a larger-scale application, so I resorted to having one TopicAgent architecture that gets replicated and run in parallel, ad-hoc, given the user-specified topics. This is similar to the GPT-Researcher implementation. The downside of that is that the nodes are named generically. Curious to hear your thoughts!
