**Kasparro Agentic FB Analyst**
A multi-agent system for autonomous Facebook Ads performance analysis and creative recommendations using GroqCloud
┌─────────────┐
│   User      │
│   Query     │
└──────┬──────┘
       │
       v
┌─────────────────┐
│ Planner Agent   │  Decomposes query into subtasks
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Data Agent     │  Loads & summarizes dataset
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Insight Agent   │  Generates hypotheses about performance
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Evaluator Agent │  Validates hypotheses quantitatively
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Creative Gen    │  Produces new creative recommendations
└────────┬────────┘
         │
         v
   ┌──────────┐
   │  Output  │
   │  Report  │
   └──────────┘
   This the overall flowchart of the Project
**Quick Start**
**1. Setup Environment**
# Clone repository
git clone <your-repo-url>
cd kasparro-agentic-fb-analyst-yourname
# Create virtual environment
python -m venv venv
venv\Scripts\activate
# Install dependencies
pip install -r requirements.txt

**2. Configure API Key**
**Create a .env file in the root directory:**
OPENAI_API_KEY=your_openai_api_key_here

**3. Run Analysis**
# Full analysis with default query
python run.py "Why did ROAS drop last week?"

# Custom query
python run.py "Analyze campaign performance and suggest improvements"

# Use sample data
python run.py "Diagnose ROAS changes" --sample

# Specify custom data file
python run.py "Analyze performance" --data-path data/my_ads.csv

The Structure Of Project

kasparro-agentic-fb-analyst-yourname/
├── README.md
├── requirements.txt
├── config/
│   └── config.yaml
├── src/
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── planner.py
│   │   ├── data_agent.py
│   │   ├── insight_agent.py
│   │   ├── evaluator.py
│   │   └── creative_generator.py
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   └── workflow.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── data_loader.py
├── prompts/
│   ├── planner_prompt.md
│   ├── data_agent_prompt.md
│   ├── insight_prompt.md
│   ├── evaluator_prompt.md
│   └── creative_prompt.md
├── data/
│   ├── README.md
│   └── sample_fb_ads.csv
├── logs/
│   └── .gitkeep
├── reports/
│   └── .gitkeep
├── tests/
│   └── test_evaluator.py
├── run.py


**Output Files**
After running the analysis, you'll find:

reports/report.md - Human-readable analysis report
reports/insights.json - Structured hypotheses with confidence scores
reports/creatives.json - Creative recommendations for low-CTR campaigns
logs/run_TIMESTAMP.json - Detailed execution logs

**Configuration**
Edit config/config.yaml to customize:


**thresholds:**
  low_ctr: 0.015          
  low_roas: 3.0           
  high_confidence: 0.75   
  min_spend: 100.0
  fatigue_days: 14


**model:**
  name: "gpt-3.5-turbo" 
  temperature: 0.7
  max_tokens: 2000
  timeout: 60

**groq:**
  model: "llama-3.3-70b-versatile"
  temperature: 0.4
  max_tokens: 2000

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

**agents:**
  max_retries: 2          
  min_confidence: 0.5    
  reflection_enabled: true 


**output:**
  log_format: "json"      
  save_intermediate: true
  verbose: true          
random_seed: 42


**requirements.txt**

openai>=1.97.1

numpy==1.26.4
pandas==2.2.0
opencv-python==4.7.0.72
openai>=1.97.1
langchain-perplexity==0.1.2
pyyaml==6.0.1
python-dotenv==1.0.0
loguru==0.7.2
pytest==7.4.3
pytest-cov==4.1.0
black==23.12.1
flake8==7.0.0
mypy==1.8.0
tqdm==4.66.1
tenacity==8.2.3

**Agent Descriptions**
**Planner Agent**
Receives user query and breaks it down into actionable subtasks. Determines what analysis is needed and coordinates the workflow.
**Data Agent**
Loads the Facebook Ads dataset, performs initial cleaning, and creates statistical summaries to feed to other agents.
**Insight Agent**
Generates hypotheses about performance patterns. Uses reasoning chains to explain potential causes of ROAS fluctuations, CTR changes, etc.
**Evaluator Agent**
Validates hypotheses using quantitative analysis. Calculates confidence scores and provides evidence for or against each hypothesis.
**Creative Generator**
Analyzes low-performing campaigns and generates new creative recommendations (headlines, messages, CTAs) based on successful patterns in the dataset.
**Validation & Quality Assurance**
The system includes multiple validation layers:

Data Quality Checks: Validates CSV format, required columns, data types
Hypothesis Confidence: Each insight includes a confidence score (0-1)
Quantitative Evidence: All claims backed by statistical evidence
Reflection Loop: Low-confidence results trigger re-analysis

**Example confidence scoring:**

High (0.75-1.0): Strong statistical evidence
Medium (0.5-0.74): Moderate evidence, some uncertainty
Low (0.0-0.49): Weak evidence, requires more investigation

E**xample Outputs**
**Sample Query**
**python run.py "Why did ROAS decrease in the last week?"**
**Sample insights.json**
json{
  "query": "Why did ROAS decrease in the last week?",
  "timestamp": "2024-11-29T10:30:00",
  "hypotheses": [
    {
      "id": "H1",
      "hypothesis": "Creative fatigue in top-spending campaigns led to declining CTR",
      "confidence": 0.82,
      "evidence": [
        "Average CTR dropped from 0.021 to 0.015 (-28.6%)",
        "Campaigns running >14 days show 35% lower CTR",
        "Video creatives maintained performance vs Image (-12% CTR drop)"
      ],
      "recommendation": "Refresh creative assets for campaigns older than 2 weeks"
    }
  ]
}
**Sample creatives.json**
json{
  "timestamp": "2024-11-29T10:30:00",
  "recommendations": [
    {
      "campaign_name": "Men_Comfort_Adset-1",
      "current_ctr": 0.012,
      "current_message": "Breathable comfort",
      "new_creatives": [
        {
          "headline": "Stay Cool All Day Long",
          "message": "Premium breathable fabric that moves with you",
          "cta": "Shop Comfort Collection",
          "rationale": "Combines top-performing 'cooling' theme with specificity"
        }
      ]
    }
  ]
}


**Troubleshooting**
Issue: OpenAI API key not found

Solution: Ensure .env file exists with valid OPENAI_API_KEY

Issue: File not found: data/fb_ads.csv

Solution: Use --sample flag or provide --data-path

Issue: Low confidence results

Solution: System will automatically retry with refined prompts

Development
Adding New Agents

Create new agent file in src/agents/
Inherit from base agent pattern
Add corresponding prompt in prompts/
Update orchestrator workflow
