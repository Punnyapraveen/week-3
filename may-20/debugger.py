import asyncio
import contextlib
import io
import tempfile
import os
import subprocess
from typing import Any, List

import google.generativeai as genai

# ============================ #
# 🌐 CONFIGURE GEMINI
# ============================ #

genai.configure(api_key="your_api")  # Replace with your actual API key
gemini_model = genai.GenerativeModel("gemini-2.0-flash")

# ============================ #
# 🛠️ TOOLS
# ============================ #

def python_executor(code: str) -> str:
    """Executes Python code and returns the output or error."""
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exec(code, {})
        return f"✅ Output:\n{stdout.getvalue()}"
    except Exception as e:
        return f"❌ Error:\n{stderr.getvalue()}\nException: {str(e)}"

def pylint_linter(code: str) -> str:
    """Runs pylint on the given code and returns the results."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        tmp_path = f.name
    try:
        result = subprocess.run(
            ["pylint", tmp_path, "--disable=all", "--enable=errors,warnings"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return f"🧹 Lint Report:\n{result.stdout.strip() or 'No issues found.'}"
    finally:
        os.remove(tmp_path)

# ============================ #
# 🤖 AGENTS
# ============================ #

class GeminiAgent:
    def __init__(self, name: str, tools: List[Any], system_prompt: str):
        self.name = name
        self.tools = tools
        self.system_prompt = system_prompt

    async def run(self, input_code: str, history: List[str]) -> str:
        tool_outputs = ""
        for tool_func in self.tools:
            tool_name = getattr(tool_func, '__name__', tool_func.__class__.__name__)
            try:
                result = tool_func(input_code)
                tool_outputs += f"\nTool ({tool_name}):\n{result}"
            except Exception as e:
                tool_outputs += f"\nTool ({tool_name}) failed: {str(e)}"

        prompt = (
            f"{self.system_prompt}\n\n"
            f"Chat History:\n" + "\n".join(history) +
            f"\n\nLatest Code:\n{input_code}" +
            f"\n\nTool Feedback:\n{tool_outputs}\n\n"
            f"Please provide the next version of the code."
        )

        response = gemini_model.generate_content(prompt)
        return response.text.strip()

# ============================ #
# 🔁 GROUPCHAT
# ============================ #

class RoundRobinGroupChat:
    def __init__(self, agents: List[GeminiAgent], max_turns: int = 10):
        self.agents = agents
        self.max_turns = max_turns
        self.history = []

    async def chat(self, initial_code: str, output_file: str = "debugging_session.txt"):
        code = initial_code
        with open(output_file, "w", encoding="utf-8") as f:
            for i in range(self.max_turns):
                agent = self.agents[i % len(self.agents)]
                thinking = f"\n🧠 [{agent.name}] is thinking...\n"
                print(thinking)
                f.write(thinking)

                response = await agent.run(code, self.history)

                reply = f"🗨️ [{agent.name}] says:\n{response}\n"
                print(reply)
                f.write(reply)

                self.history.append(f"[{agent.name}]:\n{response}")
                code = response

            end_msg = "💬 Chat ended after max turns.\n"
            print(end_msg)
            f.write(end_msg)

# ============================ #
# 🏁 MAIN
# ============================ #

async def main():
    coder = GeminiAgent(
        name="Coder",
        tools=[],
        system_prompt="You are a helpful Python code generator. Refactor or write clean, working Python code."
    )

    debugger = GeminiAgent(
        name="Debugger",
        tools=[python_executor, pylint_linter],
        system_prompt="You are a code debugger. Analyze the code using tools and suggest a fixed version."
    )

    chat = RoundRobinGroupChat(agents=[coder, debugger], max_turns=6)

    # 🐞 Accept user input
    print("Enter your Python code below (end with an empty line):")
    lines = []
    while True:
        line = input()
        if line.strip() == "":
            break
        lines.append(line)
    initial_code = "\n".join(lines)

    await chat.chat(initial_code, output_file="debugging_session.txt")


if __name__ == "__main__":
    asyncio.run(main())
