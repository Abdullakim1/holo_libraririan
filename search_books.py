import pandas as pd
from langchain_ollama import ChatOllama
from langchain_core.tools import Tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate

# 1. LOAD DATA
df = pd.read_csv("library_data.csv")

# 2. DEFINE TOOLS (accept plain strings, no kwargs)
def search_library(query: str) -> str:
    """Search by title. Input: plain text like 'Great Gatsby'"""
    results = df[df["Title"].str.contains(query, case=False, na=False)]
    if results.empty:
        return "No books found."
    return results[["Title", "Author", "Status"]].to_string(index=False)

def check_out_book(title: str) -> str:
    """Check out by exact title. Input: plain text like 'The Great Gatsby'"""
    mask = df["Title"].str.lower() == title.lower()
    if not mask.any():
        return f"'{title}' not found."
    if df.loc[mask, "Status"].iloc[0] == "Out":
        return f"'{title}' is already checked out."
    df.loc[mask, "Status"] = "Out"
    df.to_csv("library_data.csv", index=False)
    return f"✅ '{title}' checked out."

tools = [
    Tool(
        name="SearchBooks",
        func=search_library,
        description="Search library by title. Input: plain text (e.g., 'Great Gatsby'). Returns title/author/status."
    ),
    Tool(
        name="CheckOut",
        func=check_out_book,
        description="Check out a book. Input: exact title (e.g., 'The Great Gatsby'). Updates CSV."
    )
]

# 3. STRICT REACT PROMPT (forces correct format)
REACT_TEMPLATE = """You are a library assistant. Use tools EXACTLY as shown below.

TOOLS:
{tools}

FORMAT RULES:
- Action must be ONE of: [{tool_names}]
- Action Input must be PLAIN TEXT, NO parentheses, NO quotes, NO equals signs
- Example CORRECT: Action: SearchBooks\nAction Input: Great Gatsby
- Example WRONG: SearchBooks(query='Great Gatsby') ← NEVER do this

CONVERSATION:
Question: {input}
Thought:{agent_scratchpad}"""

prompt = PromptTemplate.from_template(REACT_TEMPLATE)

# 4. LOCAL LLM (use llama3.1:8b for better tool-following)
llm = ChatOllama(model="llama3.2", temperature=0)

# 5. BUILD & RUN
agent = create_react_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

executor.invoke({"input": "Is 'The Great Gatsby' available? If yes, check it out for me."})
