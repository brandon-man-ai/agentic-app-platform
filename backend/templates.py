"""Template definitions for different sandbox environments."""

import os
from typing import TypedDict, Optional


class TemplateInfo(TypedDict):
    name: str
    lib: list[str]
    file: str
    instructions: str
    port: Optional[int]


def get_template_id_suffix(template_id: str) -> str:
    """Add -dev suffix in development mode."""
    is_dev = os.getenv("NODE_ENV", "development") == "development"
    return f"{template_id}" if is_dev else template_id


def get_template_id(template_id: str) -> str:
    """Remove -dev suffix from template ID."""
    return template_id.replace("-dev", "")


TEMPLATES: dict[str, TemplateInfo] = {
   get_template_id_suffix("nextjs-developer"): {
        "name": "Next.js developer",
        "lib": [
            "nextjs@14.2.5",
            "typescript",
            "@types/node",
            "@types/react",
            "@types/react-dom",
            "postcss",
            "tailwindcss",
            "shadcn",
        ],
        "file": "pages/index.tsx",
        "instructions": "A Next.js 13+ app that reloads automatically. Using the pages router.",
        "port": 3000,
    },
    }

"""
    "code-interpreter-v1": {
        "name": "Python data analyst",
        "lib": [
            "python",
            "jupyter",
            "numpy",
            "pandas",
            "matplotlib",
            "seaborn",
            "plotly",
        ],
        "file": "script.py",
        "instructions": "Runs code as a Jupyter notebook cell. Strong data analysis angle. Can use complex visualisation to explain results.",
        "port": None,
    },
 
    get_template_id_suffix("vue-developer"): {
        "name": "Vue.js developer",
        "lib": ["vue@latest", "nuxt@3.13.0", "tailwindcss"],
        "file": "app/app.vue",
        "instructions": "A Vue.js 3+ app that reloads automatically. Only when asked specifically for a Vue app.",
        "port": 3000,
    },
    get_template_id_suffix("streamlit-developer"): {
        "name": "Streamlit developer",
        "lib": [
            "streamlit",
            "pandas",
            "numpy",
            "matplotlib",
            "requests",
            "seaborn",
            "plotly",
        ],
        "file": "app.py",
        "instructions": "A streamlit app that reloads automatically.",
        "port": 8501,
    },
    get_template_id_suffix("gradio-developer"): {
        "name": "Gradio developer",
        "lib": [
            "gradio",
            "pandas",
            "numpy",
            "matplotlib",
            "requests",
            "seaborn",
            "plotly",
        ],
        "file": "app.py",
        "instructions": "A gradio app. Gradio Blocks/Interface should be called demo.",
        "port": 7860,
    },
    """

def templates_to_prompt(templates: dict[str, TemplateInfo]) -> str:
    """Convert templates dict to a prompt string for the LLM."""
    lines = []
    for index, (template_id, template_info) in enumerate(templates.items()):
        lib_str = ", ".join(template_info["lib"])
        port_str = str(template_info["port"]) if template_info["port"] else "none"
        file_str = template_info["file"] or "none"
        lines.append(
            f'{index + 1}. {template_id}: "{template_info["instructions"]}". '
            f"File: {file_str}. Dependencies installed: {lib_str}. Port: {port_str}."
        )
    return "\n".join(lines)


def to_prompt(templates: dict[str, TemplateInfo]) -> str:
    """Generate the system prompt for code generation."""
    return f"""
    You are a skilled software engineer.
    You do not make mistakes.
    Generate a fragment.
    You can install additional dependencies.
    Do not touch project dependencies files like package.json, package-lock.json, requirements.txt, etc.
    Do not wrap code in backticks.
    Always break the lines correctly.
    You can use one of the following templates:
    {templates_to_prompt(templates)}
    """

