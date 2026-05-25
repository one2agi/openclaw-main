#!/usr/bin/env python3
"""tests/test_handler_error_detection.py — TDD: RED tests for error stack trace detection"""
import sys, os, tempfile, subprocess, json, re
from pathlib import Path

# Add scripts dir to path for write_notified imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# Root of the skill
SKILL_ROOT = Path(__file__).parent.parent


# ─── Fixtures ──────────────────────────────────────────────────────────────────

def temp_learnings_dir():
    """Create a temp .learnings dir mimicking an agent workspace."""
    with tempfile.TemporaryDirectory() as td:
        ld = Path(td)
        for fname in ("LEARNINGS.md", "ERRORS.md", "FEATURE_REQUESTS.md"):
            (ld / fname).write_text("")
        yield ld


# ─── Helper: run handler.js with a mock event ──────────────────────────────────

def run_handler(session_key, body_for_agent, home=None):
    """
    Call handler.js with a fake event and capture what it pushes to messages.
    Returns the list of strings pushed to event.context.messages.
    """
    if home is None:
        home = os.environ.get('HOME', '/home/morav')

    handler_path = SKILL_ROOT / 'hooks' / 'handler.js'
    # Use realpath so path.join in the script resolves correctly
    handler_path_abs = str(handler_path.resolve())

    script = f"""
const oldHome = process.env.HOME;
process.env.HOME = {json.dumps(home)};
try {{
const {{ default: handler }} = require({json.dumps(handler_path_abs)});
const event = {{
  type: 'message',
  action: 'preprocessed',
  sessionKey: {json.dumps(session_key)},
  context: {{
    bodyForAgent: {json.dumps(body_for_agent)},
    messages: []
  }}
}};
handler(event);
console.log(JSON.stringify(event.context.messages));
}} finally {{
  process.env.HOME = oldHome;
}}
"""
    result = subprocess.run(
        ['node', '-e', script],
        capture_output=True, text=True, cwd=str(SKILL_ROOT)
    )
    if result.returncode != 0:
        raise RuntimeError(f"handler.js error: {result.stderr}")
    try:
        return json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        raise RuntimeError(f"handler.js returned non-JSON: {result.stdout!r}\nstderr: {result.stderr}")


# ─── RED Tests ─────────────────────────────────────────────────────────────────

def test_python_traceback_in_body_triggers_errors_reminder(temp_workspace):
    """Python stack trace in bodyForAgent should push ERRORS.md reminder."""
    home = str(temp_workspace)  # temp_workspace returns $HOME/.openclaw/workspace
    messages = run_handler(
        'agent:main:telegram:123',
        'Traceback (most recent call last):\n'
        '  File "/tmp/script.py", line 10, in <module>\n'
        '    foo()\n'
        'FileNotFoundError: [Errno 2] No such file or directory',
        home=home
    )
    # Should have pushed at least one message mentioning ERRORS.md
    error_reminders = [m for m in messages if 'ERRORS.md' in m]
    assert len(error_reminders) >= 1, f"Expected ERRORS.md reminder, got: {messages}"


def test_javascript_error_in_body_triggers_errors_reminder(temp_workspace):
    """JS/Node error in bodyForAgent should push ERRORS.md reminder."""
    home = str(temp_workspace)
    messages = run_handler(
        'agent:main:telegram:123',
        'ReferenceError: foo is not defined\n'
        '    at Object.<anonymous> (/tmp/script.js:5:10)\n'
        '    at Module._load (node:internal/modules/cjs/loader:1138:5)',
        home=home
    )
    error_reminders = [m for m in messages if 'ERRORS.md' in m]
    assert len(error_reminders) >= 1, f"Expected ERRORS.md reminder, got: {messages}"


def test_command_failed_triggers_errors_reminder(temp_workspace):
    """'Command failed with exit code' should trigger ERRORS.md reminder."""
    home = str(temp_workspace)
    messages = run_handler(
        'agent:main:telegram:123',
        'Command failed with exit code 127\n'
        'sh: 1: gcc: not found',
        home=home
    )
    error_reminders = [m for m in messages if 'ERRORS.md' in m]
    assert len(error_reminders) >= 1, f"Expected ERRORS.md reminder, got: {messages}"


def test_error_word_alone_does_not_trigger_false_positive(temp_workspace):
    """Body containing 'error handling' / 'no error' should NOT trigger ERRORS.md reminder.

    Note: 'error' alone is already in the existing ERROR_KEYWORDS list, so
    conversational 'error' triggers the existing keyword detection. The new
    stack-trace detection should NOT add new false positives for 'error handling'
    style phrases.
    """
    home = str(temp_workspace)
    messages = run_handler(
        'agent:main:telegram:123',
        'The error handling routine caught the issue and recovered gracefully.',
        home=home
    )
    error_reminders = [m for m in messages if 'ERRORS.md' in m]
    assert len(error_reminders) == 0, f"False positive — 'error handling' triggered: {messages}"


def test_no_error_triggers_nothing(temp_workspace):
    """Normal conversation should not push any error reminders."""
    home = str(temp_workspace)
    messages = run_handler(
        'agent:main:telegram:123',
        'Hello, can you help me with a Python script?',
        home=home
    )
    error_reminders = [m for m in messages if 'ERRORS.md' in m]
    assert len(error_reminders) == 0, f"No error reminders expected, got: {messages}"


def test_multiple_error_patterns_same_body_triggers_once(temp_workspace):
    """Multiple error patterns in same body should push only one reminder."""
    home = str(temp_workspace)
    messages = run_handler(
        'agent:main:telegram:123',
        'Traceback (most recent call last):\n'
        '  File "/a.py", line 1\n'
        'RuntimeError: boom\n'
        'Traceback (most recent call last):\n'
        '  File "/b.py", line 2\n'
        'ValueError: bad',
        home=home
    )
    error_reminders = [m for m in messages if 'ERRORS.md' in m]
    assert len(error_reminders) == 1, f"Expected 1 reminder, got {len(error_reminders)}: {messages}"


def test_per_agent_routing_injects_correct_learnings_dir(temp_workspace):
    """Reminder should contain the agent-specific learnings path, not a hardcoded one."""
    agent_id = 'my-agent'
    # Create the agent's own workspace at expected path
    agent_ws = temp_workspace / agent_id
    agent_ld = agent_ws / '.learnings'
    agent_ld.mkdir(parents=True, exist_ok=True)
    for fname in ("LEARNINGS.md", "ERRORS.md"):
        (agent_ld / fname).write_text("")
    # Write openclaw.json at the standard location: HOME/.openclaw/openclaw.json
    oc_json = temp_workspace / '.openclaw' / 'openclaw.json'
    oc_json.parent.mkdir(parents=True, exist_ok=True)
    oc_json.write_text(json.dumps({
        'agents': {'list': [{'id': agent_id, 'workspace': str(agent_ws)}]}
    }))

    messages = run_handler(
        f'agent:{agent_id}:telegram:123',
        'Traceback (most recent call last):\n  File "x.py", line 1\n  RuntimeError: test',
        home=str(temp_workspace)
    )
    error_reminders = [m for m in messages if 'ERRORS.md' in m]
    assert len(error_reminders) >= 1, f"No reminder: {messages}"
    # The path should reference the agent-specific workspace
    reminder = error_reminders[0]
    assert agent_id in reminder or str(agent_ld) in reminder, \
        f"Reminder should reference agent-specific path, got: {reminder}"


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])