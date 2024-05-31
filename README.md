# pdf_scrape_job

CrewAI script to loop through a csv, scrape pdfs, and output values to a csv

## developer setup

1.  (running Python 3.12.2)
2.  run `python3 -m venv .venv`
3.  run `source .venv/bin/activate`
4.  run `pip install -U -r requirements.txt`

## Google cloud run set up

1. Create your google cloud account
2. Create your google cloud bucket
3. Go to cloud run and spin up your ollama instance.. you need at least 8gb of ram which requires at least 2 vcpus
4. Once the image is deployed, you need to get it to pull a llama2 model, run the following curl command (with the correct host)
5. Now you need to create the LLM on the remote Ollama with this command.

```bash
curl "https://ollamadefault-4n7hvc5kvq-uk.a.run.app/api/create" -d '{ "name": "mistral_tools", "modelfile": "<modelfile on a single line>" }'
```

in this case it was

```bash
curl "https://ollamadefault-4n7hvc5kvq-uk.a.run.app/api/create" -d '{ "name": "mixtral_tools", "modelfile": "FROM mixtral:latest\nPARAMETER temperature 0.2\nSYSTEM \"You are an assistant proficient in understanding and learning how to call functions defined by the user.\"" }'
```

6. To install an LLM from Ollama.ai/library

```bash
curl "https://ollamadefault-4n7hvc5kvq-uk.a.run.app/api/pull" -d '{  "name": "mixtral" }'
curl "https://ollamadefault-4n7hvc5kvq-uk.a.run.app/api/pull" -d '{  "name": "mixtral:8x7b-instruct-v0.1-q2_K", "stream": true }'
```

or copy your models folder up to the bucket (experimental)

```bash
gsutil -m cp -r /Users/ryankirby/ollama/models gs://ollamamodels/models
```

6. Test a deployed LLM with

```bash
curl "https://ollamadefault-4n7hvc5kvq-uk.a.run.app/api/generate" -d '{ "model": "mixtral", "prompt": "Why is the sky blue?", "stream": false }'
curl "https://ollamadefault-4n7hvc5kvq-uk.a.run.app/api/chat" -d '{ "model": "mixtral", "messages": [{ "role": "user", "content" : "Why is the sky blue?", "stream": false }]}'
```

7. To remove a model and clear up space

```bash
curl -X DELETE "https://ollamadefault-4n7hvc5kvq-uk.a.run.app/api/delete" -d '{  "name": "mistral" }'
```

# ollama on docker setup (local dev)

1. ensure docker is installed
2. run `docker ps` to check if it's not already running
3. to spin ollama up on a container - run `docker run -d -v /Users/ryankirby/ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama`
4. to interact with ollama client - run `docker exec -it ollama ollama run llama2` - to run llama2 LLM specifically
5. (optional): add an alias to your .bashrc file by adding `alias ollama='docker exec -it ollama ollama'`
6. (optional): then you can run `ollama run llama2` like normal

# developer setup

1. (running Python 3.12.2)
2. run `python3 -m venv .venv`
3. run `source .venv/bin/activate`
4. run `pip install -U -r requirements.txt`

# run app

1. create a `.env` file in the roof of this direcotry like so

```bash
OPENAI_API_KEY="<input your openai api key>"
LANGCHAIN_API_KEY="<input your langsmith key>"
```

2. place `EB_Book_Target_Geographies_Target_AUM_band.csv` in a folder called `test_data`
3. `python scrape_job.py`
