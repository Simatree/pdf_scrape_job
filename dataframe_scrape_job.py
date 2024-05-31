# To use this script: python dataframe_scrape_job.py 

from io import StringIO
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from crewai_tools import PDFSearchTool, WebsiteSearchTool

import os, getpass
import pandas as pd
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
os.environ["LANGCHAIN_PROJECT"] = "CrewAI - Dataframe - PDF Scrape Job"

# Ensure directory where files will be saved
data_directory = "test_data"
os.makedirs(data_directory, exist_ok=True)

results_csv_file_path = "test_data/recordkeeper_all.csv"

#we want very low temperature
temperature = 0.2

# gpt-4-turbo - latest, most expensive
open_ai_llm = ChatOpenAI(model_name="gpt-4-turbo", temperature=temperature)

# local LLM
local_llm = ChatOpenAI(
    openai_api_base="http://192.168.1.158:11434/v1",
    openai_api_key="ollama",
    model_name="llama3",
    temperature=temperature
)

use_local_llm = True # change when required

if use_local_llm:
    llm = local_llm
else:
    llm = open_ai_llm
    
# Initialize the tools
pdf_read_tool = PDFSearchTool()
website_read_tool = WebsiteSearchTool()

# Define the agent with the tools
analyst = Agent(
    role='Financial Analyst',
    goal=f"""To provide detail-oriented document analysis.
    """,
    backstory=f"A highly experienced analyst with a keen eye for details in documents and has a strong ability to follow business logic.",
    verbose=True,
    allow_delegation=False,
    tools=[pdf_read_tool, website_read_tool],
    llm=llm
)

def append_row_to_csv(csv_row_string):
    print(f"Appending row to CSV: {csv_row_string} ")
    # Convert the string to a DataFrame
    row_df = pd.read_csv(StringIO(csv_row_string))
    
    # Load the existing CSV file into a DataFrame
    try:
        existing_df = pd.read_csv(results_csv_file_path)
    except FileNotFoundError:
        print('File did not exist.')
        # If the file does not exist, create a new one
        column_names = ['Account ID', 'Link', 'Is Long Form', 'Schedule C Part 1a Checked', 'Schedule C Part 1b Content ']
        empty_df = pd.DataFrame(columns=column_names)
        updated_df = pd.concat([empty_df, row_df], ignore_index=True)
        updated_df.to_csv(results_csv_file_path, index=False)
        return
    
    # Append the new row to the existing DataFrame
    updated_df = pd.concat([existing_df, row_df], ignore_index=True)
    
    # Save the updated DataFrame back to the CSV file
    updated_df.to_csv(results_csv_file_path, index=False)

