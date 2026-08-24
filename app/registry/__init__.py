"""
Enterprise Agent Registry package for Prometheus sub-agent discovery and governance.
"""

from app.registry.agent_registry import AgentRegistry, AgentMetadata, agent_registry

__all__ = ["AgentRegistry", "AgentMetadata", "agent_registry"]
