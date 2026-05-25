#!/usr/bin/env python3
"""tests/conftest.py — pytest fixtures for self-improvement-loop tests"""
import sys, os
import pytest
from pathlib import Path

# Ensure scripts/ is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


@pytest.fixture
def temp_learnings_dir(tmp_path):
    """Create a temp .learnings dir at the path handler.js expects.
    handler.js uses getLearningsDir() which returns:
      getAgentWorkspace(agentId) + '/.learnings'
    getAgentWorkspace defaults to: $HOME/.openclaw/workspace
    So we create: tmp_path/.openclaw/workspace/.learnings/
    Yields the .learnings Path.
    """
    ld = tmp_path / '.openclaw' / 'workspace' / '.learnings'
    ld.mkdir(parents=True, exist_ok=True)
    for fname in ("LEARNINGS.md", "ERRORS.md", "FEATURE_REQUESTS.md"):
        (ld / fname).write_text("")
    return ld


@pytest.fixture
def temp_workspace(tmp_path, agent_id='main'):
    """Create a temp workspace at the path handler.js expects for agent 'main'.
    handler.js uses: process.env.HOME + '/.openclaw/workspace'
    So we create: tmp_path/.openclaw/workspace/.learnings/
    Set HOME=tmp_path in the test, so handler resolves to:
      HOME/.openclaw/workspace/.learnings  ✓
    Yields tmp_path (the directory to set as HOME in tests).
    """
    ld = tmp_path / '.openclaw' / 'workspace' / '.learnings'
    ld.mkdir(parents=True, exist_ok=True)
    for fname in ("LEARNINGS.md", "ERRORS.md", "FEATURE_REQUESTS.md"):
        (ld / fname).write_text("")
    # Return tmp_path so test sets HOME=tmp_path
    return tmp_path