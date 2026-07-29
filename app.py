"""LLM Research Tool web application.

This Flask app accepts two topics, queries a configured LLM to summarise
and compare them, and returns the results via simple templates.

Environment variables used:
- OPENAI_API_KEY_AC: API key for the LLM
- APP_PASSWORD: simple access password for the form
- OPENAI_API_BASE, MODEL_NAME, LLM_TIMEOUT, LLM_MAX_RETRIES, PORT
"""

import os
import logging
import textwrap
import time
from flask import Flask, render_template, request, redirect
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# Basic config
API_KEY = os.getenv("OPENAI_API_KEY_AC")
ACCESS_PASSWORD = os.getenv("APP_PASSWORD")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://llmaas.govtext.gov.sg/gateway")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "25"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "2"))
PORT = int(os.getenv("PORT", "5000"))
HOST = os.getenv("HOST", "0.0.0.0")

app = Flask(__name__)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------
# LLM Setup (lazy singleton using function attribute)
# ---------------------------

def get_llm():
    """Return a cached ChatOpenAI client, creating it on first use."""
    if not hasattr(get_llm, "client"):
        logger.info("Initializing LLM client")
        get_llm.client = ChatOpenAI(
            api_key=API_KEY,
            openai_api_base=OPENAI_API_BASE,
            model=MODEL_NAME,
            timeout=LLM_TIMEOUT,
            max_retries=LLM_MAX_RETRIES,
        )
    return get_llm.client


def _clean_prompt(text: str):
    """Normalize indentation/whitespace for multi-line prompts."""
    return textwrap.dedent(text).strip()


# pylint: disable=broad-exception-caught
def ask_agent(chat, system_role: str, prompt: str):
    """Invoke the LLM and return a cleaned text response. Logs on exception."""
    try:
        sys_msg = SystemMessage(content=_clean_prompt(system_role))
        human_msg = HumanMessage(content=_clean_prompt(prompt))
        response = chat.invoke([sys_msg, human_msg])
        return (response.content or "").strip()
    except Exception as exc:
        logger.exception("LLM invocation failed: %s", exc)
        return ""


# ---------------------------
# Routes
# ---------------------------
@app.route("/", methods=["GET"])
def index():
    """Render the input form page."""
    return render_template("input.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    """Handle form submission: query LLMs and render results."""
    userinput1 = request.form.get("input1", "").strip()
    userinput2 = request.form.get("input2", "").strip()
    password = request.form.get("password", "")

    if password != ACCESS_PASSWORD:
        logger.warning("Unauthorized access attempt")
        return redirect("/")

    if not API_KEY:
        logger.error("Missing API key")
        return "Missing API Key", 500

    chat = get_llm()

    # Agent 1: Summariser A
    botoutput1 = ""
    if userinput1:
        botoutput1 = ask_agent(
            chat,
            "You summarise content concisely.",
            f"Summarise the following in max 200 words:\n{userinput1}",
        )

    time.sleep(5)

    # Agent 2: Summariser B
    botoutput2 = ""
    if userinput2:
        botoutput2 = ask_agent(
            chat,
            "You summarise content concisely.",
            f"Summarise the following in max 200 words:\n{userinput2}",
        )

    time.sleep(8)

# Agent 3: Comparator
    botoutput3 = ""
    if botoutput1 and botoutput2:
        botoutput3 = ask_agent(
            chat,
            "You compare two pieces of information analytically.",
            f"""
            Compare the following two summaries.

            Summary A:
            {botoutput1}

            Summary B:
            {botoutput2}

            Provide similarities and differences in the research summaries. Based on the two summaries, provide a list of potential research topics that could be explored further. For each topic, include some Research articles and websites on each topic.
            """,
        )

    return render_template(
        "output.html",
        displayoutput1=botoutput1,
        displayoutput2=botoutput2,
        displayoutput3=botoutput3,
    )


# ---------------------------
# Run App
# ---------------------------
if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)
