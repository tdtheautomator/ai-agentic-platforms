"""Tool registry."""

TOOLS: dict[str, dict] = {}


def register_tool(fn):
    """
    Decorator to register a tool.
    
    Args:
        fn: Tool function
        
    Returns:
        Decorated function
    """
    TOOLS[fn.__name__] = {
        "name": fn.__name__,
        "description": fn.__doc__ or "",
        "params": list(fn.__code__.co_varnames[: fn.__code__.co_argcount]),
        "fn": fn,
    }
    return fn
