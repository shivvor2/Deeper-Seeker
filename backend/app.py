from typing import List, Dict, Any, Callable
import os
import requests
import json
from openai import OpenAI
from groq import Groq
import re
from pathlib import Path
from datetime import datetime

import concurrent.futures
from exa_py import Exa
from google import genai
from dotenv import load_dotenv

from .llm_providers.mappings import (
    GENERATE_FOLLOWUP, 
    GENERATE_RESEARCH_PLAN, 
    GENERATE_QUERIES_FOR_STEP, 
    GENERATE_REPORT
)

load_dotenv()

# Search Engines
EXA_API_KEY = os.getenv("EXA_API_KEY")
EXA_BASE_URL = os.getenv("EXA_BASE_URL")
exa = Exa(EXA_API_KEY) # This is somehow not used but exceeds the scope of the pr

# LLM clients
# OpenAI (or openAI compatible inference providers)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL") # If not set OpenAI will be used
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
openai_client = OpenAI(api_key = OPENAI_API_KEY)

# Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL")
groq_client = Groq(api_key=GROQ_API_KEY)

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# App config (see config.json)
config_path = os.getenv("CONFIG_PATH") # Relative to app.py
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_path)

clients = {
    "openai": openai_client,
    "groq": groq_client,
    "gemini": gemini_client
}

with open(config_path, 'r') as file:
    config = json.load(file)

# Which LLM service to be used for each step
service_followup: str = config["ai_providers"]["followup"]
service_research_plan: str = config["ai_providers"]["research_plan"]
service_queries_for_step: str = config["ai_providers"]["query_generation"]
service_report: str = config["ai_providers"]["report_generation"]

# Exact model name for each step
model_followup: str = config["models"][service_followup]["followup"]
model_research_plan: str = config["models"][service_research_plan]["research_plan"]
model_query_for_step: str = config["models"][service_queries_for_step]["query_generation"]
model_report: str = config["models"][service_report]["report_generation"]

# We do not set the types of the callable since the code structure is not yet stable
generate_followup: Callable[..., Any] = GENERATE_FOLLOWUP[service_followup]
generate_research_plan: Callable[..., Any] = GENERATE_RESEARCH_PLAN[service_research_plan]
generate_queries_for_step: Callable[..., Any] = GENERATE_QUERIES_FOR_STEP[service_queries_for_step]
generate_report: Callable[..., Any] = GENERATE_REPORT[service_report]

# Function to write output to output.md
# def write_output_to_file(output: str, filename: str = "output.md"):
#     """Write the output to a markdown file."""
#     with open(filename, "a") as file:
#         file.write(output + "\n\n")

# Functions

def run_followup_loop(initial_query: str, iterations: int = 3) -> Dict[str, Any]:
    """Iteratively generate follow-up questions and collect user responses."""
    context = initial_query
    history = []
    for i in range(iterations):
        followup = generate_followup(client = clients[service_followup],model = model_followup, context = context)
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

def execute_plan(plan_steps: Dict[str, str]) -> Dict:
    """ Execute each step of the research plan and fetch search results. """
    search_queries_and_responses = {"plan": {}}

    for step, description in plan_steps.items():
        # Generate search queries for the step
        search_queries = generate_queries_for_step(client = clients[service_queries_for_step], model = model_query_for_step, step = step, description = description)
        
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

def generate_unique_filename(base_format: str, save_path: str) -> str:
    """
    Generate a unique filename based on the format specified in config.
    Supports patterns like:
    - {date} : current date
    - {time} : current time
    - {n} : incremental number for collision avoidance
    
    Example formats:
    - "report_{date}_{n}.md"
    - "final_report_{n}.md"
    - "{date}_research_{time}.md"
    """
    
    # Create the save directory if it doesn't exist
    save_path = Path(save_path)
    save_path.mkdir(parents=True, exist_ok=True)
    
    # Replace date and time patterns
    now = datetime.now()
    filename = base_format.replace('{date}', now.strftime('%Y%m%d'))
    filename = filename.replace('{time}', now.strftime('%H%M%S'))
    
    # Handle incremental numbering if {n} is in the format
    if '{n}' in filename:
        pattern = filename.replace('{n}', r'(\d*)')
        pattern = '^' + pattern.replace('.', r'\.') + '$'
        
        # Get existing files that match the pattern
        existing_files = []
        for f in save_path.glob('*'):
            if re.match(pattern, f.name):
                match = re.search(pattern, f.name)
                num = int(match.group(1)) if match.group(1) else 0
                existing_files.append(num)
                
        # Find the next available number
        next_num = 1
        if existing_files:
            next_num = max(existing_files) + 1
            
        filename = filename.replace('{n}', str(next_num))
    else:
        # If no {n} pattern but file exists, append number
        base_path = save_path / filename
        if base_path.exists():
            name_parts = filename.rsplit('.', 1)
            counter = 1
            while (save_path / filename).exists():
                filename = f"{name_parts[0]}{counter}.{name_parts[1]}"
                counter += 1

    return str(save_path / filename)

# save the report to a markdown file
def save_report_to_file(report: str, config: dict):
    """Save the generated report to a markdown file."""
    save_path = config['settings'].get('report_save_path', 'reports')
    name_format = config['settings'].get('report_name_format', 'final_report_{n}.md')
    
    filename = generate_unique_filename(name_format, save_path)
    
    with open(filename, "w") as file:
        file.write(report)
    return filename

# Main 
if __name__ == "__main__":
    # Clear the output file at the start of the script
    # open("output.md", "w").close()

    initial_query = input("Enter your query:")
    followup_result = run_followup_loop(initial_query, iterations=3)
    research_plan = generate_research_plan(client = clients[service_research_plan], model = model_research_plan, initial_query = followup_result["initial_query"], followup_context = followup_result["final_context"])
    plan_steps = research_plan["plan"]
    result = execute_plan(plan_steps)

    # Extract learnings from the result
    learnings_string = extract_learnings(result)

    # report generation call
    report = generate_report(client = clients[service_report], model = model_report, prompt = initial_query, learnings = learnings_string)

    # Save the report
    save_report_to_file(report)
    print("Report generated and saved to final_report.md")