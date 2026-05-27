"""Tests for memory module."""

import pytest
from pathlib import Path
from memory import ContextMemory, WorkingMemory


def test_context_memory_add():
    """Test adding to context memory."""
    ctx = ContextMemory(limit=5)
    entry = ctx.add("user", "test message")
    assert entry["role"] == "user"
    assert entry["content"] == "test message"
    assert ctx.count() == 1


def test_context_memory_compaction():
    """Test context memory compaction."""
    ctx = ContextMemory(limit=3)
    for i in range(5):
        ctx.add("user", f"message {i}")
    
    # Should have compacted
    assert ctx.count() <= 4  # 1 system + 3 kept


def test_context_memory_clear():
    """Test clearing context memory."""
    ctx = ContextMemory()
    ctx.add("user", "test")
    assert ctx.count() == 1
    ctx.clear()
    assert ctx.count() == 0


def test_working_memory_set_get():
    """Test working memory set and get."""
    wm = WorkingMemory()
    wm.set("test_key", "test_value", ttl=300)
    value = wm.get("test_key")
    assert value == "test_value"


def test_working_memory_get_missing():
    """Test getting missing key from working memory."""
    wm = WorkingMemory()
    value = wm.get("nonexistent")
    assert value is None


def test_working_memory_list():
    """Test listing working memory items."""
    wm = WorkingMemory()
    wm.set("key1", "value1", ttl=300)
    wm.set("key2", "value2", ttl=300)
    items = wm.list_all()
    assert len(items) >= 2
