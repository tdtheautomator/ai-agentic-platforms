"""
Agent Registry and Decorator

Provides the @register_agent decorator for registering agent definitions
and the A2A_AGENTS dictionary for agent discovery and execution.
"""

# Global agent registry
A2A_AGENTS = {}


def register_agent(agent_id: str):
    """
    Decorator for registering agent definitions.
    
    Args:
        agent_id: Unique identifier for the agent (e.g., 'intake', 'risk')
        
    Returns:
        Decorator function that registers the agent definition
    """
    def decorator(fn):
        """Register the agent definition in the registry."""
        # Call the function to get the definition dict
        definition = fn()
        A2A_AGENTS[agent_id] = definition
        return fn
    return decorator
