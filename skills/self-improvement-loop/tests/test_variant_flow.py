#!/usr/bin/env python3
"""tests/test_variant_flow.py — TDD: variant flow data model extension

Tests the new JSONL fields for variant generation and execution tracking.
"""
import sys, os, json, subprocess, tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

SKILL_ROOT = Path(__file__).parent.parent
MANAGER_PY = SKILL_ROOT / 'scripts' / 'manager.py'


def run_manager(cmd, learnings_dir, extra_args=None):
    args = ['python3', str(MANAGER_PY), '--learnings-dir', str(learnings_dir)]
    if isinstance(cmd, list):
        args.extend(cmd)
    else:
        args.append(cmd)
    if extra_args:
        args.extend(extra_args)
    result = subprocess.run(args, capture_output=True, text=True)
    return result


def create_temp_workspace():
    """Create temp workspace (not a fixture, for direct use)."""
    td = Path(tempfile.mkdtemp())
    ld = td / '.openclaw' / 'workspace' / '.learnings'
    ld.mkdir(parents=True, exist_ok=True)
    for fname in ['learnings.jsonl', 'errors.jsonl', 'features.jsonl']:
        (ld / fname).touch()
    return td, ld


def test_add_entry_with_variants():
    """Entry with variants_generated should be stored correctly."""
    td, ld = create_temp_workspace()

    entry = {
        "type": "learnings",
        "category": "correction",
        "pattern_key": "test.pattern",
        "what_happened": "Test error occurred",
        "root_cause": "Missing type check",
        "how_to_avoid": "Add type validation",
        "variants_generated": [
            {"id": "A", "description": "保守方案", "risk": "low"},
            {"id": "B", "description": "激进方案", "risk": "high"}
        ]
    }

    tmp_file = '/tmp/test_variants.json'
    with open(tmp_file, 'w') as f:
        json.dump(entry, f)

    result = run_manager(['add', '--json', tmp_file], ld)
    assert result.returncode == 0, f"add failed: {result.stderr}"

    # Get the entry ID
    list_result = run_manager(['list', '--type', 'learnings'], ld)
    lines = [l for l in list_result.stdout.strip().split('\n') if l]
    entry_id = lines[-1].split('[')[1].split(']')[0]

    # Retrieve and verify
    get_result = run_manager(['get', entry_id], ld)
    retrieved = json.loads(get_result.stdout)

    assert 'variants_generated' in retrieved, "variants_generated not stored"
    assert len(retrieved['variants_generated']) == 2, "Wrong variant count"
    assert retrieved['variants_generated'][0]['id'] == 'A'


def test_add_entry_with_full_trace_fields():
    """Entry should support selected_variant, execution_trace, execution_result."""
    td, ld = create_temp_workspace()

    entry = {
        "type": "learnings",
        "category": "correction",
        "pattern_key": "test.trace",
        "what_happened": "Test trace flow",
        "root_cause": "N/A",
        "how_to_avoid": "N/A",
        "selected_variant": "B",
        "execution_trace": ["Step 1", "Step 2", "Step 3"],
        "execution_result": "success"
    }

    tmp_file = '/tmp/test_trace.json'
    with open(tmp_file, 'w') as f:
        json.dump(entry, f)

    result = run_manager(['add', '--json', tmp_file], ld)
    assert result.returncode == 0

    # Get ID and verify
    list_result = run_manager(['list', '--type', 'learnings'], ld)
    lines = [l for l in list_result.stdout.strip().split('\n') if l]
    entry_id = lines[-1].split('[')[1].split(']')[0]

    get_result = run_manager(['get', entry_id], ld)
    retrieved = json.loads(get_result.stdout)

    assert retrieved.get('selected_variant') == 'B'
    assert retrieved.get('execution_trace') == ["Step 1", "Step 2", "Step 3"]
    assert retrieved.get('execution_result') == 'success'


def test_update_entry_status():
    """Should be able to update entry status."""
    td, ld = create_temp_workspace()

    # Add simple entry
    run_manager([
        'add', '--type', 'learnings',
        '--category', 'test',
        '--pattern-key', 'test.update',
        '--what', 'Test update',
        '--source', 'test'
    ], ld)

    # Get ID
    list_result = run_manager(['list', '--type', 'learnings'], ld)
    lines = [l for l in list_result.stdout.strip().split('\n') if l]
    entry_id = lines[-1].split('[')[1].split(']')[0]

    # Update status
    update_result = run_manager(['update', entry_id, '--status', 'resolved'], ld)
    assert update_result.returncode == 0

    # Verify
    get_result = run_manager(['get', entry_id], ld)
    retrieved = json.loads(get_result.stdout)
    assert retrieved.get('status') == 'resolved'


def test_list_shows_variants_entry():
    """list command should show entry when variants are present."""
    td, ld = create_temp_workspace()

    entry = {
        "type": "learnings",
        "category": "correction",
        "pattern_key": "test.list",
        "what_happened": "Test list variants",
        "variants_generated": [
            {"id": "A", "description": "方案A"},
            {"id": "B", "description": "方案B"},
            {"id": "C", "description": "方案C"}
        ]
    }
    tmp_file = '/tmp/test_list.json'
    with open(tmp_file, 'w') as f:
        json.dump(entry, f)

    run_manager(['add', '--json', tmp_file], ld)

    # Get entry directly to verify variants
    list_result = run_manager(['list', '--type', 'learnings'], ld)
    lines = [l for l in list_result.stdout.strip().split('\n') if l]
    entry_id = lines[-1].split('[')[1].split(']')[0]

    get_result = run_manager(['get', entry_id], ld)
    retrieved = json.loads(get_result.stdout)

    # Entry should be retrievable with variants
    assert retrieved.get('pattern_key') == 'test.list'
    assert len(retrieved.get('variants_generated', [])) == 3


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])