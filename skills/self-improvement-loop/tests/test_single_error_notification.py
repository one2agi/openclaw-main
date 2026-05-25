#!/usr/bin/env python3
"""tests/test_single_error_notification.py — RED tests for single-failure ERROR notification

TDD Step 1 (RED): These tests define the expected behavior for --error-mode.
They MUST FAIL until the coder implements:
  1. distill.sh --error-mode flag that sets THRESHOLD=1 and scans only ERRORS.md
  2. distill.sh passes the correct threshold to distill_json.py

Test strategy:
  - Create real LEARNINGS.md / ERRORS.md files in a temp workspace
  - Run distill.sh with LEARNINGS_DIR=<tmp> --check-only [--error-mode]
  - Parse JSON output and assert notification_trigger values
"""
import sys, os, json, subprocess
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from conftest import temp_workspace

SKILL_ROOT = Path(__file__).parent.parent
DISTILL_SH = SKILL_ROOT / 'scripts' / 'distill.sh'


# ─── Helpers ────────────────────────────────────────────────────────────────────

def run_distill(learnings_dir, extra_args=None):
    """Run distill.sh --check-only and return parsed JSON."""
    env = os.environ.copy()
    env['LEARNINGS_DIR'] = str(learnings_dir)
    args = [str(DISTILL_SH), '--check-only']
    if extra_args:
        args.extend(extra_args)
    result = subprocess.run(args, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        raise RuntimeError(f"distill.sh failed: {result.stderr}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"distill.sh returned non-JSON: {result.stdout!r}\nstderr: {result.stderr}")


def write_error_entry(ld, pattern_key, status='pending'):
    """Append a single ERRORS.md entry."""
    entry_id = f"ERR-20260525-{pattern_key.split('.')[-1][:3].upper()}"
    content = f"""## [{entry_id}] test error
**Logged**: 2026-05-25
**Status**: {status}
**Pattern-Key**: {pattern_key}
"""
    (ld / 'ERRORS.md').write_text((ld / 'ERRORS.md').read_text() + content)


def write_learning_entry(ld, category, status='pending'):
    """Append a single LEARNINGS.md entry."""
    entry_id = f"LRN-20260525-{category[:3].upper()[:3]}"
    content = f"""## [{entry_id}] {category}
**Logged**: 2026-05-25
**Status**: {status}
**Pattern-Key**: test.{category}.single
"""
    (ld / 'LEARNINGS.md').write_text((ld / 'LEARNINGS.md').read_text() + content)


def get_trigger_for(entries, source_file, name):
    """Find notification_trigger for an entry with given source_file and name."""
    for e in entries:
        if e.get('first_file') == source_file and e.get('name') == name:
            return e.get('notification_trigger', 0)
        if e.get('first_file') == source_file and name in e.get('name', ''):
            return e.get('notification_trigger', 0)
    return None


# ─── RED Tests ──────────────────────────────────────────────────────────────────

def test_single_error_entry_triggers_notification(temp_workspace):
    """With --error-mode, a single ERRORS.md entry (count=1) should have notification_trigger=1."""
    ld = temp_workspace / '.openclaw' / 'workspace' / '.learnings'
    # Write one ERRORS.md entry
    write_error_entry(ld, 'test.error.single')

    result = run_distill(learnings_dir=ld, extra_args=['--error-mode'])

    all_entries = result.get('patterns', []) + result.get('category_fallback', [])
    trigger = get_trigger_for(all_entries, 'ERRORS.md', 'test.error.single')

    assert trigger == 1, (
        f"Expected notification_trigger=1 for single ERRORS.md entry in --error-mode, "
        f"got {trigger}. Full result: {json.dumps(result, indent=2)}"
    )


def test_error_mode_uses_threshold_1(temp_workspace):
    """--error-mode sets threshold=1, verified by a 1-entry ERRORS.md triggering."""
    ld = temp_workspace / '.openclaw' / 'workspace' / '.learnings'
    write_error_entry(ld, 'test.error.threshold')

    result = run_distill(learnings_dir=ld, extra_args=['--error-mode'])

    assert result.get('meta', {}).get('threshold') == 1, (
        f"Expected threshold=1 in --error-mode, got {result.get('meta', {}).get('threshold')}. "
        f"Full result: {json.dumps(result, indent=2)}"
    )


def test_learnings_threshold_still_2_in_normal_mode(temp_workspace):
    """Without --error-mode, LEARNINGS.md still requires count>=2 to trigger."""
    ld = temp_workspace / '.openclaw' / 'workspace' / '.learnings'
    # Write one LEARNINGS.md entry with count=1 — should NOT trigger
    write_learning_entry(ld, 'correction')

    result = run_distill(learnings_dir=ld, extra_args=None)

    all_entries = result.get('patterns', []) + result.get('category_fallback', [])
    trigger = get_trigger_for(all_entries, 'LEARNINGS.md', 'correction')

    # In normal mode (threshold=2), count=1 should NOT trigger
    assert trigger == 0, (
        f"Expected notification_trigger=0 for single LEARNINGS.md entry in normal mode, "
        f"got {trigger}. Full result: {json.dumps(result, indent=2)}"
    )


def test_mixed_files_error_mode_only_affects_errors(temp_workspace):
    """With --error-mode, ERRORS.md entry triggers but LEARNINGS.md entry with count=1 does NOT trigger."""
    ld = temp_workspace / '.openclaw' / 'workspace' / '.learnings'
    # Write one entry in each file
    write_error_entry(ld, 'test.error.mixed')
    write_learning_entry(ld, 'correction')

    result = run_distill(learnings_dir=ld, extra_args=['--error-mode'])

    all_entries = result.get('patterns', []) + result.get('category_fallback', [])

    error_trigger = get_trigger_for(all_entries, 'ERRORS.md', 'test.error.mixed')
    learning_trigger = get_trigger_for(all_entries, 'LEARNINGS.md', 'correction')

    assert error_trigger == 1, (
        f"Expected ERRORS.md entry to trigger (notification_trigger=1), got {error_trigger}. "
        f"Full result: {json.dumps(result, indent=2)}"
    )
    assert learning_trigger == 0, (
        f"Expected LEARNINGS.md entry NOT to trigger in --error-mode (notification_trigger=0), "
        f"got {learning_trigger}. Full result: {json.dumps(result, indent=2)}"
    )


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