# Assuming parseRecordKeeperFromLink is defined elsewhere
def parseRecordKeeperFromLink(account_id, link):
    # Example implementation
    print(f"Parsing link for Account ID {account_id}: {link}")

    # Define the task
    analysis_task = Task(
        description=f"""
        Given the Tax form 5500 PDF file url ({link}).
        
        Download the PDF. Perform the following analysis.
        1. If the Tax form says "5500-SF", then it is a short form. Otherwise it is a long form. Remember if it is a long or a short form.
        2. If it is a long form, return any and all of the content(s) of Schedule C Part 1b form section(s) of the tax form. Otherwise, return N/A.
        3. If Schedule C Part 1a is checked "Yes". 
        
        Return a single commas seperated string of all the relevant content found in the PDF.
        If there are any errors for a given row, return "Error" for everything field in that row and move on to the next row.
        
        Examples:
        3240992,https://efast2-filings-public.s3.amazonaws.com/prd/2022/10/07/20221007050946NAL0016187601001.pdf,Long,Yes,ALLIANZ GLOBAL INVESTORS DISTRIBUTO 1345 AVENUE OF THE AMERICAS NEW YORK, NY 10105 ALPS DISTRIBUTORS, INC P.O. BOX 328 DENVER, CO 80202 AMERICAN FUNDS DISTRIBUTORS, INC. 95-2769620 FRANKLIN TEMPLETON DISTRIBUTORS, I 100 FOUNTAIN PARKWAY ST. PETERSBURG, FL 33716 INVESCO 1555 PEACHTREE STREET NW 1800 ATLANTA, GA 30309 METROPOLITAN WEST FUNDS 865 SOUTH FIGUEROA STREET LOS ANGELES, CA 90017 MFS FUND DISTRIBUTORS, INC. 04-2747644 PRUDENTIAL INVESTMENTS LLC 22-3468527 T. ROWE PRICE 100 EAST PRATT STREET BALTIMORE, MD 21202 VANGUARD 455 DEVON PARK DRIVE WAYNE, PA 19087
        3259865,https://efast2-filings-public.s3.amazonaws.com/prd/2022/10/14/20221014155008NAL0027803457001.pdf,Long,Yes,VOYA RETIREMENT INSURANCE 71-0294708
        4264765,https://efast2-filings-public.s3.amazonaws.com/prd/2022/09/22/20220922095457NAL0003236864001.pdf,Long,Yes,FIDELITY INVESTMENTS INSTITUTIONAL 04-2647786
        4327306,https://efast2-filings-public.s3.amazonaws.com/prd/2022/10/14/20221014215057NAL0032008288001.pdf,Long,Yes,FIDELITY INVESTMENTS INSTITUTIONAL 04-2647786
        3259617,https://efast2-filings-public.s3.amazonaws.com/prd/2022/09/09/20220909101329NAL0047988066001.pdf,Short,N/A,N/A
        """,
        expected_output=f"""
        Return a single CSV row containing the following columns.
        1. Account ID
        2. Link
        3. If it is a Long or Short form
        4. If Schedule C Part 1a is checked "Yes"
        5. Schedule C Part 1b form section(s) content found.
        
        Return nothing else.
        Examples:
        3240992,https://efast2-filings-public.s3.amazonaws.com/prd/2022/10/07/20221007050946NAL0016187601001.pdf,Long,Yes,ALLIANZ GLOBAL INVESTORS DISTRIBUTO 1345 AVENUE OF THE AMERICAS NEW YORK, NY 10105 ALPS DISTRIBUTORS, INC P.O. BOX 328 DENVER, CO 80202 AMERICAN FUNDS DISTRIBUTORS, INC. 95-2769620 FRANKLIN TEMPLETON DISTRIBUTORS, I 100 FOUNTAIN PARKWAY ST. PETERSBURG, FL 33716 INVESCO 1555 PEACHTREE STREET NW 1800 ATLANTA, GA 30309 METROPOLITAN WEST FUNDS 865 SOUTH FIGUEROA STREET LOS ANGELES, CA 90017 MFS FUND DISTRIBUTORS, INC. 04-2747644 PRUDENTIAL INVESTMENTS LLC 22-3468527 T. ROWE PRICE 100 EAST PRATT STREET BALTIMORE, MD 21202 VANGUARD 455 DEVON PARK DRIVE WAYNE, PA 19087
        3259865,https://efast2-filings-public.s3.amazonaws.com/prd/2022/10/14/20221014155008NAL0027803457001.pdf,Long,Yes,VOYA RETIREMENT INSURANCE 71-0294708
        4264765,https://efast2-filings-public.s3.amazonaws.com/prd/2022/09/22/20220922095457NAL0003236864001.pdf,Long,Yes,FIDELITY INVESTMENTS INSTITUTIONAL 04-2647786
        4327306,https://efast2-filings-public.s3.amazonaws.com/prd/2022/10/14/20221014215057NAL0032008288001.pdf,Long,Yes,FIDELITY INVESTMENTS INSTITUTIONAL 04-2647786
        3259617,https://efast2-filings-public.s3.amazonaws.com/prd/2022/09/09/20220909101329NAL0047988066001.pdf,Short,N/A,N/A
        """,
        agent=analyst,
        output_file=f"{account_id}_recordkeeper.csv",
    )

    # Instantiate the crew
    document_crew = Crew(
        agents=[analyst],
        tasks=[analysis_task],
        process=Process.sequential,  # Tasks will be executed one after the other,
        memory=True,
        verbose=True
    )
    result = document_crew.kickoff()
    append_row_to_csv(result)
    

def main(csv_file_path):
    # 1. Load the CSV file into a DataFrame
    df = pd.read_csv(csv_file_path)
    
    # 2. Extract "Account ID" and "Link" fields
    account_ids = df['Account ID']
    links = df['Link']
    
    # 3. Call parseRecordKeeperFromLink() with each "Account ID" and "Link"
    for account_id, link in zip(account_ids, links):
        parseRecordKeeperFromLink(account_id, link)

if __name__ == "__main__":
    # Path to your CSV file
    csv_file_path = "test_data/EB_Book_Target_Geographies_Target_AUM_band.csv"
    main(csv_file_path)
    