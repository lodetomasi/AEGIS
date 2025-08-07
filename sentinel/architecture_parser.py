"""Architecture parsing for agent configuration analysis."""

import json
import yaml
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path
import re


@dataclass
class ModelInfo:
    """Information about an AI model."""
    name: str
    version: Optional[str] = None
    provider: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)


@dataclass
class ToolInfo:
    """Information about a tool/function."""
    name: str
    description: str
    permissions: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    risk_level: str = "low"  # low, medium, high
    
    def has_permission(self, permission: str) -> bool:
        """Check if tool has specific permission."""
        return permission in self.permissions


@dataclass
class AgentArchitecture:
    """Complete agent architecture representation."""
    
    # Core components
    models: List[ModelInfo]
    tools: List[ToolInfo]
    
    # Permissions and access
    permissions: Dict[str, bool]
    data_access: List[str]
    api_access: List[str]
    
    # Configuration
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    
    # Dependencies
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    
    # Workflow
    workflow_steps: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    version: Optional[str] = None
    created_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_dependency_graph(self) -> Dict[str, Set[str]]:
        """Get dependency graph as adjacency list."""
        graph = {}
        
        for component, deps in self.dependencies.items():
            if component not in graph:
                graph[component] = set()
            graph[component].update(deps)
            
            # Ensure all dependencies are in graph
            for dep in deps:
                if dep not in graph:
                    graph[dep] = set()
        
        return graph
    
    def get_all_permissions(self) -> Set[str]:
        """Get all permissions across tools and config."""
        all_perms = set()
        
        # Config permissions
        for perm, enabled in self.permissions.items():
            if enabled:
                all_perms.add(perm)
        
        # Tool permissions
        for tool in self.tools:
            all_perms.update(tool.permissions)
        
        return all_perms
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'models': [
                {
                    'name': m.name,
                    'version': m.version,
                    'provider': m.provider,
                    'parameters': m.parameters,
                    'capabilities': m.capabilities,
                    'limitations': m.limitations
                }
                for m in self.models
            ],
            'tools': [
                {
                    'name': t.name,
                    'description': t.description,
                    'permissions': t.permissions,
                    'parameters': t.parameters,
                    'risk_level': t.risk_level
                }
                for t in self.tools
            ],
            'permissions': self.permissions,
            'data_access': self.data_access,
            'api_access': self.api_access,
            'system_prompt': self.system_prompt,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'dependencies': self.dependencies,
            'workflow_steps': self.workflow_steps,
            'version': self.version,
            'created_by': self.created_by,
            'metadata': self.metadata
        }


