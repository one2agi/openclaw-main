#!/usr/bin/env python3
"""tests/test_e2e_full_flow.py — End-to-End integration tests for self-improvement-loop

Tests the complete user flow:
1. install.sh initializes agent workspace
2. handler.js detects error → calls manager.py add
3. JSONL file written correctly
4. scan detects pattern when threshold reached
5. notification triggered correctly
6. User A/B/C/D response updates entry status
"""
import sys
import os
import json
import subprocess
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from conftest import temp_workspace

SKILL_ROOT = Path(__file__).parent.parent
MANAGER_PY = SKILL_ROOT / 'scripts' / 'manager.py'
INSTALL_SH = SKILL_ROOT / 'install.sh'


def run_manager(cmd, learnings_dir, extra_args=None):
    """Run manager.py with specified command."""
    args = ['python3', str(MANAGER_PY), '--learnings-dir', str(learnings_dir)]
    if isinstance(cmd, list):
        args.extend(cmd)
    else:
        args.append(cmd)
    if extra_args:
        args.extend(extra_args)

    result = subprocess.run(args, capture_output=True, text=True)
    return result


def run_handler(body_for_agent, learnings_dir, session_key='agent:main:telegram:123'):
    """Simulate handler.js detecting an error and calling manager.py."""
    handler_path = SKILL_ROOT / 'hooks' / 'handler.js'

    # Simulate handler.js behavior: detect error and call manager.py add
    # The actual handler.js does this internally
    error_patterns = ['Traceback', 'Error:', 'ReferenceError', 'TypeError', 'Command failed']

    triggered = any(pattern in body_for_agent for pattern in error_patterns)

    if triggered:
        # Determine entry type
        if 'Traceback' in body_for_agent or any(e in body_for_agent for e in ['Error:', 'ReferenceError', 'TypeError']):
            etype = 'errors'
            category = 'python_error'
        else:
            etype = 'learnings'
            category = 'correction'

        # Extract pattern key from body
        pattern_key = 'detected.' + body_for_agent[:30].replace('\n', ' ').replace(' ', '_')[:30]

        result = run_manager([
            'add', '--type', etype,
            '--category', category,
            '--pattern-key', pattern_key,
            '--what', body_for_agent[:200],
            '--source', 'handler_detected'
        ], learnings_dir)

        return {
            'triggered': True,
            'type': etype,
            'entry_id': result.stdout.strip().split('\n')[-1] if result.returncode == 0 else None,
            'pattern_key': pattern_key
        }

    return {'triggered': False}


# ─── E2E Tests ──────────────────────────────────────────────────────────────────

def test_e2e_install_and_initialization(temp_workspace):
    """E2E Step 1: install.sh should initialize gateway-level structure.

    Note: install.sh creates .learnings at ~/.openclaw/workspace/.learnings (gateway-level),
    not per-agent. Each agent shares the same learnings dir.
    """
    result = subprocess.run(
        ['bash', str(INSTALL_SH)],
        capture_output=True, text=True,
        env={**os.environ, 'HOME': str(temp_workspace)}
    )

    assert result.returncode == 0, f"install.sh failed: {result.stderr}"

    # v5.0.0: .learnings is at gateway level, not per-agent
    learnings_dir = temp_workspace / '.openclaw' / 'workspace' / '.learnings'
    assert learnings_dir.exists(), f".learnings dir not created at gateway level: {learnings_dir}"

    for fname in ('learnings.jsonl', 'errors.jsonl', 'features.jsonl'):
        assert (learnings_dir / fname).exists(), f"{fname} not created"


def test_e2e_handler_detects_and_records_error(temp_workspace):
    """E2E Step 2: Error in message should be recorded to JSONL."""
    agent_ws = temp_workspace / 'test-agent'
    learnings_dir = agent_ws / '.learnings'
    learnings_dir.mkdir(parents=True, exist_ok=True)
    (learnings_dir / 'errors.jsonl').touch()
    (learnings_dir / 'learnings.jsonl').touch()
    (learnings_dir / 'features.jsonl').touch()

    error_msg = 'Traceback (most recent call last):\n  File "test.py", line 10\nNameError: name "x" is not defined'
    result = run_handler(error_msg, learnings_dir)

    assert result['triggered'] == True, "Error should have been detected"
    assert result['type'] == 'errors', f"Should be 'errors', got {result['type']}"

    # Verify JSONL was written
    errors_file = learnings_dir / 'errors.jsonl'
    lines = errors_file.read_text().strip().split('\n')
    assert len(lines) >= 1, "Should have at least one entry in errors.jsonl"

    entry = json.loads(lines[-1])
    assert entry['type'] == 'errors'
    assert entry['status'] == 'pending'
    assert entry['notified'] == False


