from langchain_core.runnables.config import set_config_context
import streamlit AS ST
import os
import time
import langchain
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
import pytesseract as pyt
from tavily import TavilyClient
from langchain.messages import SystemMessage , HumanMessage
import numpy as np
import streamlit as st
from langchain_community.document_loaders import PyMuPDFLoader
import requests as r
import time
from urllib.parse import quote
from PIL import Image
import base64
#PROJECT FLOW
# OBJECTIVE : PPT GENERATOR
# MODEL ==> LLM CALL : TOOL ==> SEARCH API'S , IMAGE API  :: SUB-AGENT ==> TO WORK ON SPECIFIC TASK ::MAIN AGENT ==> ORCHASTRATE  ALL AGENT :: CODE TEST ==> CHECK OUTPUT :: FRONT END ==> STREAMLIT :: LIVE DEPLOY ==>
#-> STREAMLIT FORNT END DEGSINE :) =======================
st.set_page_config(layout="wide")

st.title("AI PPT GENERATOR")
st.divider()
st.sidebar.title("Enter API-KEYS")

#-> api key loader 
google= st.sidebar.text_input("GEMINI",type="password")
GROQ= st.sidebar.text_input("GROQ",type="password")
TAVILY =st.sidebar.text_input("TAVILY",type="password")

#============conditional model creation ===============================
# =========API VALIDATIONS===========
ALL_API = [google,TAVILY]

if not all(ALL_API):
    st.sidebar.error("MUST PASS ALL API-KEYS")

elif all(ALL_API):
    st.sidebar.success("API-KEYS LOADED SUCCESSFULLY")
    # MODEL LOAD
    model = ChatGoogleGenerativeAI(
        google_api_key = google,
        model = st.sidebar.selectbox(
            "Gemini-Model-Name",
            options = [
                "gemini-2.5-flash",
                "gemini-2.5-flash-lite",
                "gemini-3.5-flash",
                "gemini-3.5-flash-lite"
            ]
        )
    )

else:
    st.sidebar.info("CHECK-API-KEYS")

#==== TOOL1 : NEWS SEARCHER / INFO GATHERER=========
def search(query):
  """this function helps to give latest search query based on user given rescearch related or content  """

  tavily_client = TavilyClient(api_key="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")
  return tavily_client.search(query)


#===================USER INPUT================================
st.header("write prompt to generate ppt or image or fetch latest news ")
user=st.text_area("write HERE: ")
# ================CREATING TOOL 2: IMAGE GENERATION ==============================================
def generate_image(img_prompt, slide_no=1):
  """This function helps user to generate image using free api, with given img_prompt"""

  encoded_prompt = quote(img_prompt)
  url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"

  # Increased timeout to 60 seconds
  for attempt in range(3):
    response = r.get(url, timeout=60)
    if response.status_code == 200 and response.headers.get("content-type", "").startswith("image"):
      break
    time.sleep(2)
  else:
    return None

  # Save the image to a file temporarily
  filename = f"ai_image_{slide_no}.jpeg"
  with open(filename, 'wb') as f:
    f.write(response.content)

  try:
    # Verify image and then encode it to base64
    img = Image.open(filename)
    img.verify()

    # Read the image content and encode to base64
    with open(filename, 'rb') as img_file:
      encoded_string = base64.b64encode(img_file.read()).decode('utf-8')

    # Determine content type (assuming JPEG for now, could be made dynamic)
    content_type = response.headers.get("content-type", "image/jpeg")

    # Return data URI
    return f"data:{content_type};base64,{encoded_string}"
  except Exception:
    return None

#================== PROMPT GENERATOR ========================
def agent_prompt(query):
  """This function helps to promptify the given user query into a detailed textual outline for a presentation."""

  prompt = f"""Generate a detailed, professional outline for a presentation based on the user's query.  The outline should include a suggested title for each slide, key points, and ideas for images,specifying the number of slides requested in the original query. Do NOT generate HTML. Just provide the textual outline.  User Query: {query}"""

  response = model.invoke(prompt)
  presentation_outline = response.content[-1]['text']

  with open("PPT_OUTLINE.txt",'w') as f:
    f.write(presentation_outline)
  return presentation_outline


#=============PPT PROMPT MAKER : ===================
def run_agent(leader_agent, user_query):
    # Get a detailed textual outline from agent_prompt
    # This outline will guide the leader_agent on how many slides and what content for each.
    presentation_outline = agent_prompt(user_query)  # Now `agent_prompt` returns a text outline

    # Construct a clear prompt for the leader_agent to generate HTML slides
    # It needs to understand how to parse the outline and use tools iteratively.
    prompt_for_leader_agent = f"""
    You are an AI assistant tasked with creating a multi-slide presentation in HTML format.
    Below is an outline for the presentation, generated from the user's request.
    Your goal is to convert this outline into a series of visually appealing HTML slides.

    Instructions:
    1. Parse the provided presentation outline to understand the structure and content for each slide, including the requested number of slides.
    2. For each slide in the outline:
       a. **Generate an image**: Use the `generate_image` tool with a descriptive prompt based on the slide's content. Use the link of Polinations AI site to make the images.
       b. **Gather information**: If necessary, use the `search` tool to get additional factual details or context for the slide's text.
       c. **Create HTML for the slide**: Design a clean, professional HTML div for the slide, incorporating the generated image and textual content. Ensure the HTML is well-structured and styled.
    3. Combine all individual slide HTML divs into a single HTML document. Make sure each slide is clearly separated and presentable (e.g., using distinct divs or sections).
    4. The final output must be a single, complete HTML string representing the entire multi-slide presentation.
    5. Also make sure that the number of slides are the same as given in slide_no in the prompt (be it 5 or 10). Each slide should have one proper image in a placeholder AND each slide should have a presentable image.

    Presentation Outline:

    Users Original Request: {user_query}
    give output in HTML
    User query given below: {presentation_outline}"""

    # Append the outline again to reinforce context
    prompt_for_leader_agent += presentation_outline

    # Send the constructed prompt to the leader_agent
    response = leader_agent.invoke({
        'messages': [
            {'role': 'user', 'content': prompt_for_leader_agent}
        ]
    })

    # The agent should now return the complete HTML for all slides
    code = response['messages'][-1].content[-1]['text']
    return code


#========================AGENT CALLING =====================================================================

# leader_agent creation
leader_agent = create_agent(
    model = model,
    tools=[search,generate_image])

