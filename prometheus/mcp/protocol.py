"""
Model Context Protocol (MCP) JSON-RPC 2.0 schemas and tool definitions.
"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field


class JSONRPCRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    method: str
    params: Optional[Dict[str, Any]] = Field(default_factory=dict)


class JSONRPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


class MCPToolParameter(BaseModel):
    type: str = "object"
    properties: Dict[str, Any] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)


class MCPToolDefinition(BaseModel):
    name: str
    description: str
    inputSchema: MCPToolParameter


class MCPListToolsResponse(BaseModel):
    tools: List[MCPToolDefinition]


class MCPCallToolRequest(BaseModel):
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