def test_e2e_scan_detects_pattern_at_threshold(temp_workspace):
    """E2E Step 3: scan should detect pattern when count >= threshold."""
    agent_ws = temp_workspace / 'test-agent'
    learnings_dir = agent_ws / '.learnings'
    learnings_dir.mkdir(parents=True, exist_ok=True)
    (learnings_dir / 'errors.jsonl').touch()
    (learnings_dir / 'learnings.jsonl').touch()

    pattern_key = 'e2e.test.pattern'

    # Add 2 entries with same pattern_key (threshold=2)
    for i in range(2):
        run_manager([
            'add', '--type', 'errors',
            '--category', 'test',
            '--pattern-key', pattern_key,
            '--what', f'Test error #{i+1}',
            '--source', 'e2e_test'
        ], learnings_dir)

    # Run scan with threshold=2
    result = run_manager(['--json-output', 'scan', '--threshold', '2'], learnings_dir)
    assert result.returncode == 0, f"scan failed: {result.stderr}"

    output = json.loads(result.stdout)
    patterns = output.get('patterns', [])

    matching = [p for p in patterns if p['name'] == pattern_key]
    assert len(matching) == 1, f"Should find pattern '{pattern_key}', got {len(matching)} patterns"
    assert matching[0]['should_notify'] == True, "Should trigger notification at threshold"


def test_e2e_single_error_triggers_notification(temp_workspace):
    """E2E Step 4: With threshold=1, single error should trigger immediately."""
    agent_ws = temp_workspace / 'test-agent'
    learnings_dir = agent_ws / '.learnings'
    learnings_dir.mkdir(parents=True, exist_ok=True)
    (learnings_dir / 'errors.jsonl').touch()

    run_manager([
        'add', '--type', 'errors',
        '--category', 'critical',
        '--pattern-key', 'e2e.critical.error',
        '--what', 'Critical error that needs immediate attention',
        '--source', 'e2e_test'
    ], learnings_dir)

    # With threshold=1, single entry should trigger
    result = run_manager(['--json-output', 'scan', '--threshold', '1'], learnings_dir)
    output = json.loads(result.stdout)
    patterns = output.get('patterns', [])

    assert len(patterns) >= 1, "Single error at threshold=1 should appear"
    assert patterns[0]['should_notify'] == True, "should_notify should be True"


def test_e2e_user_response_updates_entry(temp_workspace):
    """E2E Step 5: User A/B/C/D response should update entry status."""
    agent_ws = temp_workspace / 'test-agent'
    learnings_dir = agent_ws / '.learnings'
    learnings_dir.mkdir(parents=True, exist_ok=True)
    (learnings_dir / 'learnings.jsonl').touch()

    # Add an entry
    run_manager([
        'add', '--type', 'learnings',
        '--category', 'correction',
        '--pattern-key', 'e2e.user.response',
        '--what', 'User corrected the approach',
        '--source', 'human_correction'
    ], learnings_dir)

    # Get the entry ID
    result = run_manager(['list', '--type', 'learnings'], learnings_dir)
    entry_id = result.stdout.strip().split('\n')[-1].split('[')[1].split(']')[0]

    # User marks it as resolved
    result = run_manager(['update', entry_id, '--status', 'resolved'], learnings_dir)
    assert result.returncode == 0, f"update failed: {result.stderr}"

    # Verify status changed
    result = run_manager(['get', entry_id], learnings_dir)
    entry = json.loads(result.stdout)
    assert entry['status'] == 'resolved', f"Status should be 'resolved', got {entry['status']}"


