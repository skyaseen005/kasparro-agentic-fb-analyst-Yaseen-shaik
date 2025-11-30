**Kasparro Agentic FB Analyst**

Kasparro Agentic FB Analyst is an AI-powered multi-agent system that analyzes Facebook Ads performance, identifies why ROAS or CTR dropped, validates insights with data, and generates new creative recommendations automatically.

It uses an agentic workflow and supports both Groq (free) and OpenAI models.

<img width="749" height="494" alt="image" src="https://github.com/user-attachments/assets/fea8d155-00a9-4c9b-8201-89b15c7e89d3" />

                      work Flow


**Quick Start**

**1. Clone Repository**

`git clone https://github.com/<your-username>/kasparro-agentic-fb-analyst-Yaseen-shaik.git`

`cd kasparro-agentic-fb-analyst-Yaseen-shaik`


**2. Create Virtual Environment**

**Windows:**

`python -m venv venv`

`venv\Scripts\activate`

**Mac/Linux:**

`python3 -m venv venv`

`source venv/bin/activate`

**3. Install Dependencies**
pip install -r requirements.txt

**4. Configure API Keys**


Create a file named .env in the root directory:

`OPENAI_API_KEY=your_openai_api_key`

`GROQ_API_KEY=your_groq_api_key`

**Run Analysis**


**Default analysis**

`python run.py "Why did ROAS drop last week?"`

**Custom query**

p`ython run.py "Analyze campaign performance and suggest improvements"`

**Use sample dataset**

`python run.py "Diagnose ROAS changes" --sample`

**Use custom CSV**

`python run.py "Analyze performance" --data-path data/my_ads.csv`

**Project Structure**

<img width="870" height="897" alt="image" src="https://github.com/user-attachments/assets/6f442f9e-b712-4380-8c55-4c1bf11a7349" />




**Output Files**


**File	Description**

File Name                                             Description


**reports/report.md**                      Final human-readable analysis report

**reports/insights.json**                  AI-generated hypotheses and validated insights

**reports/creatives.json**                 Creative recommendations for low-performing ads

**logs/run_TIMESTAMP.json**                Execution logs for debugging the table generation process



**Configuration (config/config.yaml)**


**Thresholds**

**thresholds:**

           low_ctr: 0.015
           
           low_roas: 3.0
           
           high_confidence: 0.75
           
           min_spend: 100.0
           
           fatigue_days: 14
  

**Model (OpenAI Fallback)**

**model:**

           name: "gpt-3.5-turbo"
           
           temperature: 0.7
           
           max_tokens: 2000
           
           timeout: 60

**Groq Model Settings**

**groq:**

              model: "llama-3.3-70b-versatile"
              
              temperature: 0.4
              
              max_tokens: 2000

**Data Requirements**

**data:**

  sample_size: 1000
  
  date_format: "%Y-%m-%d"
  
  required_columns:
  
    - campaign_name
    
    - adset_name
    
    - date
    
    - spend
    
    - impressions
    
    - clicks
    
    - ctr
    
    - purchases
    
    - revenue
    
    - roas
    
    - creative_type

    - creative_message
    
    - audience_type

    - platform
    
    - country

**Agent Settings**

**agents:**

     -max_retries: 2
  
     -min_confidence: 0.5
  
     -reflection_enabled: true
  

**Output Options**

**output:**

      log_format: "json"
      
     save_intermediate: true
     
     verbose: true

      random_seed: 42

**Agent Descriptions**

**Planner Agent**


Creates a structured plan by breaking down the user query into actionable tasks.

**Data Agent**

Loads, validates, cleans, and summarizes the Facebook Ads dataset.

**Insight Agent**

Generates hypotheses describing why ROAS/CTR changed using reasoning chains.

**Evaluator Agent**

Validates hypotheses using statistical evidence and assigns confidence scores.

**Creative Generator**

Generates fresh creative ideas (headlines, messages, CTAs) for underperforming campaigns.

**Quality Assurance**

         **The system performs:**
         
         Data validation
         
         Confidence scoring
         
         Statistical verification
         
         Reflection loop for improving low-confidence insights
         
         Multi-agent consistency checks

**Confidence scale:**

`High (0.75–1.0)`

`Medium (0.50–0.74)`

`Low (0.00–0.49)`

**Example Output**

         **insights.json**
         {
           "query": "Why did ROAS decrease in the last week?",
           "timestamp": "2024-11-29T10:30:00",
           "hypotheses": [
             {
               "id": "H1",
               "hypothesis": "Creative fatigue in top-spending campaigns caused declining CTR",
               "confidence": 0.82,
               "evidence": [
                 "CTR dropped from 0.021 to 0.015",
                 "Campaigns running more than 14 days show 35% decline",
                 "Video creatives stayed stable while Images dropped"
               ],
               "recommendation": "Refresh creatives for adsets older than 2 weeks"
             }
           ]
         }


         

         creatives.json
         {
           "timestamp": "2024-11-29T10:30:00",
           "recommendations": [
             {
               "campaign_name": "Men_Comfort_Adset-1",
               "current_ctr": 0.012,
               "current_message": "Breathable comfort",
               "new_creatives": [
                 {
                   "headline": "Stay Cool All Day Long",
                   "message": "Premium breathable fabric designed for daily comfort",
                   "cta": "Shop Comfort Collection",
                   "rationale": "Leverages top-performing cooling theme"
                 }
               ]
             }
           ]
         }

**Troubleshooting**


Missing API Key

Add keys inside .env.

CSV Not Found

Use:

--sample

or:

--data-path path/to/file.csv

Low Confidence

System retries automatically using reflection.

      Development Guide
      
      Adding a New Agent
      
      Create a file in src/agents/
      
      Add its prompt in src/prompts/
      
      Link it inside src/orchestrator/workflow.py

Run Tests

`pytest --cov=src`
