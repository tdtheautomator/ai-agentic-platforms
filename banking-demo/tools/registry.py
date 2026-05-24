"""
Tool Registry and Decorator

Provides the @register_tool decorator for registering tool functions
and the TOOLS dictionary for tool discovery and execution.
"""

# Global tool registry
TOOLS = {}


def register_tool(fn):
    """
    SDK @register_tool decorator — registers function + schema.
    
    Extracts function name, docstring, and parameter names to build
    a tool schema for discovery and execution.
    
    Args:
        fn: Function to register as a tool
        
    Returns:
        The original function (unchanged)
    """
    TOOLS[fn.__name__] = {
        "name": fn.__name__,
        "description": fn.__doc__ or "",
        "params": list(fn.__code__.co_varnames[:fn.__code__.co_argcount]),
        "fn": fn,
    }
    return fn


# Alias for backward compatibility with existing code
tool = register_tool
