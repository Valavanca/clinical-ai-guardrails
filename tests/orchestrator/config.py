import json
import yaml
import jsonschema
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

from loguru import logger
from smolagents import Tool, LiteLLMModel, OpenAIServerModel, CodeAgent, ToolCallingAgent


@dataclass
class AgentConfig:
    """Configuration for a single agent."""
    name: str
    description: str
    agent_type: str                                 # "code" or "tool_calling"
    model_id: str
    guidelines: List[str]                           # List of guideline files
    tools: List[str]                                # List of tool class names
    managed_agents: Optional[List[str]] = None      # Agents this agent manages
    instructions: Optional[str] = None
    additional_imports: Optional[List[str]] = None
    max_steps: Optional[int] = None
    planning_interval: Optional[int] = None


class AgentFactory:
    """Factory for creating configured agents with validation."""
    
    def __init__(self, config_dir: Path, schemas_dir: Path):
        self.config_dir = Path(config_dir)
        self.schemas_dir = Path(schemas_dir)
        self.guidelines_dir = self.config_dir / "guidelines"
        
        # schema_path = self.schemas_dir / "agent_contracts.json" 
        schema_path = self.schemas_dir / "agent_contracts_basic.json"
        with open(schema_path) as f:
            self.output_schema = json.load(f)
    
    def load_agent_configs(self) -> Dict[str, AgentConfig]:
        """Load all agent configurations from YAML files."""
        configs = {}
        
        for config_file in self.config_dir.glob("agents/*.yaml"):
            with open(config_file) as f:
                config_data = yaml.safe_load(f)
            
            config = AgentConfig(**config_data)
            configs[config.name] = config
        
        return configs

    def create_agent(
            self,
            config: AgentConfig,
            tools_registry: Dict[str, Tool],
            agents: Dict[str, Any]
        ) -> Any:
        """Create an agent from configuration."""
        
        # Get model
        # model = LiteLLMModel(model_id=config.model_id)

        model = OpenAIServerModel(
            model_id=config.model_id,
            service_tier="flex"
        )

        agent_tools = [tools_registry[tool_name] for tool_name in config.tools]
        instructions = self._build_instructions(config)

        # !DEBUG:
        # save instructions into a file into ./output/tmp
        # output_dir = Path("./output/tmp")
        # output_dir.mkdir(parents=True, exist_ok=True)
        # with open(output_dir / f"{config.name}_instructions.txt", "w") as f:
        #     f.write(instructions)

        if config.managed_agents:
            try:
                managed_agents = [agents[name] for name in config.managed_agents]
            except KeyError as e:
                logger.warning(f"Managed agent not found: {e}. Available agents: {list(agents.keys())}")
        else:
            managed_agents = []

        if config.agent_type == "code":
            return CodeAgent(
                model=model,
                tools=agent_tools,
                name=config.name,
                description=config.description,
                instructions=instructions,
                managed_agents=managed_agents,
                additional_authorized_imports=config.additional_imports or [],
                max_steps=config.max_steps,
                planning_interval=config.planning_interval
            )
        elif config.agent_type == "tool_calling":
            return ToolCallingAgent(
                model=model,
                tools=agent_tools,
                name=config.name,
                description=config.description,
                instructions=instructions,
                managed_agents=managed_agents,
                max_steps=config.max_steps,
                planning_interval=config.planning_interval
            )
        else:
            raise ValueError(f"Unknown agent type: {config.agent_type}")
    
    def _build_instructions(self, config: AgentConfig) -> str:
        """Build agent instructions from guidelines and config."""
        
        instructions = []
        
        # --- Base instructions
        if config.instructions:
            instructions.append(config.instructions)
        
        # --- Schema
        # agent_schema = self.output_schema.get("agent_outputs", {}).get(config.name)
        # if agent_schema:
        #     instructions.append(f"\nYou MUST return output in this JSON schema:\n{json.dumps(agent_schema, indent=2)}")

        # --- Guidelines
        if config.guidelines:
            instructions.append("\n## Relevant Guidelines:")
            for guideline_file in config.guidelines:
                guideline_path = self.guidelines_dir / guideline_file
                if guideline_path.exists():
                    instructions.append(f"\n### {guideline_file}")
                    instructions.append(guideline_path.read_text())
        
        return "\n".join(instructions)
    
    def validate_output(self, agent_name: str, output: Any) -> bool:
        """Validate agent output against schema.
        """
        agent_schema = self.output_schema.get("agent_outputs", {}).get(agent_name)
        if not agent_schema:
            return True
        try:
            jsonschema.validate(output, agent_schema)
            return True
        except jsonschema.ValidationError:
            return False


class ToolsRegistry:
    """Registry for managing agent tools."""
    
    def __init__(self):
        self._tools = {}
    
    def register(self, tool: Tool):
        """Register a tool by its name."""
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> Tool:
        """Get a tool by name."""
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not registered")
        return self._tools[name]
    
    def get_multiple(self, names: List[str]) -> List[Tool]:
        """Get multiple tools by names."""
        return [self.get(name) for name in names]
    
    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())


# Global tools registry


def setup_default_tools():
    """Setup default tools registry"""
    from tests.orchestrator.tools.statistics import (
        WilsonCITool, BootstrapMetricTool, CohensDTool,
        StatisticalTestTool, MultipleTestingCorrectionTool, ClinicalMetricsTool,
        ClinicalThresholdTool, PerformanceValidatorTool
    )
    from tests.orchestrator.tools.dataset import LoadCSVDatasetTool, SummarizeDatasetTool  
    from tests.orchestrator.tools.code import ReadIPYNBTool
    from tests.orchestrator.tools.guideline import ReadMarkdownTool
    
    tools_registry = ToolsRegistry()

    # --- + Statistical tools
    tools_registry.register(WilsonCITool())
    tools_registry.register(BootstrapMetricTool())
    tools_registry.register(CohensDTool())
    tools_registry.register(StatisticalTestTool())
    tools_registry.register(MultipleTestingCorrectionTool())
    tools_registry.register(ClinicalMetricsTool())
    tools_registry.register(ClinicalThresholdTool())
    tools_registry.register(PerformanceValidatorTool())

    # --- + Dataset tools
    tools_registry.register(LoadCSVDatasetTool())
    tools_registry.register(SummarizeDatasetTool())

    # --- + Code tools
    tools_registry.register(ReadIPYNBTool())

    # --- + Guideline tools
    tools_registry.register(ReadMarkdownTool())

    return tools_registry
