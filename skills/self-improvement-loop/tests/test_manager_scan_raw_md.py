"""Test that scan output includes raw_md field for each entry."""
import subprocess, json, tempfile, os

def test_scan_includes_raw_md():
    """scan output should include raw_md field for each entry"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create minimal learnings dir
        learnings = os.path.join(tmpdir, '.learnings')
        os.makedirs(learnings)
        # Write a test entry
        with open(os.path.join(learnings, 'learnings.jsonl'), 'w') as f:
            f.write(json.dumps({
                'id': 'test-001',
                'pattern_key': 'test-pattern',
                'what_happened': 'Something happened',
                'root_cause': 'Root cause here',
                'how_to_avoid': 'Avoid this way',
                'status': 'pending',
                'notified': False,
                'notification_count': 0
            }) + '\n')

        result = subprocess.run(
            ['python3', 'scripts/manager.py', '--learnings-dir', learnings, 'scan'],
            capture_output=True, text=True
        )
        data = json.loads(result.stdout)
        entry = data['patterns'][0]['entries'][0]

        assert 'raw_md' in entry, f"raw_md missing: {entry.keys()}"
        assert '### What Happened' in entry['raw_md']
        assert '### Root Cause' in entry['raw_md']
        assert '### How To Avoid' in entry['raw_md']
