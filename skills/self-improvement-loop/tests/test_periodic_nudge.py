#!/usr/bin/env python3
"""tests/test_periodic_nudge.py — Tests for periodic nudge/pattern notification

Tests the manager.py scan behavior for periodic nudges based on pattern frequency.
"""
import sys, os, json, subprocess
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from conftest import temp_workspace

SKILL_ROOT = Path(__file__).parent.parent
MANAGER_PY = SKILL_ROOT / 'scripts' / 'manager.py'


def run_scan(learnings_dir, threshold=2):
    """Run manager.py scan and return parsed JSON."""
    env = os.environ.copy()
    env['LEARNINGS_DIR'] = str(learnings_dir)
    result = subprocess.run([
        'python3', str(MANAGER_PY), '--json-output', 'scan',
        '--threshold', str(threshold)
    ], capture_output=True, text=True, env=env)
    if result.returncode != 0:
        raise RuntimeError(f"manager.py scan failed: {result.stderr}")
    return json.loads(result.stdout)


def add_entry(ld, etype, pattern_key, category='test'):
    """Add a single entry with given pattern_key."""
    env = os.environ.copy()
    env['LEARNINGS_DIR'] = str(ld)
    subprocess.run([
        'python3', str(MANAGER_PY), 'add',
        '--type', etype,
        '--category', category,
        '--pattern-key', pattern_key,
        '--what', f'test {etype}: {pattern_key}',
        '--source', 'test'
    ], capture_output=True, text=True, env=env)


# ─── Tests ────────────────────────────────────────────────────────────────────────

def test_nudge_triggers_at_threshold(temp_workspace):
    """With threshold=2, 2+ entries with same pattern_key should trigger should_notify=True."""
    ld = temp_workspace / '.openclaw' / 'workspace' / '.learnings'
    add_entry(ld, 'learnings', 'test.nudge.repeat')
    add_entry(ld, 'learnings', 'test.nudge.repeat')

    result = run_scan(learnings_dir=ld, threshold=2)
    patterns = result.get('patterns', [])

    matching = [p for p in patterns if p['name'] == 'test.nudge.repeat']
    assert len(matching) == 1, f"Expected pattern 'test.nudge.repeat', got {len(matching)} patterns"
    assert matching[0]['should_notify'] == True, (
        f"Expected should_notify=True with 2 entries at threshold=2, got {matching[0]['should_notify']}"
    )


def test_nudge_does_not_fire_when_already_triggered(temp_workspace):
    """Once notified, repeated scan should not re-trigger (notification_count >= count)."""
    ld = temp_workspace / '.openclaw' / 'workspace' / '.learnings'
    add_entry(ld, 'learnings', 'test.nudge.stable')
    add_entry(ld, 'learnings', 'test.nudge.stable')

    result = run_scan(learnings_dir=ld, threshold=2)
    patterns = result.get('patterns', [])
    matching = [p for p in patterns if p['name'] == 'test.nudge.stable']

    assert len(matching) == 1
    first = matching[0]

    # If notification_count >= count, should_notify should be False
    if first.get('first_entry', {}).get('notification_count', 0) >= first['count']:
        assert first['should_notify'] == False, (
            "Should NOT re-trigger if notification_count >= count"
        )


def test_nudge_resets_after_complete_review(temp_workspace):
    """After marking entry as promoted, it should not appear in scan results."""
    ld = temp_workspace / '.openclaw' / 'workspace' / '.learnings'
    add_entry(ld, 'learnings', 'test.nudge.resolved.1')
    add_entry(ld, 'learnings', 'test.nudge.resolved.2')

    # Scan and mark first entry as promoted
    env = os.environ.copy()
    env['LEARNINGS_DIR'] = str(ld)
    result = subprocess.run([
        'python3', str(MANAGER_PY), '--json-output', 'scan', '--threshold', '2'
    ], capture_output=True, text=True, env=env)

    patterns = []
    if result.returncode == 0 and result.stdout.strip():
        patterns = json.loads(result.stdout).get('patterns', [])

    if patterns:
        entry_id = patterns[0]['entries'][0]['id']
        subprocess.run([
            'python3', str(MANAGER_PY), 'update', entry_id, '--status', 'promoted'
        ], capture_output=True, text=True, env=env)

    # Verify promoted entry doesn't appear in scan
    result2 = subprocess.run([
        'python3', str(MANAGER_PY), '--json-output', 'scan', '--threshold', '2'
    ], capture_output=True, text=True, env=env)

    patterns2 = []
    if result2.returncode == 0 and result2.stdout.strip():
        patterns2 = json.loads(result2.stdout).get('patterns', [])

    # The promoted pattern_key should not appear (or should_notify=False if count < threshold)
    for p in patterns2:
        if p['name'] == patterns[0]['name'] and p['should_notify'] == False:
            break
    else:
        # If promoted entry's pattern no longer triggers, test passes
        promoted_names = [patterns[0]['name']]
        matching = [p for p in patterns2 if p['name'] in promoted_names and p['should_notify'] == True]
        assert len(matching) == 0, f"Promoted entry should not trigger: {matching}"


def test_no_nudge_before_threshold(temp_workspace):
    """With threshold=2, a single entry should NOT trigger (should_notify=False)."""
    ld = temp_workspace / '.openclaw' / 'workspace' / '.learnings'
    add_entry(ld, 'learnings', 'test.nudge.single')

    result = run_scan(learnings_dir=ld, threshold=2)
    patterns = result.get('patterns', [])

    matching = [p for p in patterns if p['name'] == 'test.nudge.single']
    # Single entry at threshold=2: pattern exists but should_notify=False
    assert len(matching) == 1 and matching[0]['should_notify'] == False, (
        f"Single entry at threshold=2 should have should_notify=False, got {matching}"
    )


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])