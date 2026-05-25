#!/usr/bin/env python3
"""tests/test_periodic_nudge.py — TDD: RED tests for Periodic Nudge feature

These tests verify that the handler pushes nudge reminders when:
1. Message count reaches threshold (>=10) AND review hasn't been triggered
2. Nudge does NOT fire when already triggered (review_triggered=true)
3. Nudge resets after complete_review() is called
4. Nudge does NOT fire before threshold is reached
"""
import sys, os, json, subprocess
from pathlib import Path

# Root of the skill
SKILL_ROOT = Path(__file__).parent.parent

# Add scripts dir to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


# ─── Helper: run handler.js with a mock event ──────────────────────────────────

def run_handler(session_key, body_for_agent, home=None):
    """
    Call handler.js with a fake event and capture what it pushes to messages.
    Returns the list of strings pushed to event.context.messages.
    """
    if home is None:
        home = os.environ.get('HOME', '/home/morav')

    handler_path = SKILL_ROOT / 'hooks' / 'handler.js'
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


# ─── Session state helpers ──────────────────────────────────────────────────────

SCRIPT_DIR = SKILL_ROOT / 'scripts'
SESSION_STATE_SH = SCRIPT_DIR / 'session_state.sh'


def call_session_state(agent_id, command, home):
    """Call session_state.sh with given command. Returns stdout stripped."""
    result = subprocess.run(
        ['bash', str(SESSION_STATE_SH), agent_id, command],
        capture_output=True, text=True,
        env={**os.environ, 'HOME': home}
    )
    if result.returncode != 0:
        raise RuntimeError(f"session_state.sh error: {result.stderr}")
    return result.stdout.strip()


# ─── Tests ──────────────────────────────────────────────────────────────────────

def test_nudge_triggers_at_threshold(temp_workspace):
    """When message_count>=10 AND !review_triggered, handler should push a nudge reminder."""
    home = str(temp_workspace)

    # Clean slate
    call_session_state('main', 'reset', home)

    # Increment message count to threshold (10)
    for _ in range(10):
        call_session_state('main', 'inc', home)

    # Verify session_state.sh returns 'yes'
    should = call_session_state('main', 'should', home)
    assert should == 'yes', f"Expected 'yes' at threshold, got: {should}"

    # Handler should push a nudge reminder
    messages = run_handler(
        'agent:main:telegram:123',
        'Hello, how are you?',
        home=home
    )
    nudge_reminders = [m for m in messages if 'nudge' in m.lower() or 'self-review' in m.lower() or 'review' in m.lower()]
    assert len(nudge_reminders) >= 1, f"Expected nudge reminder at threshold, got: {messages}"


def test_nudge_does_not_fire_when_already_triggered(temp_workspace):
    """When session_state.sh returns 'no' (review already triggered), handler should NOT push nudge."""
    home = str(temp_workspace)

    # Clean slate
    call_session_state('main', 'reset', home)

    # Increment to threshold
    for _ in range(10):
        call_session_state('main', 'inc', home)

    # First call should trigger review (sets review_triggered=true)
    messages_first = run_handler(
        'agent:main:telegram:123',
        'Hello, how are you?',
        home=home
    )

    # Verify session_state.sh now returns 'no' (already triggered)
    should = call_session_state('main', 'should', home)
    assert should == 'no', f"Expected 'no' after trigger, got: {should}"

    # Second call should NOT push nudge
    messages_second = run_handler(
        'agent:main:telegram:123',
        'Another message after review triggered.',
        home=home
    )
    nudge_reminders = [m for m in messages_second if 'nudge' in m.lower() or 'self-review' in m.lower()]
    assert len(nudge_reminders) == 0, f"Should NOT nudge when already triggered, got: {messages_second}"


def test_nudge_resets_after_complete_review(temp_workspace):
    """After complete_review() sets review_triggered=false, subsequent 'yes' should trigger again."""
    home = str(temp_workspace)

    # Clean slate
    call_session_state('main', 'reset', home)

    # Increment to threshold and trigger
    for _ in range(10):
        call_session_state('main', 'inc', home)

    # Trigger the review
    run_handler('agent:main:telegram:123', 'Hello', home=home)

    # Verify it's triggered
    should_before = call_session_state('main', 'should', home)
    assert should_before == 'no', f"Expected 'no' before complete, got: {should_before}"

    # Complete the review (resets review_triggered=false)
    call_session_state('main', 'complete', home)

    # Verify session_state.sh returns 'yes' again
    should_after = call_session_state('main', 'should', home)
    assert should_after == 'yes', f"Expected 'yes' after complete, got: {should_after}"

    # Handler should trigger nudge again
    messages_after_complete = run_handler(
        'agent:main:telegram:123',
        'Message after completing review.',
        home=home
    )
    nudge_reminders = [m for m in messages_after_complete if 'nudge' in m.lower() or 'self-review' in m.lower() or 'review' in m.lower()]
    assert len(nudge_reminders) >= 1, f"Expected nudge after complete_review(), got: {messages_after_complete}"


def test_no_nudge_before_threshold(temp_workspace):
    """Messages before reaching threshold should NOT trigger nudge."""
    home = str(temp_workspace)

    # Clean slate
    call_session_state('main', 'reset', home)

    # Increment message count to 9 (just below threshold)
    for _ in range(9):
        call_session_state('main', 'inc', home)

    # Verify session_state.sh returns 'no' (not at threshold)
    should = call_session_state('main', 'should', home)
    assert should == 'no', f"Expected 'no' before threshold, got: {should}"

    # Handler should NOT push nudge
    messages = run_handler(
        'agent:main:telegram:123',
        'Hello, how are you?',
        home=home
    )
    nudge_reminders = [m for m in messages if 'nudge' in m.lower() or 'self-review' in m.lower()]
    assert len(nudge_reminders) == 0, f"Should NOT nudge before threshold, got: {messages}"


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
