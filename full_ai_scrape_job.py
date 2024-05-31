# To use this script: python full_ai_scrape_job.py 

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from crewai_tools import PDFSearchTool, CSVSearchTool, WebsiteSearchTool

import os, getpass
from dotenv import load_dotenv
# load the .env file
load_dotenv()

def _set_if_undefined(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"Please provide your {var}")

#ensure .env file is correct
_set_if_undefined("OPENAI_API_KEY")
_set_if_undefined("LANGCHAIN_API_KEY")

# fill out langsmith stuff
os.environ['LANGCHAIN_TRACING_V2'] = 'true'
os.environ['LANGCHAIN_ENDPOINT'] = 'https://api.smith.langchain.com'
os.environ["LANGCHAIN_PROJECT"] = "CrewAI - PDF Scrape Job"

# Ensure directory where files will be saved
data_directory = "test_data"
os.makedirs(data_directory, exist_ok=True)

#we want very low temperature
temperature = 0.1

# gpt-4-turbo - latest, most expensive
open_ai_llm = ChatOpenAI(model_name="gpt-4-turbo", temperature=temperature)

# local LLM
local_llm = ChatOpenAI(
    openai_api_base="http://192.168.1.158:11434/v1",
    openai_api_key="ollama",
    model_name="llama3",
    temperature=temperature
)

use_local_llm = False # change when required

if use_local_llm:
    llm = local_llm
else:
    llm = open_ai_llm


print('Initiated.')
    
# Initialize the tools
pdf_read_tool = PDFSearchTool()
csv_read_tool = CSVSearchTool(csv='test_data/EB_Book_Target_Geographies_Target_AUM_band.csv', delimiter=',')
website_read_tool = WebsiteSearchTool()

# Define the agent with the tools
analyst = Agent(
    role='Financial Analyst',
    goal=f"""To provide detail-oriented document analysis.
    """,
    backstory=f"A highly experienced analyst with a keen eye for details in documents and has a strong ability to follow business logic.",
    verbose=True,
    allow_delegation=False,
    tools=[pdf_read_tool, csv_read_tool, website_read_tool],
    llm=llm
)

# Define the task
analysis_task = Task(
    description=f"""
    For each row in the EB_Book_Target_Geographies_Target_AUM_band.csv find the Tax form 5500 PDF file url in the "Link" column and then download it.
    
    If the Tax form says "5500-SF", then it is a short form. Otherwise it is a long form.
    If it is a long form, return any and all of the content(s) of Schedule C Part 1b of the tax form.
    Retrieve the text found in the Part 1b form section(s) of the Tax form. 
    Return N/A if no text was found in the tax form fields.
    Repeat this process for each row in the EB_Book_Target_Geographies_Target_AUM_band.csv.
    
    Write an output CSV containing the results of each row in the EB_Book_Target_Geographies_Target_AUM_band.csv. 
    If there are any errors for a given row, return "Error" for everything field in that row and move on to the next row.
    """,
    expected_output=f"""
    Generate an output CSV where each row contains the following columns.
    1. Account ID
    2. Account Name
    3. Link
    4. Short or Long Tax Form 5500
    5. If Schedule C Part 1a is checked "Yes"
    6. Relavent content found
    
    The number of rows in the output csv should match the number of rows in the EB_Book_Target_Geographies_Target_AUM_band.csv
    """,
    agent=analyst,
    output_file="recordkeeper.csv",
)

# Instantiate the crew
document_crew = Crew(
    agents=[analyst],
    tasks=[analysis_task],
    process=Process.sequential,  # Tasks will be executed one after the other,
    memory=True,
    verbose=True
)
# Begin the task execution
result = document_crew.kickoff()
print(result)
    