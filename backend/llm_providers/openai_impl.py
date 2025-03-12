from openai import OpenAI
from typing import Dict
import json

from ..prompts import FOLLOWUP_PROMPT, RESEARCH_PLAN_PROMPT, GEN_QUERY_PROMPT

# OpenAI/Groq implementations
def generate_followup(client: OpenAI, model: str, context: str) -> Dict:
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": FOLLOWUP_PROMPT},
            {"role": "user", "content": context}
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(completion.choices[0].message.content)

def generate_research_plan(client: OpenAI, model: str, initial_query: str, followup_context: str) -> Dict:
    combined_context = initial_query + followup_context
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": RESEARCH_PLAN_PROMPT},
            {"role": "user", "content": combined_context}
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(completion.choices[0].message.content)

def generate_queries_for_step(client: OpenAI, model: str, step: str, description: str) -> Dict:
    # Implementation here
    try:
        completion = client.chat.completions.create(
            model=model,
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

# TODO
def generate_report(client: OpenAI, model: str, prompt: str, learnings: str) -> str:
    # Implementation here
    raise NotImplementedError()