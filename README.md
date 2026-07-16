# PokerLLMAntiFraud

A console-based tool that monitors a poker platform's anti-fraud incidents, fetches suspicious games, and analyses them using AI models (Cloudflare Workers AI by default) to detect potential fraud patterns such as chip dumping, zero rake, and collusion. Results are saved into an Excel file for further investigation.

## Prerequisites

1. Python 3.10 or newer
2. A Cloudflare account (if you plan to use the built‑in Cloudflare provider)
3. Access credentials (login/password) for the EvenBet poker admin panel

## Installation

1. Clone the repository and navigate to the project root (the directory containing `PokerLLMAntiFraud` and `config`).
2. Install the required packages:

   pip install -r requirements.txt

## AI Provider Setup

By default the project uses Cloudflare Workers AI. The free tier gives you up to 10,000 tokens per day, which is enough for moderate usage.

### Using Cloudflare

1. Register (or log in) at Cloudflare Workers AI.
2. Create an API token with permission to run AI models.
3. Open config/providers.yaml (an example is already present) and locate the Cloudflare section. 
4. Create a .env file in the config/ directory (an example .env example is provided) and add your credentials:

### Using a different provider

If you want to use OpenAI, a local LLM, or any other provider:
1. Create a new model class similar to CloudflareModels (or extend BaseModel).
2. Update providers.yaml with the new provider’s settings (base URL, accounts, models).
3. Add the new provider’s credentials to the .env file.
4. Extend ModelFactory to recognise the new provider.

The architecture is provider‑agnostic – you only need to implement the BaseModel interface and register the provider.

## EvenBet Credentials

The tool logs into the EvenBet admin panel automatically. Add your login and password to the .env file:
ini
- LOGIN=your_admin_login
- PASSWORD=your_admin_password
- GAME_FETCHER_BASE_URL=https://demotest.evenbetpoker.com
The program will authenticate once, save the session, and reuse it as long as it remains valid.

## Running the Application

From the project root, execute:

  python -m PokerLLMAntiFraud.src.main

Make sure your working directory is the project root (the folder containing PokerLLMAntiFraud, config, and requirements.txt).

## Console Commands

1. start <model_id>	Start analysing incidents. Replace <model_id> with one of the models from providers.yaml (e.g. @cf/google/gemma-4-26b-a4b-it).
2. stop	Stop the analysis loop.
3. change_model <model_id>	Change the AI model without stopping the loop.
4. set_interval <seconds>	Set how often new incidents are fetched (default 60 seconds).
5. set_lookback <minutes>	Set how far back in time the incident search goes (default 1440 minutes = 1 day).
6. exit	Shut down the application completely.
   
## How It Works
The program authenticates with the EvenBet admin panel using the provided login and password.
It periodically fetches new fraud incidents from the anti‑fraud API.
For each incident it retrieves the related games.
Every game is downloaded as an HTML page, parsed to extract players, stacks, hand history, and other details.
The selected AI model receives a structured prompt describing the game and returns a probability score, reasoning, and a list of detected fraud types.
All results are appended to results.xlsx (created automatically). The file is updated in real time and can be opened while the program is running.
The Excel file contains columns: time, game ID, incident types, player IDs, and the model’s explanation.

The free Cloudflare tier limits you to 10,000 tokens per day. If you exceed that, requests will fail until the quota resets.
The lookback time is set to 1440 minutes (1 day) by default. Adjust it with set_lookback if you need a longer or shorter history.
The program is designed to run continuously; use stop and start to control the analysis without restarting.

## Files and Configuration
   1. config/providers.yaml – AI provider definitions and model list.
   2. config/.env – secrets: API keys, Cloudflare account ID, EvenBet login/password.
   3. results.xlsx – output file with analysis results (auto‑created).
   4. session.json – saved authentication cookies (auto‑generated, do not share).

    