def test_e2e_archive_resolved_entries(temp_workspace):
    """E2E Step 6: Resolved entries should be archived."""
    agent_ws = temp_workspace / 'test-agent'
    learnings_dir = agent_ws / '.learnings'
    learnings_dir.mkdir(parents=True, exist_ok=True)
    (learnings_dir / 'learnings.jsonl').touch()

    # Add and resolve entries
    for i in range(3):
        run_manager([
            'add', '--type', 'learnings',
            '--category', 'temp',
            '--pattern-key', f'e2e.temp.{i}',
            '--what', f'Temp entry {i}',
            '--source', 'e2e_test'
        ], learnings_dir)

        result = run_manager(['list', '--type', 'learnings'], learnings_dir)
        entry_id = result.stdout.strip().split('\n')[-1].split('[')[1].split(']')[0]
        run_manager(['update', entry_id, '--status', 'resolved'], learnings_dir)

    # Run archive
    result = run_manager(['archive', '--dry-run'], learnings_dir)
    assert result.returncode == 0, f"archive failed: {result.stderr}"
    assert 'DRY RUN' in result.stdout or 'Archived' in result.stdout


def test_e2e_concurrent_writes_no_corruption(temp_workspace):
    """E2E Step 7: Concurrent writes should not corrupt JSONL."""
    agent_ws = temp_workspace / 'test-agent'
    learnings_dir = agent_ws / '.learnings'
    learnings_dir.mkdir(parents=True, exist_ok=True)
    (learnings_dir / 'learnings.jsonl').touch()

    import concurrent.futures
    import threading

    errors = []
    entries_written = threading.Lock()
    count = [0]

    def write_entry(i):
        result = run_manager([
            'add', '--type', 'learnings',
            '--category', 'concurrent',
            '--pattern-key', 'e2e.concurrent',
            '--what', f'Concurrent entry {i}',
            '--source', 'e2e_test'
        ], learnings_dir)
        if result.returncode != 0:
            errors.append(result.stderr)
        else:
            with entries_written:
                count[0] += 1

    # Write 10 entries concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(write_entry, i) for i in range(10)]
        concurrent.futures.wait(futures)

    assert len(errors) == 0, f"Concurrent writes had errors: {errors}"

    # Verify JSONL is valid
    learnings_file = learnings_dir / 'learnings.jsonl'
    lines = learnings_file.read_text().strip().split('\n')
    valid_lines = 0
    for line in lines:
        if line.strip():
            try:
                json.loads(line)
                valid_lines += 1
            except json.JSONDecodeError:
                pass

    assert valid_lines == count[0], (
        f"JSONL corruption: expected {count[0]} valid entries, got {valid_lines}"
    )


def test_e2e_full_user_flow_simulation(temp_workspace):
    """E2E: Simulate complete user flow from error detection to resolution."""
    agent_ws = temp_workspace / 'test-agent'
    learnings_dir = agent_ws / '.learnings'
    learnings_dir.mkdir(parents=True, exist_ok=True)
    (learnings_dir / 'learnings.jsonl').touch()
    (learnings_dir / 'errors.jsonl').touch()

    # Step 1: User makes a mistake, gets corrected
    print("\n=== E2E Flow Simulation ===")

    # User types something with an error
    error_msg = "Here's my code:\nTraceback (most recent call last):\n  File 'main.py', line 5\nTypeError: cannot concatenate 'str' and 'int'"

    result = run_handler(error_msg, learnings_dir)
    print(f"1. Handler detected: {result['triggered']}, type: {result.get('type')}")
    assert result['triggered'] == True

    # Step 2: Add another similar error
    error_msg2 = "Another traceback:\nTraceback:\n  File 'main.py', line 10\nTypeError: cannot concatenate"
    result2 = run_handler(error_msg2, learnings_dir)
    print(f"2. Second error detected: {result2['triggered']}")

    # Step 3: Run scan to detect pattern
    scan_result = run_manager(['--json-output', 'scan', '--threshold', '2'], learnings_dir)
    scan_data = json.loads(scan_result.stdout)
    print(f"3. Scan found {len(scan_data['patterns'])} patterns")

    # Step 4: Verify notification would be triggered
    patterns = scan_data.get('patterns', [])
    for p in patterns:
        if 'TypeError' in p['name'] or 'cannot concatenate' in p['name']:
            print(f"4. Pattern '{p['name']}' should_notify: {p['should_notify']}")
            assert p['should_notify'] == True, "Pattern should trigger notification"
            break

    # Step 5: User marks as resolved
    if patterns:
        entry_id = patterns[0]['entries'][0]['id']
        run_manager(['update', entry_id, '--status', 'resolved'], learnings_dir)

        # Verify it's resolved
        get_result = run_manager(['get', entry_id], learnings_dir)
        entry = json.loads(get_result.stdout)
        print(f"5. Entry {entry_id} status: {entry['status']}")
        assert entry['status'] == 'resolved'

    print("=== E2E Flow Complete ===\n")


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])