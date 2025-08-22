from __future__ import annotations
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional

from loguru import logger
from smolagents import FinalAnswerTool, GradioUI

from tests.orchestrator.config import AgentFactory, ToolsRegistry, AgentConfig

from tests.orchestrator.tools.statistics import (
    WilsonCITool, BootstrapMetricTool, CohensDTool,
    StatisticalTestTool, MultipleTestingCorrectionTool, ClinicalMetricsTool,
    ClinicalThresholdTool, PerformanceValidatorTool
)
from tests.orchestrator.tools.dataset import LoadCSVDatasetTool, SummarizeDatasetTool  
from tests.orchestrator.tools.code import ReadIPYNBTool
from tests.orchestrator.tools.guideline import ReadMarkdownTool


class ClinicalAgentSystem:
    """Main system for managing clinical AI validation agents."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path(__file__).parent / "context"
        self.schemas_dir = Path(__file__).parent / "schemas"
        
        self.tools_registry = ToolsRegistry()
        self.agent_factory = AgentFactory(self.config_dir, self.schemas_dir)
        self.agents: Dict[str, Any] = {}
        
        self._setup_tools()
        self._load_agents()
    
    def _setup_tools(self):
        """Register all available tools."""
        
        # setup_default_tools()
        
        # --- + Statistical tools
        self.tools_registry.register(WilsonCITool())
        self.tools_registry.register(BootstrapMetricTool())
        self.tools_registry.register(CohensDTool())
        self.tools_registry.register(StatisticalTestTool())
        self.tools_registry.register(MultipleTestingCorrectionTool())
        self.tools_registry.register(ClinicalMetricsTool())
        self.tools_registry.register(ClinicalThresholdTool())
        self.tools_registry.register(PerformanceValidatorTool())

        # --- + Dataset tools
        self.tools_registry.register(LoadCSVDatasetTool())
        self.tools_registry.register(SummarizeDatasetTool())

        # --- + Code tools
        self.tools_registry.register(ReadIPYNBTool())

        # --- + Guideline tools
        self.tools_registry.register(ReadMarkdownTool())

        # --- Common tools
        self.tools_registry.register(FinalAnswerTool())


    def _load_agents(self):
        """Load agent configurations and create agents."""
        try:
            agents_dir = self.config_dir / "agents"
            if not agents_dir.exists():
                raise FileNotFoundError(f"Agents directory not found: {agents_dir}")
            
            # BUG: orchestrator must be initialized last, as it depends on the other agents listed in `managed_agents`.
            for config_file in agents_dir.glob("*.yaml"):
                with open(config_file) as f:
                    config_data = yaml.safe_load(f) 
                config = AgentConfig(**config_data)
                agent = self.agent_factory.create_agent(config, self.tools_registry._tools, self.agents)
                self.agents[config.name] = agent
        except ImportError:
            logger.error("PyYAML not installed. Please install it to load agent configurations.")
    
    def get_agent(self, name: str) -> Any:
        """Get agent by name."""
        if name not in self.agents:
            raise KeyError(f"Agent '{name}' not found. Available: {list(self.agents.keys())}")
        return self.agents[name]

    def run_validation(
            self, query: str,
            validate: bool = True,
            ui: str = None,
            **kwargs
        ) -> Dict[str, Any]:
        """Run full clinical AI validation workflow."""
        ui = str(ui).lower().strip() if ui else None
        if ui not in [None, 'gradio']:
            raise ValueError(f"Invalid UI type: {ui}. Only 'gradio' or None are allowed.")

        orchestrator = self.get_agent("orchestrator")
        
        if ui=='gradio':
            result = GradioUI(orchestrator).launch(False)
        else:
            result = orchestrator.run(query, **kwargs)
        
        if validate and hasattr(self.agent_factory, 'validate_output'):
            is_valid = self.agent_factory.validate_output("orchestrator", result)
            if not is_valid:
                logger.warning("Orchestrator output does not match expected schema")
        
        return result
    
    def validate_agent_output(self, agent_name: str, output: Any) -> bool:
        """Validate agent output against schema."""
        return self.agent_factory.validate_output(agent_name, output)


_system: Optional[ClinicalAgentSystem] = None

def get_system(config_dir: Optional[Path] = None) -> ClinicalAgentSystem:
    """Get or create the global agent system."""
    global _system
    if _system is None:
        _system = ClinicalAgentSystem(config_dir)
    return _system


def get_agent(name: str) -> Any:
    """Convenience function to get an agent."""
    return get_system().get_agent(name)


def run_clinical_validation(query: str) -> Dict[str, Any]:
    """Convenience function to run validation workflow."""
    return get_system().run_validation(query)