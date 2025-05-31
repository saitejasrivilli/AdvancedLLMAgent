import os
import logging
import re
from typing import Dict, List, Tuple

from src.agents import LLM_Agent, Reasoning_Agent
from src.lean_runner import execute_lean_code
from src.parser import extract_goal_statement
from src.embedding_models import OpenAIEmbeddingModel
from src.embedding_db import VectorDB

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type alias
LeanCode = Dict[str, str]

# Instantiate agents
planner = Reasoning_Agent(model="o3-mini")
feedback = Reasoning_Agent(model="o3-mini")
generator = LLM_Agent(model="gpt-4o")

def query_relevant_context(query: str, top_k: int = 5) -> str:
    """
    Lightweight wrapper to get top-k relevant chunks using VectorDB.
    """
    model = OpenAIEmbeddingModel()
    chunks, _ = VectorDB.get_top_k("database.npy", model, query, k=top_k)
    return "\n\n".join(chunks)

def strip_markdown_fencing(text: str) -> str:
    """
    Removes markdown code block markers (``` or ```lean) from LLM output.
    """
    return re.sub(r"```(?:lean)?|```", "", text).strip()

def main_workflow(problem_description: str, task_lean_code: str = "") -> LeanCode:
    """
    Main workflow for the coding agent.
    """
    def solve_task(goal: str) -> str:
        plan_prompt = [
            {"role": "system", "content": "You are a planning agent for Lean 4."},
            {"role": "user", "content": f"Given the task, return a concise, actionable plan.\n\nTASK:\n{goal}"}
        ]
        plan = planner.get_response(plan_prompt)
        context = query_relevant_context(goal)

        def build_prompt(updated_plan: str):
            return [
                {"role": "system", "content": "You are a Lean 4 code generation agent."},
                {"role": "user", "content": f"Use this plan and context to generate the requested Lean code or proof.\n"
                                            f"Only return valid Lean syntax.\n\nPLAN:\n{updated_plan}\n\nCONTEXT:\n{context}\n\nTASK:\n{goal}"}
            ]

        last_attempt = ""
        for _ in range(2):
            candidate = generator.get_response(build_prompt(plan)).strip()
            valid, error_msg = execute_lean_code(candidate)
            if valid:
                return candidate
            feedback_prompt = [
                {"role": "system", "content": "You are a Lean 4 feedback agent."},
                {"role": "user", "content": f"The following code failed with an error. Refine the plan.\n\n"
                                            f"FAILED CODE:\n{candidate}\n\nERROR:\n{error_msg}\n\nPLAN:\n{plan}"}
            ]
            plan = feedback.get_response(feedback_prompt)
            last_attempt = candidate

        return last_attempt

    needs_code = "{{code}}" in task_lean_code
    needs_proof = "{{proof}}" in task_lean_code

    code_result_raw = solve_task("Implement the function described below:\n" + problem_description) if needs_code else "sorry"
    proof_result_raw = solve_task("Prove the theorem specified in the Lean code template using Mathlib and Aesop.") if needs_proof else "sorry"

    code_result = strip_markdown_fencing(code_result_raw)
    proof_result = strip_markdown_fencing(proof_result_raw)

    print("=== Final Lean file ===")
    print(task_lean_code.replace("{{code}}", code_result).replace("{{proof}}", proof_result))

    return {
        "code": code_result,
        "proof": proof_result
    }

def get_problem_and_code_from_taskpath(task_path: str) -> Tuple[str, str]:
    with open(os.path.join(task_path, "description.txt"), "r") as f:
        problem_description = f.read()
    with open(os.path.join(task_path, "task.lean"), "r") as f:
        lean_code_template = f.read()
    return problem_description, lean_code_template

def get_unit_tests_from_taskpath(task_path: str) -> List[str]:
    with open(os.path.join(task_path, "tests.lean"), "r") as f:
        unit_tests = f.read()
    return unit_tests

def get_task_lean_template_from_taskpath(task_path: str) -> str:
    with open(os.path.join(task_path, "task.lean"), "r") as f:
        task_lean_template = f.read()
    return task_lean_template
