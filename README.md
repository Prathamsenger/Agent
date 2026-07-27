# 🏙️ City Agent

## About This Project

City Agent is an AI-powered assistant that answers natural-language questions about any city — starting with its current **weather** and its **latest news**. Instead of hardcoding logic for each request, the agent uses a large language model (Mistral) to understand what the user is asking, decide which tool to call (a weather API or a news search), and then reply in plain language.

What makes this project interesting is the **human-in-the-loop safety layer**: before the agent is allowed to actually call a tool (hit an external API), it pauses and asks a human for approval. Nothing runs silently in the background — every external action is transparent and requires a "yes" before it executes. This pattern is useful for any AI agent that takes real actions (API calls, sending messages, executing code, etc.) where you want a human checkpoint before something happens.

The project ships with **two interfaces built on the exact same agent logic**:
- **CLI** (`agent.py`) — a terminal chat loop where approvals are given by typing `yes`/`no`.
- **Streamlit UI** (`streamlit_app.py`) — a browser-based chat app where approvals are given by clicking Approve/Deny buttons, with the agent running in a background thread so the UI stays responsive while waiting.

This makes the project a good reference example for building LangChain agents with tool use, human approval middleware, and multiple front-ends (CLI + web) on top of one shared core.

## Features

- 🌦️ Get current weather for any city (OpenWeather API)
- 📰 Get latest news for any city (Tavily Search API)
- ✅ Human-in-the-loop approval before any tool executes
- 💬 Simple chat interface (CLI or Streamlit)

## Prerequisites

- Python 3.10+
- API keys for:
  - [Mistral AI](https://console.mistral.ai/)
  - [OpenWeatherMap](https://openweathermap.org/api)
  - [Tavily](https://tavily.com/)

## Installation

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
python -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```env
MISTRAL_API_KEY=your_mistral_api_key
OPENWEATHER_API_KEY=your_openweather_api_key
TAVILY_API_KEY=your_tavily_api_key
```

> ⚠️ Never commit your `.env` file. It's already excluded via `.gitignore`.

## Usage

### CLI version

```bash
python agent.py
```

Type your question (e.g. `weather in Ludhiana`), approve or deny tool calls when prompted, and type `exit` to quit.

### Streamlit version

```bash
streamlit run streamlit_app.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`) and chat in the browser. Approve or deny tool calls using the on-screen buttons.

## Project Structure

```
.
├── agent.py             # CLI version of the agent
├── streamlit_app.py      # Streamlit UI version of the agent
├── requirements.txt      # Python dependencies
├── .env                  # API keys (not committed)
├── .gitignore
└── README.md
```

## Tech Stack

- `langchain` / `langchain-mistralai` — agent framework + LLM
- `tavily-python` — news/web search
- `requests` — weather API calls
- `streamlit` — web UI
- `python-dotenv` — environment variable management

## License

MIT
