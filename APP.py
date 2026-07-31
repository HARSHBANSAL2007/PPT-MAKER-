from langchain_core.runnables.config import set_config_context
import streamlit as st
import os
import time
import langchain
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
import pytesseract as pyt
from tavily import TavilyClient
from langchain.messages import SystemMessage, HumanMessage
import numpy as np
from langchain_community.document_loaders import PyMuPDFLoader
import requests as r
from urllib.parse import quote
from PIL import Image
import base64
model=None
# PROJECT FLOW
# OBJECTIVE : PPT GENERATOR
# MODEL ==> LLM CALL : TOOL ==> SEARCH API'S , IMAGE API
# SUB-AGENT ==> TO WORK ON SPECIFIC TASK
# MAIN AGENT ==> ORCHESTRATE ALL AGENTS
# CODE TEST ==> CHECK OUTPUT
# FRONT END ==> STREAMLIT
# LIVE DEPLOY ==> STREAMLIT FRONT END DESIGN

st.set_page_config(layout="wide")

st.title("AI PPT GENERATOR")
st.divider()
st.sidebar.title("Enter API-KEYS")

# API key loader
google = st.sidebar.text_input("GEMINI", type="password")
GROQ = st.sidebar.text_input("GROQ", type="password")
TAVILY = st.sidebar.text_input("TAVILY", type="password")

# API VALIDATIONS
ALL_API = [google, TAVILY]

if not all(ALL_API):
    st.sidebar.error("MUST PASS ALL API-KEYS")

elif all(ALL_API):
    st.sidebar.success("API-KEYS LOADED SUCCESSFULLY")
    # MODEL LOAD
    model = ChatGoogleGenerativeAI(
        google_api_key=google,
        model=st.sidebar.selectbox(
            "Gemini-Model-Name",
            options=[
                "gemini-2.5-flash",
                "gemini-2.5-flash-lite",
                "gemini-3.5-flash",
                "gemini-3.5-flash-lite"
            ]
        )
    )
else:
    st.sidebar.info("CHECK-API-KEYS")


# TOOL1 : NEWS SEARCHER / INFO GATHERER
def search(query):
    """This function helps to give latest search query based on user given research related or content"""
    tavily_client = TavilyClient(api_key="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")
    return tavily_client.search(query)


# USER INPUT
st.header("Write prompt to generate ppt or image or fetch latest news")
user = st.text_area("Write HERE: ")


# TOOL2 : IMAGE GENERATION
def generate_image(img_prompt, slide_no = 1):
  """This function helps user to generate image
  using free api, with given img_prompt, with slide no"""

  url = f"https://image.pollinations.ai/{img_prompt}"

  import requests as r
  content = r.get(url).content
  with open(f"ai_image_{slide_no}.jpeg", 'wb') as f:
    f.write(content)

  from PIL import Image
  img = Image.open(f"ai_image_{slide_no}.jpeg")
  return url


# PROMPT GENERATOR
def agent_prompt(query):
    """This function helps to promptify the given user query into a detailed textual outline for a presentation."""
    prompt = f"""Generate a detailed, professional outline for a presentation based on the user's query.
    The outline should include a suggested title for each slide, key points, and ideas for images,
    specifying the number of slides requested in the original query.
    Do NOT generate HTML. Just provide the textual outline.
    User Query: {query}"""

    response = model.invoke(prompt)
    presentation_outline = response.content[-1]['text']

    with open("PPT_OUTLINE.txt", 'w') as f:
        f.write(presentation_outline)
    return presentation_outline


# PPT PROMPT MAKER
def run_agent(leader_agent, user_query):
    presentation_outline = agent_prompt(user_query)

    prompt_for_leader_agent = f"""
    You are an AI assistant tasked with creating a multi-slide presentation in HTML format.
    Below is an outline for the presentation, generated from the user's request.
    Your goal is to convert this outline into a series of visually appealing HTML slides.

    Instructions:
    1. Parse the provided presentation outline to understand the structure and content for each slide.
    2. For each slide:
       a. Generate an image using Polinations AI.
       b. Gather information using search tool if needed.
       c. Create HTML for the slide with image + text.
    3. Combine all slides into one HTML document.
    4. Ensure number of slides matches slide_no.
    5. Each slide must have a proper image.

    Presentation Outline:

    User's Original Request: {user_query}
    give output in HTML
    User query given below: {presentation_outline}"""

    prompt_for_leader_agent += presentation_outline

    response = leader_agent.invoke({
        'messages': [{'role': 'user', 'content': prompt_for_leader_agent}]
    })

    code = response['messages'][-1].content[-1]['text']
    return code


# AGENT CREATIONleader_agent = create_agent(model=model, tools=[search, generate_image])
if all(ALL_API):
    leader_agent = create_agent(model=model, tools=[search, generate_image])
else:
    st.error("Model not initialized. Please enter API keys.")

tab1, tab2, tab3 = st.tabs(["GENERATE IMAGES", "FETCH NEWS", "GENERATE PPT"])

if user:
    # TAB 1
    with tab1:
        if st.button('GENERATE IMAGES', key='gen-image'):
            with st.spinner("Running agent"):
                try:
                    generate_image(user)
                except:
                    url = f"https://image.pollinations.ai/prompt/{user}"
                    time.sleep(4)
                    st.image(url)

    # TAB 2
    with tab2:
        if st.button("FETCH NEWS", key="fetch-news"):
            with st.spinner("Running agent"):
                try:
                    prompt_for_leader_agent = "Give the news in HTML card format for topic " + user
                    response = leader_agent.invoke({
                        'messages': [{'role': 'user', 'content': prompt_for_leader_agent}]
                    })
                    code = response['messages'][-1].content[-1]['text']
                    st.html(code, width="stretch", unsafe_allow_javascript=True)
                except Exception as er:
                    st.error(er)

    # TAB 3
    with tab3:
        if st.button("Generate PPT", key="Gen-PPT"):
            with st.spinner("Running Agent"):
                try:
                    code = run_agent(leader_agent, user)
                    st.html(code, width="stretch", unsafe_allow_javascript=True)

                    with open("ppt.html", "w") as f:
                        f.write(code)

                    st.download_button(
                        label="DOWNLOAD PPT",
                        data=code,
                        file_name="ppt.html",
                        mime="text/html"
                    )
                except Exception as err:
                    st.error(err)
        else:
            st.error("SOMETHING WENT WRONG!!")
