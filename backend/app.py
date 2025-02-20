from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import requests
import json
from openai import OpenAI
from groq import Groq
from colorama import Fore, Style, init
import time
import pyfiglet
import concurrent.futures
from exa_py import Exa
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()


EXA_API_KEY = os.getenv("EXA_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
EXA_BASE_URL = os.getenv("EXA_BASE_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

exa = Exa(EXA_API_KEY)
openai_client = Groq(api_key=GROQ_API_KEY)
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# Pydantic model for structured Gemini response
class ReportResponse(BaseModel):
    reportMarkdown: str

# Prompts
FOLLOWUP_PROMPT = """you are a highly capable research analyst. Given a user query and additional context (previous followup questions), your job is to analyze the context and ask clarifying questions/follow-up questions to complete the query and context for the research agent.
Return the follow-up questions in a structured JSON format as follows:
{
  "question": "the follow-up question to the user",
  "query_context": "query/query + context given to you."
}
"""

RESEARCH_PLAN_PROMPT = """You are an expert research analyst who excels at creating multi-step approaches and research plans. Given a user query and additional context, your task is to create a structured, multi-step research plan to effectively answer the query.
Each step should break down the research process into logical, sequential parts. These steps will later be used to generate specific search queries for a research agent to browse the internet and gather relevant information.Generate only 5 steps.
Return the research plan in a structured JSON format as follows:
{
  "plan": {
    "step 1": "Description of step 1",
    "step 2": "Description of step 2",
    ...
    "step 5":
  }
}
"""

GEN_QUERY_PROMPT = """You are a research analyst agent who is tasked with generating Browser search queries based on the research plan given to you.The current date is 20th Feb 2025 The search queries should be specific and focused such that they can be used to browse Google/Bing to gather relevant resources and information useful for executing the research plan step. 
Return 3 search queries for each step in JSON format as follows:
{
 "plan_step": "Description of the plan step",
 "search_queries": ["query1", "query2", "query3"]
}
"""

# Function to write output to output.md
# def write_output_to_file(output: str, filename: str = "output.md"):
#     """Write the output to a markdown file."""
#     with open(filename, "a") as file:
#         file.write(output + "\n\n")

# Functions
def generate_followup(context: str) -> Dict:
    """Generate follow-up questions based on the user query and context."""
    try:
        completion = openai_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": FOLLOWUP_PROMPT},
                {"role": "user", "content": context}
            ],
            response_format={"type": "json_object"},
        )
        return json.loads(completion.choices[0].message.content)
    except json.JSONDecodeError:
        return {"question": "Could you clarify further?", "query_context": context}

def run_followup_loop(initial_query: str, iterations: int = 3) -> Dict[str, Any]:
    """Iteratively generate follow-up questions and collect user responses."""
    context = initial_query
    history = []
    for i in range(iterations):
        followup = generate_followup(context)
        question = followup.get("question", "Could you elaborate?")
        print(f"\nAssistant: {question}")
        user_answer = input("Your response: ")
        context += f" Follow-up Q: {question} Follow-up A: {user_answer}"
        history.append({
            "iteration": i + 1,
            "question": question,
            "answer": user_answer,
            "context_snapshot": context
        })
        # Write each interaction to the output file
        # write_output_to_file(f"### Follow-up Interaction {i + 1}\n**Question:** {question}\n**Answer:** {user_answer}\n**Context Snapshot:** {context}")
    return {
        "final_context": context,
        "interaction_history": history,
        "initial_query": initial_query,
        "total_iterations": iterations
    }

def generate_research_plan(initial_query: str, followup_context: str) -> Dict:
    """Generate a research plan based on the query and follow-up context."""
    try:
        combined_context = initial_query + followup_context
        completion = openai_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": RESEARCH_PLAN_PROMPT},
                {"role": "user", "content": combined_context}
            ],
            response_format={"type": "json_object"},
        )
        research_plan = json.loads(completion.choices[0].message.content)
        # Write the research plan to the output file
        # write_output_to_file("### Research Plan\n" + json.dumps(research_plan, indent=2))
        return research_plan
    except json.JSONDecodeError:
        return {"plan": "Could you clarify further?"}

def generate_queries_for_step(step: str, description: str) -> Dict:
    """Generate search queries for a specific research step."""
    try:
        completion = openai_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": GEN_QUERY_PROMPT},
                {"role": "user", "content": description}
            ],
            response_format={"type": "json_object"},
        )
        queries = json.loads(completion.choices[0].message.content)
        # Write the generated queries to the output file
        # write_output_to_file(f"### Generated Queries for {step}\n" + json.dumps(queries, indent=2))
        return {step: queries}
    except json.JSONDecodeError:
        return {step: {"error": "Failed to generate queries"}}

