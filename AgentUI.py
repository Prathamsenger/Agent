
import os
import queue
import threading
import time

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from langchain_mistralai import ChatMistralAI
from langchain.tools import tool
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda
from tavily import TavilyClient
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call

# =========================
# 🌦️ Weather Tool
# =========================


@tool
def get_weather(city: str) -> str:
    """Get current weather of a city"""

    api_key = os.getenv("OPENWEATHER_API_KEY")
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city},IN&appid={api_key}&units=metric"

    response = requests.get(url)
    data = response.json()

    if str(data.get("cod")) != "200":
        return f"Error: {data.get('message', 'Could not fetch weather')}"

    temp = data["main"]["temp"]
    desc = data["weather"][0]["description"]

    return f"Weather in {city}: {desc}, {temp}°C"


# =========================
# 📰 News Tool (Tavily)
# =========================

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


@tool
def get_news(city: str) -> str:
    """Get latest news about a city"""

    response = tavily_client.search(
        query=f"latest news in {city}",
        search_depth="basic",
        max_results=3,
    )

    results = response.get("results", [])

    if not results:
        return f"No news found for {city}"

    news_list = []

    for r in results:
        title = r.get("title", "No title")
        url = r.get("url", "")
        snippet = r.get("content", "")

        news_list.append(f"- {title}\n  🔗 {url}\n  📝 {snippet[:100]}...")

    return f"Latest news in {city}:\n\n" + "\n\n".join(news_list)


# =========================
# 🧠 LLM Setup
# =========================

llm = ChatMistralAI(model="mistral-small-2506")

# Queues used to turn the blocking input() approval into UI buttons.
# The background agent thread PUTs an approval request and BLOCKS on
# response_queue.get() -- exactly like input() blocks -- until the
# Streamlit main thread PUTs back "yes"/"no" after a button click.
approval_request_queue: "queue.Queue" = queue.Queue()
approval_response_queue: "queue.Queue" = queue.Queue()


@wrap_tool_call
def human_approval(request, handler):
    """Ask for human approval before every tool call."""
    tool_name = request.tool_call["name"]

    approval_request_queue.put(tool_name)
    confirm = approval_response_queue.get()  # blocks, same role as input()

    if confirm.lower() != "yes":
        return ToolMessage(
            content="Tool call denied by user.",
            tool_call_id=request.tool_call["id"],
        )

    return handler(request)


agent = create_agent(
    llm,
    tools=[get_weather, get_news],
    system_prompt="you are a helpful city assistant.",
    middleware=[human_approval],
)

agent_runnable = RunnableLambda(lambda x: agent.invoke(x))


# =========================
# 🖥️ Streamlit UI
# =========================

st.set_page_config(page_title="City Agent", page_icon="🏙️")
st.title("🏙️ City Agent")
st.caption("Ask about a city's weather or news. Tool calls need your approval.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # list of {"role": ..., "content": ...}
if "agent_thread" not in st.session_state:
    st.session_state.agent_thread = None
if "thread_result" not in st.session_state:
    st.session_state.thread_result = {}
if "pending_tool" not in st.session_state:
    st.session_state.pending_tool = None

# Render existing chat history
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


def run_agent_in_thread(user_input: str, result_holder: dict):
    try:
        result = agent_runnable.invoke({"messages": [{"role": "user", "content": user_input}]})
        result_holder["output"] = result["messages"][-1].content
    except Exception as e:
        result_holder["error"] = str(e)
    finally:
        result_holder["done"] = True


user_input = st.chat_input("Ask about a city...")

if user_input and st.session_state.agent_thread is None:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    st.session_state.thread_result = {"done": False}
    t = threading.Thread(
        target=run_agent_in_thread,
        args=(user_input, st.session_state.thread_result),
        daemon=True,
    )
    st.session_state.agent_thread = t
    t.start()
    st.rerun()

# While the agent thread is alive, poll for an approval request or completion
if st.session_state.agent_thread is not None:
    # Check if the agent is asking for approval
    if st.session_state.pending_tool is None:
        try:
            st.session_state.pending_tool = approval_request_queue.get_nowait()
        except queue.Empty:
            pass

    if st.session_state.pending_tool is not None:
        with st.chat_message("assistant"):
            st.warning(f"Agent wants to call **'{st.session_state.pending_tool}'**. Approve?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Approve", use_container_width=True):
                    approval_response_queue.put("yes")
                    st.session_state.pending_tool = None
                    st.rerun()
            with col2:
                if st.button("❌ Deny", use_container_width=True):
                    approval_response_queue.put("no")
                    st.session_state.pending_tool = None
                    st.rerun()

    elif st.session_state.thread_result.get("done"):
        result = st.session_state.thread_result
        if "error" in result:
            reply = f"⚠️ Error: {result['error']}"
        else:
            reply = result.get("output", "")

        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        st.session_state.agent_thread = None
        st.session_state.thread_result = {}
        st.rerun()

    else:
        with st.chat_message("assistant"):
            st.markdown("_thinking..._")
        time.sleep(0.4)
        st.rerun()