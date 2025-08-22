# Clinical AI Guardrails

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Proof of Concept](https://img.shields.io/badge/status-proof%20of%20concept-orange.svg)](https://github.com/Valavanca/clinical-ai-guardrails)

A lightweight validation/testing workflow that runs alongside your codebase. AI agents review notebooks (or other files) and test them against written guidelines.

### Agent Architecture

```mermaid
flowchart TD
    %% User Input Layer
    User[👤 User<br/>Request: Assess notebook<br/>📓 1.train.ipynb] 
    
    %% Orchestrator Layer
    User --> Orchestrator{🎯 Orchestrator Agent<br/>━━━━━━━━━━━━━━<br/>- Reads notebook<br/>- Plans validation<br/>- Coordinates agents}
    
    %% Tool Usage
    Orchestrator -.->|reads| NotebookTool[ • read_ipynb <br/>Extract cells & code]
    
    %% Agent Delegation
    Orchestrator -->|Task: Guideline Check| GuidelineAgent[📋 Guideline Agent<br/>━━━━━━━━━━━━━━<br/>Validates compliance]
    
    Orchestrator -->|Task: Sanity Check| SanityAgent[🔍 Sanity Agent<br/>━━━━━━━━━━━━━━<br/>Detects anti-patterns]
    
    Orchestrator -->|Task: Statistical Analysis| StatAgent[📊 Statistical Agent<br/>━━━━━━━━━━━━━━<br/>Validates ML practices]
    
    %% Guidelines and Resources
    GuidelineAgent -->|consults| Guidelines[(📄 clinical_integration.md<br/>📄 data_quality.md<br/>📄 model_selection.md)]
    
    SanityAgent -->|consults| SanityDocs[(📄 sanity_checks.md)]
    
    StatAgent -->|uses| StatTools[• wilson_ci<br/>• bootstrap_metric<br/>• cohens_d<br/>• paired_tests]
    
    StatTools -->|references| StatGuidelines[(📄 statistical_validation.md)]
    
    %% Results Flow
    GuidelineAgent -->|Compliance Report| Results{📊 Results Aggregation}
    SanityAgent -->|Issue Detection| Results
    StatAgent -->|Statistical Analysis| Results
    
    Results --> Orchestrator
    
    %% Final Output
    Orchestrator --> Report[📋 Validation Report<br/>━━━━━━━━━━━━━━<br/>✅ Passed: 12 checks<br/>⚠️ Warnings: 3 issues<br/>🔴 Critical: 1 blocker<br/>🎯 Recommendations]
    
    %% Styling
    classDef userClass fill:#e8f5e8,stroke:#2e7d32,stroke-width:3px,color:#1b5e20
    classDef orchestratorClass fill:#e3f2fd,stroke:#0277bd,stroke-width:3px,color:#01579b
    classDef agentClass fill:#fff3e0,stroke:#f57c00,stroke-width:2px,color:#e65100
    classDef toolClass fill:#fce4ec,stroke:#c2185b,stroke-width:2px,color:#880e4f
    classDef guidelineClass fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#4a148c
    classDef reportClass fill:#e8f5e8,stroke:#388e3c,stroke-width:3px,color:#2e7d32
    classDef resultsClass fill:#fff8e1,stroke:#ffa000,stroke-width:2px,color:#e65100
    
    class User userClass
    class Orchestrator orchestratorClass
    class GuidelineAgent,SanityAgent,StatAgent agentClass
    class NotebookTool,StatTools toolClass
    class Guidelines,SanityDocs,StatGuidelines guidelineClass
    class Report reportClass
    class Results resultsClass
```

- **Orchestrator Agent**: Receives notebook path, reads content, plans tasks, delegates to specialized agents, and aggregates results
- **Guideline Agent**: Validates against clinical guidelines and internal documentation (conservative approach)  
- **Sanity Agent**: Applies generic high-level checks and flags common failures or violations
- **Statistical Agent**: Validates ML/statistical best practices for small clinical datasets using specialized tools


## Installation
```bash
cd clinical-ai-guardrails
uv sync
```


## Quick Start
```python
from tests.orchestrator.agent import get_system

system = get_system()
system.run_validation(
    "Assess `src/clinical_ai_guardrails/notebooks/1.train.ipynb`",
    max_steps=6
)
```

> [!NOTE]  
> By default, the system uses **OpenAI API** (gpt-5-nano). Create a `.env` file with your API key:
> 
> ```bash
> OPENAI_API_KEY=your_api_key_here
> ```
> 
> Alternative providers or local models can also be configured via LiteLLM (`LiteLLMModel`).