def execute_plan(plan_steps: Dict[str, str]) -> Dict:
    """ Execute each step of the research plan and fetch search results. """
    search_queries_and_responses = {"plan": {}}

    for step, description in plan_steps.items():
        # Generate search queries for the step
        search_queries = generate_queries_for_step(step, description)
        
        if step in search_queries:
            queries = search_queries[step].get("search_queries", [])
        else:
            queries = ["No queries generated"]
        
        # Execute the queries and fetch search results
        search_results = execute_queries(queries)

        print({
            "plan_step": description,
            "search_queries": queries,
            "search_results": search_results  # Includes answers and citations
        })

        # Store results
        search_queries_and_responses["plan"][step] = {
            "plan_step": description,
            "search_queries": queries,
            "search_results": search_results  # Includes answers and citations
        }

        # Write the search results to the output file
        # write_output_to_file(f"### Search Results for {step}\n" + json.dumps({
        #     "plan_step": description,
        #     "search_queries": queries,
        #     "search_results": search_results
        # }, indent=2))

    return search_queries_and_responses

def execute_queries(step_queries: Dict[str, List[str]]) -> Dict:
    """Execute search queries in parallel and return the top 3 citations from each result."""
    search_results = {"queries": {}}

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_to_query = {executor.submit(web_search_wrapper, query): query for query in step_queries}

        for future in concurrent.futures.as_completed(future_to_query):
            query = future_to_query[future]
            try:
                response = future.result()
                answer = response.get("answer", "No answer found")
                citations = response.get("citations", [])[:1]  # Get top 3 citations

                search_results["queries"][query] = {
                    "answer": answer,
                    "top_citations": citations
                }
            except Exception as exc:
                search_results["queries"][query] = {
                    "error": str(exc)
                }

    return search_results

# wrapper for web search -- roadmap -> add multiple supports (exa, firecrawl, tavily search)
def web_search_wrapper(query:str)->Dict:
    """a wrapper around exa answer api"""
    data = {"query": query , "text" : True}
    try:
        response = requests.post(EXA_BASE_URL, json=data , headers={"Authorization" :  f"Bearer {EXA_API_KEY}", "Content-type" : "application/json"})
        response.raise_for_status
        return response.json()
    except requests.exceptions.RequestException as error:
        return {"error" : str(error)}

# extract learning from the search results
def extract_learnings(output: dict) -> str:
    """Extract learnings from the search results."""
    learnings = []
    for step, data in output["plan"].items():
        plan_step = data["plan_step"]
        search_results = data["search_results"]["queries"]
        for query, result in search_results.items():
            answer = result["answer"]
            citations = result["top_citations"]
            learnings.append(f"### {plan_step}\n**Query:** {query}\n**Answer:** {answer}\n**Citations:** {json.dumps(citations, indent=2)}")
    return "\n\n".join(learnings)

# Report generation function - LLM used - gemini2.0
def generate_report(prompt: str, learnings: str) -> str:
    """Generate a detailed markdown report using Google Gemini."""
    sys_instruct = "You are a professional research analyst. Your task is to generate a detailed 3-page markdown report based on the provided research data."
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ReportResponse,
            ),
            contents=[
                f"Given the following prompt from the user, write a final report on the topic using "
                f"the learnings from research. Return a JSON object with a 'reportMarkdown' field "
                f"containing a detailed markdown report (aim for 3+ pages). Include ALL the learnings. use the text field corresponding to the query.The report should be very detailed with inline citations in markdown format :- (text)[source link] in each subsection "
                f"from research:\n\n<prompt>{prompt}</prompt>\n\n"
                f"Here are all the learnings from research:\n\n<learnings>\n{learnings}\n</learnings>"
            ]
        )
        # response parsing using pydantic model
        report_response = ReportResponse.parse_raw(response.text)
        return report_response.reportMarkdown
    except Exception as e:
        print(f"Error generating report: {e}")
        return f"Error generating report: {e}"

# save the report to a markdown file
def save_report_to_file(report: str, filename: str = "final_report1.md"):
    """Save the generated report to a markdown file."""
    with open(filename, "w") as file:
        file.write(report)

# Main 
if __name__ == "__main__":
    # Clear the output file at the start of the script
    # open("output.md", "w").close()

    initial_query = input("Enter your query:")
    followup_result = run_followup_loop(initial_query, iterations=3)
    research_plan = generate_research_plan(followup_result["initial_query"], followup_result["final_context"])
    plan_steps = research_plan["plan"]
    result = execute_plan(plan_steps)

    # Extract learnings from the result
    learnings_string = extract_learnings(result)

    # report generation call
    report = generate_report(initial_query, learnings_string)

    # Save the report
    save_report_to_file(report)
    print("Report generated and saved to final_report.md")