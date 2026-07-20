from langchain_core.tools import tool


@tool
def search_memory(query: str, child_id: str) -> str:
    """Search the child's long-term memories for relevant information.

    Args:
        query: Natural language query describing what to search for.
        child_id: The child's unique identifier.

    Returns:
        Matching memory contents as a formatted string.
    """
    # Stub implementation — Runtime injects actual MemoryStore dependency
    return f"[search_memory stub] Searching for: {query}"


@tool
def save_memory(content: str, child_id: str, memory_type: str = "fact", importance: float = 0.5) -> str:
    """Save a new memory about the child.

    Args:
        content: The memory content in natural language.
        child_id: The child's unique identifier.
        memory_type: Type of memory (fact, interest, emotion, milestone).
        importance: Importance score from 0.0 to 1.0.

    Returns:
        Confirmation message.
    """
    return f"[save_memory stub] Saved: {content}"


@tool
def get_child_info(child_id: str) -> str:
    """Get basic information about the child (age, grade, nickname).

    Args:
        child_id: The child's unique identifier.

    Returns:
        Child information as a formatted string.
    """
    return f"[get_child_info stub] child_id: {child_id}"
