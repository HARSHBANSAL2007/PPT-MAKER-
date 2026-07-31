# step 1 load modules 
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
import streamlit as st

#=========================== STEP 2 =============================
st.set_page_config(layout = "wide")
st.title("AI PPT GENERATOR")
st.divider()
st.sidebar.title("ENTER API-KEYS")

#========step 3 ====================

GOOGLE_API_KEY = st.sidebar.text_input("GOOGLE_API_KEY", type = "password")
TAVILY_API_KEY = st.sidebar.text_input("TAVILY_API_KEY", type = "password")


#============API VALIDATIONS ============
ALL_API = [GOOGLE_API_KEY,TAVILY_API_KEY]

if not all(ALL_API):
  st.sidebar.error("MUST PASS ALL API KEYS")
elif all(ALL_API):
  st.sidebar.success("API_KEY loaded")
  #MODEL LOAD 
  model = ChatGoogleGenerativeAI(
    google_api_key = GOOGLE_API_KEY,
    model = st.sidebar.selectbox("Gemini-Model-Name",
                                 options = ["gemini-2.5-flash",
                                            "gemini-2.5-flash-lite",
                                            "gemini-3.5-flash",
                                            "gemini-3.5-flash-lite"])
  )
else:
  st.sidebar.info("check api keys")

# search the latest info using tavily
def search_latest_info(query):
  """this function helps to give
  latest search info using tavily
  based on given user query related research
  or contents"""
  client = TavilyClient(TAVILY_API_KEY)
  response = client.search(query)
  return response

#==============step 6 user input ====================
st.header("write the prompt to generate ppt or image or fetch latest news")
user_input = st.text_area("write here: ")

def generate_image(img_prompt,slide_no = 1):
  """this function helps user generate
  image using free api key with given
  image_prompt"""
  url = f"https://image.pollinations.ai/{img_prompt}"

  import requests as r
  content = r.get(url).content
  with open(f"ai_image_{slide_no}.jpeg",'wb') as f:
    f.write(content)
  from PIL import Image
  img = Image.open(f"ai_image_{slide_no}.jpeg")
  return url

def agent_prompt(query):
  """this function helps promptify the given user
  query, suppose user needs ppt based on given qury by user it gives detailed professional prompt
  to return the output"""

  prompt = f"""give high professional prompt for below given prompt :-

  you are a professional ppt designer based on user given query, your task is to create
  professional html output prompt with no markdown
  user query :- {query}"""

  resonse = model.invoke(prompt)
  final_prompt = resonse.content[-1]['text']

  with open("PPT_PROMPT.txt", 'w') as f:
    f.write(final_prompt)
  return final_prompt

def run_agent(leader_agent, query):
  prompt = f"""Based on Below given Query, your task is to call specific tool,
  first to promptify user prompt, than call image tool, or latest search if
  required.give slide dynamic, ui ux, with creative design, keep help of
  function to generate image based on given topic, Generate image using
   with no of slide asked
  and imbed that in same html ppt and using file handling embed this in
  output html, use java script function to generate image using async
  func and threading and give output in HTML user query given below:"""
  prompt += query
  prompt = agent_prompt(prompt)
  response = leader_agent.invoke({'messages': [{'role': 'user', 'content': prompt}]})
  code = response['messages'] [-1].content[-1]['text']
  return code

#==================step 7 ========================
if all (ALL_API):
  leader_agent = create_agent(
      model = model,
      tools = [search_latest_info,
               #generate_image
               ])
else:
  st.error("must pass api key ")


#======================step no 8========================
tab1,tab2,tab3 = st.tabs(["Generate Image",
                          "Fetch latest news",
                          "Generate PPT"])

if (user_input) and (leader_agent):
  #tab 1 code 
  with tab1:
   if st.button("Generate image",key = "Gen-Image"):
     with st.spinner("Running agent"):
       try:
         img = generate_image(user_input)
         st.image(img)
       except:
          url = f"https://image.pollinations.ai/{user_input}"
          time.sleep(4)
          st.image(url)
  with tab2:
    if st.button("Fetch News", key = "Fetch-News"):
      with st.spinner("Running Agent"):
        try:
          prompt = "Give Multiple news in HTML card Format for topic" + user_input
          response = leader_agent.invoke({'messages':[{'role': 'user',
                                                      'content': prompt}]})
          code = response['messages'] [-1].content[-1]['text']
          st.html(code, width="stretch",
          unsafe_allow_javascript=True)
        except Exception as err:
          st.error(err)
  with tab3:
    if st.button("Generate PPT", key = "Gen-PPT"):
      with st.spinner("Running Agent"):
        try:
          code = run_agent(leader_agent, user_input)
          st.html(code, width="stretch",
          unsafe_allow_javascript=True)
          #file savce
          with open("ppt.html",'w') as f:
            f.write(code)
          st.download_button(label = "DOWNLOAD PPT",
                          data = code,
                          file_name = 'ppt.html',
                          mime = 'text/html')
        except Exception as err:
          st.error(err)
else:
  st.error("something went wrong")
                          