class ArchitectureParser:
    """Parses agent configurations to extract architecture."""
    
    def __init__(self):
        """Initialize architecture parser."""
        self.known_models = self._load_known_models()
        self.known_tools = self._load_known_tools()
    
    def _load_known_models(self) -> Dict[str, Dict[str, Any]]:
        """Load database of known AI models."""
        return {
            'gpt-4': {
                'provider': 'openai',
                'capabilities': ['text_generation', 'reasoning', 'code_generation'],
                'limitations': ['hallucination', 'training_cutoff', 'context_limit']
            },
            'claude-3': {
                'provider': 'anthropic',
                'capabilities': ['text_generation', 'analysis', 'code_generation'],
                'limitations': ['hallucination', 'training_cutoff']
            },
            'gemini-pro': {
                'provider': 'google',
                'capabilities': ['text_generation', 'multimodal', 'reasoning'],
                'limitations': ['hallucination', 'api_limits']
            },
            'llama-2': {
                'provider': 'meta',
                'capabilities': ['text_generation', 'open_source'],
                'limitations': ['smaller_context', 'less_capable']
            }
        }
    
    def _load_known_tools(self) -> Dict[str, Dict[str, Any]]:
        """Load database of known tools/functions."""
        return {
            'web_search': {
                'permissions': ['internet_access'],
                'risk_level': 'medium',
                'description': 'Search the web for information'
            },
            'code_execution': {
                'permissions': ['code_exec', 'system_access'],
                'risk_level': 'high',
                'description': 'Execute code in sandbox'
            },
            'file_read': {
                'permissions': ['file_read'],
                'risk_level': 'medium',
                'description': 'Read files from filesystem'
            },
            'file_write': {
                'permissions': ['file_write'],
                'risk_level': 'high',
                'description': 'Write files to filesystem'
            },
            'database_query': {
                'permissions': ['db_read'],
                'risk_level': 'medium',
                'description': 'Query database'
            },
            'database_write': {
                'permissions': ['db_write'],
                'risk_level': 'high',
                'description': 'Write to database'
            },
            'api_call': {
                'permissions': ['api_access'],
                'risk_level': 'medium',
                'description': 'Make external API calls'
            },
            'email_send': {
                'permissions': ['email_access'],
                'risk_level': 'high',
                'description': 'Send emails'
            }
        }
    
    def parse(self, config: Dict[str, Any]) -> AgentArchitecture:
        """
        Parse agent configuration into architecture.
        
        Args:
            config: Agent configuration dictionary
            
        Returns:
            Parsed agent architecture
        """
        # Parse models
        models = self._parse_models(config)
        
        # Parse tools
        tools = self._parse_tools(config)
        
        # Parse permissions
        permissions = self._parse_permissions(config)
        
        # Parse data access
        data_access = self._parse_data_access(config)
        
        # Parse API access
        api_access = self._parse_api_access(config)
        
        # Parse workflow
        workflow_steps = self._parse_workflow(config)
        
        # Build dependencies
        dependencies = self._build_dependencies(config, models, tools)
        
        return AgentArchitecture(
            models=models,
            tools=tools,
            permissions=permissions,
            data_access=data_access,
            api_access=api_access,
            system_prompt=config.get('system_prompt'),
            temperature=config.get('temperature', 0.7),
            max_tokens=config.get('max_tokens', 2048),
            dependencies=dependencies,
            workflow_steps=workflow_steps,
            version=config.get('version'),
            created_by=config.get('created_by'),
            metadata=config.get('metadata', {})
        )
    
    def parse_from_file(self, file_path: str) -> AgentArchitecture:
        """Parse architecture from configuration file."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(path, 'r') as f:
            if path.suffix in ['.yaml', '.yml']:
                config = yaml.safe_load(f)
            else:
                config = json.load(f)
        
        return self.parse(config)
    
    def _parse_models(self, config: Dict[str, Any]) -> List[ModelInfo]:
        """Parse model information from config."""
        models = []
        
        # Check various possible locations for model info
        model_configs = config.get('models', [])
        if not model_configs and 'model' in config:
            model_configs = [config['model']]
        
        # Also check for model in LLM config
        if 'llm' in config:
            llm_config = config['llm']
            if isinstance(llm_config, str):
                model_configs.append({'name': llm_config})
            elif isinstance(llm_config, dict):
                model_configs.append(llm_config)
        
        for model_config in model_configs:
            if isinstance(model_config, str):
                model_name = model_config
                model_info = {}
            else:
                model_name = model_config.get('name', model_config.get('model', 'unknown'))
                model_info = model_config
            
            # Look up known model info
            known_info = self.known_models.get(model_name.lower(), {})
            
            model = ModelInfo(
                name=model_name,
                version=model_info.get('version'),
                provider=model_info.get('provider', known_info.get('provider')),
                parameters=model_info.get('parameters', {}),
                capabilities=model_info.get('capabilities', known_info.get('capabilities', [])),
                limitations=model_info.get('limitations', known_info.get('limitations', []))
            )
            
            models.append(model)
        
        return models
    
    def _parse_tools(self, config: Dict[str, Any]) -> List[ToolInfo]:
        """Parse tool information from config."""
        tools = []
        
        # Check various possible locations
        tool_configs = config.get('tools', [])
        if not tool_configs:
            tool_configs = config.get('functions', [])
        if not tool_configs:
            tool_configs = config.get('capabilities', [])
        
        for tool_config in tool_configs:
            if isinstance(tool_config, str):
                tool_name = tool_config
                tool_info = self.known_tools.get(tool_name.lower(), {})
            else:
                tool_name = tool_config.get('name', 'unknown')
                tool_info = tool_config
            
            # Merge with known tool info
            known_info = self.known_tools.get(tool_name.lower(), {})
            
            tool = ToolInfo(
                name=tool_name,
                description=tool_info.get('description', known_info.get('description', '')),
                permissions=tool_info.get('permissions', known_info.get('permissions', [])),
                parameters=tool_info.get('parameters', {}),
                risk_level=tool_info.get('risk_level', known_info.get('risk_level', 'low'))
            )
            
            tools.append(tool)
        
        return tools
    
    def _parse_permissions(self, config: Dict[str, Any]) -> Dict[str, bool]:
        """Parse permissions from config."""
        permissions = {}
        
        # Direct permissions
        if 'permissions' in config:
            perms = config['permissions']
            if isinstance(perms, dict):
                permissions.update(perms)
            elif isinstance(perms, list):
                for perm in perms:
                    permissions[perm] = True
        
        # Infer from other fields
        if config.get('allow_file_access'):
            permissions['file_read'] = True
            permissions['file_write'] = config.get('allow_file_write', False)
        
        if config.get('allow_internet'):
            permissions['internet_access'] = True
        
        if config.get('allow_code_execution'):
            permissions['code_exec'] = True
        
        return permissions
    
    def _parse_data_access(self, config: Dict[str, Any]) -> List[str]:
        """Parse data access patterns."""
        data_access = []
        
        # Direct specification
        if 'data_access' in config:
            data_access.extend(config['data_access'])
        
        # Infer from other fields
        if 'databases' in config:
            data_access.extend([f"database:{db}" for db in config['databases']])
        
        if 'file_paths' in config:
            data_access.extend([f"file:{path}" for path in config['file_paths']])
        
        return data_access
    
    def _parse_api_access(self, config: Dict[str, Any]) -> List[str]:
        """Parse API access patterns."""
        api_access = []
        
        # Direct specification
        if 'api_access' in config:
            api_access.extend(config['api_access'])
        
        # Infer from other fields
        if 'external_apis' in config:
            api_access.extend(config['external_apis'])
        
        if 'webhooks' in config:
            api_access.extend([f"webhook:{w}" for w in config['webhooks']])
        
        return api_access
    
    def _parse_workflow(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse workflow steps."""
        workflow = []
        
        if 'workflow' in config:
            workflow = config['workflow']
        elif 'pipeline' in config:
            workflow = config['pipeline']
        elif 'steps' in config:
            workflow = config['steps']
        
        return workflow
    
    def _build_dependencies(
        self,
        config: Dict[str, Any],
        models: List[ModelInfo],
        tools: List[ToolInfo]
    ) -> Dict[str, List[str]]:
        """Build dependency graph."""
        dependencies = {}
        
        # Model dependencies on tools
        for model in models:
            model_key = f"model:{model.name}"
            dependencies[model_key] = []
            
            for tool in tools:
                tool_key = f"tool:{tool.name}"
                dependencies[model_key].append(tool_key)
        
        # Tool dependencies
        for tool in tools:
            tool_key = f"tool:{tool.name}"
            if tool_key not in dependencies:
                dependencies[tool_key] = []
            
            # Some tools depend on others
            if tool.name == 'code_execution' and any(t.name == 'file_write' for t in tools):
                dependencies[tool_key].append('tool:file_write')
        
        # Explicit dependencies from config
        if 'dependencies' in config:
            for component, deps in config['dependencies'].items():
                if component not in dependencies:
                    dependencies[component] = []
                dependencies[component].extend(deps)
        
        return dependencies
    
    def detect_architecture_type(self, architecture: AgentArchitecture) -> str:
        """Detect the type of agent architecture."""
        # Check for common patterns
        has_tools = len(architecture.tools) > 0
        has_web_access = any(t.name == 'web_search' for t in architecture.tools)
        has_code_exec = any(t.name == 'code_execution' for t in architecture.tools)
        has_workflow = len(architecture.workflow_steps) > 0
        
        if has_workflow and len(architecture.models) > 1:
            return "multi_agent_system"
        elif has_code_exec:
            return "code_assistant"
        elif has_tools and has_web_access:
            return "research_assistant"
        elif has_tools:
            return "tool_augmented"
        else:
            return "basic_llm"