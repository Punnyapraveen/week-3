import asyncio
import contextlib
import io
import os
from typing import Any, List

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import google.generativeai as genai

# ============================ #
# 🌐 CONFIGURE GEMINI
# ============================ #
genai.configure(api_key="your_api")  # Replace with your Gemini API key
gemini_model = genai.GenerativeModel("gemini-2.0-flash")  # or "gemini-2.0-pro"

# ============================ #
# 🛠️ TOOLS
# ============================ #

loaded_df = {}

def pandas_summary(csv_path: str) -> str:
    try:
        df = pd.read_csv(csv_path)
        loaded_df["data"] = df  # Save for visualization
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            print("📊 Summary:")
            print(df.describe(include='all'))
            print("\n🔢 Data Types:")
            print(df.dtypes)
            print("\n📐 Shape:", df.shape)
            print("\n🧱 Null Values:")
            print(df.isnull().sum())
        return buffer.getvalue()
    except Exception as e:
        return f"❌ Error reading CSV: {str(e)}"

def matplotlib_visualize(_: str) -> str:
    try:
        df = loaded_df.get("data")
        if df is None:
            return "⚠️ Data not loaded for visualization."

        numeric_cols = df.select_dtypes(include='number').columns
        if len(numeric_cols) < 2:
            return "⚠️ Need at least 2 numeric columns for visualization."

        plt.figure(figsize=(12, 8))

        # 1. Scatter plot
        plt.subplot(2, 2, 1)
        sns.scatterplot(data=df, x=numeric_cols[0], y=numeric_cols[1])
        plt.title(f'{numeric_cols[0]} vs {numeric_cols[1]}')

        # 2. Histogram for first numeric column
        plt.subplot(2, 2, 2)
        sns.histplot(df[numeric_cols[0]], kde=True)
        plt.title(f'Distribution of {numeric_cols[0]}')

        # 3. Histogram for second numeric column
        plt.subplot(2, 2, 3)
        sns.histplot(df[numeric_cols[1]], kde=True)
        plt.title(f'Distribution of {numeric_cols[1]}')

        # 4. Boxplot for all numeric columns
        plt.subplot(2, 2, 4)
        sns.boxplot(data=df[numeric_cols])
        plt.title('Boxplot of Numeric Columns')

        plt.tight_layout()
        os.makedirs("output", exist_ok=True)
        plot_path = os.path.join("output", "visualizations.png")
        plt.savefig(plot_path)
        plt.close()

        return f"🖼️ Visualizations saved to: {plot_path}"

    except Exception as e:
        return f"❌ Visualization failed: {str(e)}"

# ============================ #
# 🤖 AGENT WRAPPER
# ============================ #

class GeminiAgent:
    def __init__(self, name: str, tools: List[Any], system_prompt: str):
        self.name = name
        self.tools = tools
        self.system_prompt = system_prompt

    async def run(self, input_text: str, history: List[str]) -> str:
        tool_outputs = ""
        for tool_func in self.tools:
            try:
                result = tool_func(input_text)
                tool_outputs += f"\n🛠️ {tool_func.__name__} Output:\n{result}\n"
            except Exception as e:
                tool_outputs += f"\n❌ {tool_func.__name__} Failed: {str(e)}\n"

        prompt = (
            f"{self.system_prompt}\n"
            f"\n📝 Chat History:\n{chr(10).join(history)}"
            f"\n\n📥 Input:\n{input_text}"
            f"\n\n📤 Tool Results:\n{tool_outputs}"
        )

        response = gemini_model.generate_content(prompt)
        return response.text.strip()

# ============================ #
# 🔁 ROUND ROBIN GROUP CHAT
# ============================ #

class RoundRobinGroupChat:
    def __init__(self, agents: List[GeminiAgent], max_turns: int = 6):
        self.agents = agents
        self.max_turns = max_turns
        self.history = []

    async def chat(self, initial_input: str, output_file: str = "output/session_log.txt"):
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        query = initial_input
        with open(output_file, "w", encoding="utf-8") as f:
            for i in range(self.max_turns):
                agent = self.agents[i % len(self.agents)]
                f.write(f"\n🧠 [{agent.name}] is thinking...\n")
                print(f"\n🧠 [{agent.name}] is thinking...")

                response = await agent.run(query, self.history)
                self.history.append(f"[{agent.name}]: {response}")

                f.write(f"🗨️ [{agent.name}] says:\n{response}\n")
                print(f"🗨️ [{agent.name}] says:\n{response}\n")

                query = response

            print("✅ Analysis complete.")
            f.write("\n✅ Analysis complete.\n")

# ============================ #
# 🏁 MAIN
# ============================ #

async def main():
    data_fetcher = GeminiAgent(
        name="DataFetcher",
        tools=[pandas_summary],
        system_prompt="You are a data scientist. Load and summarize the dataset from the given path."
    )

    analyst = GeminiAgent(
        name="Analyst",
        tools=[matplotlib_visualize],
        system_prompt="You are a data analyst. Visualize the dataset and share insights."
    )

    chat = RoundRobinGroupChat(agents=[data_fetcher, analyst], max_turns=6)

    csv_path = input("📂 Enter the full path to your CSV file:\n>>> ").strip()
    await chat.chat(csv_path)

if __name__ == "__main__":
    asyncio.run(main())
