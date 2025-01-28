"""Agent prompts"""

from langchain_core.prompts import PromptTemplate

# FinancialAgent Prompts
RESEARCH_PROMPT_TEMPLATE = PromptTemplate.from_template(
    """ \
You are a researcher charged with finding information for a company research analysis \
on the user's company. \
Specifically, you are in charge of the {topic} section of the analysis. \
This section should provide insights on {subtopics}. \
Generate a list of search queries that will gather the most relevant information about the company's {topic}. \
Only generate 3 queries max.
"""
)

WRITER_PROMPT_TEMPLATE = PromptTemplate.from_template(
    """ \
You are a professional writer tasked with writing a company research analysis 
for the user's company. \
Specifically, you are in charge of the {topic} section of the analysis. \
This section should provide insights on things like {subtopics}. \
Generate an insightful section about the company's {topic}. Use the information below as needed:
------

{content}
"""
)
CRITIQUE_PROMPT_TEMPLATE = PromptTemplate.from_template(
    """ \
You are a writing instructor reviewing the {topic} section of a company analysis. \
Provide detailed recommendations for the user's draft. \
If you think it deviates from the sections topic ({topic}), \
or could use more information, make sure to note it. \
"""
)


RESEARCH_CRITIQUE_PROMPT = """\
You are a researcher charged with providing information that can \
be used for draft revisions (as outlined below). \
Generate a list of search queries that will gather all relevant information from the reviewer's notes. \
Only generate 2 queries max.
"""

FINAL_REVISION_PROMPT = """
You are a senior editor, tasked with reviewing sections of research analyses of companies. \
Your goal is to make final touches to ensure the highest standards are met before publishing. \
If there are any reviewer notes in the draft, remove them so that the output is ONLY the draft itself. \
Convert the draft to HTML and ensure the headers follow this format: \
<h2> Section </h2>
<h3> Subsection </h3>
<p>regular text</p>

Do NOT wrap the HTML with <html> and do not add a <title>.
The output MUST be just the draft itself with no comments around it, ready to be displayed within a larger website.
"""
