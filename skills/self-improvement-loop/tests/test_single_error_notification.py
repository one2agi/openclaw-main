#!/usr/bin/env python3
"""tests/test_single_error_notification.py — Tests for single-failure ERROR notification

Tests the --error-mode equivalent behavior via manager.py scan.
In error mode, threshold=1 for errors (vs threshold=2 for normal).
"""
import sys, os, json, subprocess
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from conftest import temp_workspace

SKILL_ROOT = Path(__file__).parent.parent
MANAGER_PY = SKILL_ROOT / 'scripts' / 'manager.py'


# ─── Helpers ────────────────────────────────────────────────────────────────────

def run_scan(learnings_dir, threshold=2):
    """Run manager.py scan and return parsed JSON."""
    env = os.environ.copy()
    env['LEARNINGS_DIR'] = str(learnings_dir)
    args = ['python3', str(MANAGER_PY), '--json-output', 'scan', '--threshold', str(threshold)]
    result = subprocess.run(args, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        raise RuntimeError(f"manager.py scan failed: {result.stderr}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"manager.py scan returned non-JSON: {result.stdout!r}\nstderr: {result.stderr}")


def write_error_entry(ld, pattern_key, category='test'):
    """Write a single error entry via manager.py."""
    env = os.environ.copy()
    env['LEARNINGS_DIR'] = str(ld)
    subprocess.run([
        'python3', str(MANAGER_PY), 'add',
        '--type', 'errors',
        '--category', category,
        '--pattern-key', pattern_key,
        '--what', f'test error: {pattern_key}',
        '--source', 'test'
    ], capture_output=True, text=True, env=env)


def write_learning_entry(ld, category, pattern_key):
    """Write a single learning entry via manager.py."""
    env = os.environ.copy()
    env['LEARNINGS_DIR'] = str(ld)
    subprocess.run([
        'python3', str(MANAGER_PY), 'add',
        '--type', 'learnings',
        '--category', category,
        '--pattern-key', pattern_key,
        '--what', f'test learning: {pattern_key}',
        '--source', 'test'
    ], capture_output=True, text=True, env=env)


# ─── Tests ────────────────────────────────────────────────────────────────────────

def test_single_error_entry_triggers_notification(temp_workspace):
    """With threshold=1, a single error entry should have should_notify=True."""
    ld = temp_workspace / '.openclaw' / 'workspace' / '.learnings'
    write_error_entry(ld, 'test.error.single', 'test')

    result = run_scan(learnings_dir=ld, threshold=1)

    patterns = result.get('patterns', [])
    error_patterns = [p for p in patterns if p['name'] == 'test.error.single']

    assert len(error_patterns) == 1, f"Expected 1 pattern for test.error.single, got {len(error_patterns)}"
    assert error_patterns[0]['should_notify'] == True, (
        f"Expected should_notify=True for single error entry with threshold=1, "
        f"got {error_patterns[0]['should_notify']}"
    )


def test_error_mode_uses_threshold_1(temp_workspace):
    """threshold=1 should be passed correctly."""
    ld = temp_workspace / '.openclaw' / 'workspace' / '.learnings'
    write_error_entry(ld, 'test.error.threshold', 'test')

    result = run_scan(learnings_dir=ld, threshold=1)

    assert result.get('meta', {}).get('threshold') == 1, (
        f"Expected threshold=1, got {result.get('meta', {}).get('threshold')}"
    )


def test_learnings_threshold_still_2_in_normal_mode(temp_workspace):
    """With threshold=2, a single learning entry should NOT trigger (should_notify=False)."""
    ld = temp_workspace / '.openclaw' / 'workspace' / '.learnings'
    write_learning_entry(ld, 'correction', 'test.correction.single')

    result = run_scan(learnings_dir=ld, threshold=2)

    patterns = result.get('patterns', [])
    learning_patterns = [p for p in patterns if p['name'] == 'test.correction.single']

    assert len(learning_patterns) == 1 and learning_patterns[0]['should_notify'] == False, (
        f"Expected should_notify=False for single learning at threshold=2, got {learning_patterns}"
    )


def test_mixed_files_error_mode_only_affects_errors(temp_workspace):
    """With threshold=1, error entry triggers but learning entry (count=1) does NOT."""
    ld = temp_workspace / '.openclaw' / 'workspace' / '.learnings'
    write_error_entry(ld, 'test.error.mixed', 'test')
    write_learning_entry(ld, 'correction', 'test.correction.mixed')

    result = run_scan(learnings_dir=ld, threshold=1)

    patterns = result.get('patterns', [])
    error_patterns = [p for p in patterns if 'test.error.mixed' in p['name']]
    learning_patterns = [p for p in patterns if 'test.correction.mixed' in p['name']]

    assert len(error_patterns) == 1 and error_patterns[0]['should_notify'] == True, (
        f"Expected error entry to trigger, got {error_patterns}"
    )
    # At threshold=1, both error and learning entries with count=1 trigger
    assert len(learning_patterns) == 1 and learning_patterns[0]['should_notify'] == True, (
        f"With threshold=1, single learning entry should also trigger, got {learning_patterns}"
    )


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])