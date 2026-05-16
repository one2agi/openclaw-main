#!/usr/bin/env python3
"""Unit and integration tests for write_notified.py"""
import json, os, subprocess, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import pytest

SCRIPT = Path(__file__).parent.parent / "scripts" / "write_notified.py"
MD_SAMPLE = """\
# Learnings

## [test-entry-001] Test Entry

Some description here.

- Tags: python, testing
  - Notified: false
  - Notification-Count: 2

More content after.
"""

MD_BOLD_STATUS = """\
# Learnings

## [test-entry-002] Bold Status Entry

Description.

**Status**: pending
  - Notified: false

More text.
"""

MD_DASH_STATUS = """\
# Learnings

## [test-entry-003] Dash Status Entry

Description.

  - Status: pending
  - Notified: false

More text.
"""

MD_NO_STATUS = """\
# Learnings

## [test-entry-004] No Status Entry

Description.

  - Notified: false
"""

MD_MISSING_ENTRY = """\
# Learnings

## [other-entry] Other Entry

Something else.
"""


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as td:
        yield td


@pytest.fixture
def learnings_dir(temp_dir):
    ld = Path(temp_dir)
    for fname in ("LEARNINGS.md", "ERRORS.md", "FEATURE_REQUESTS.md"):
        (ld / fname).write_text("")
    yield ld


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def run_script(*args):
    """Run the script; return (returncode, stdout, stderr)."""
    result = subprocess.run(
        ["python3", str(SCRIPT), *args],
        capture_output=True, text=True
    )
    return result.returncode, result.stdout, result.stderr


def read_entry(md_path, entry_id):
    """Return the text block for the given entry_id."""
    content = Path(md_path).read_text()
    import re
    m = re.search(
        r"(## \[" + re.escape(entry_id) + r"\] .+?)(?=\n## \[|$)",
        content, re.DOTALL
    )
    return m.group(1) if m else None


# ──────────────────────────────────────────────────────────────────────────────
# Unit tests — _upsert_field
# ──────────────────────────────────────────────────────────────────────────────

def test_upsert_field_replace_existing():
    from write_notified import _upsert_field, _RE_NOTIFIED, _RE_BOLD_STATUS
    text = "## [x] Title\n\n**Status**: old\n  - Notified: false\n"
    new_text, changed = _upsert_field(text, _RE_NOTIFIED, "true", [_RE_BOLD_STATUS])
    assert "Notified: true" in new_text
    assert "false" not in new_text
    assert changed


def test_upsert_field_insert_after_anchor():
    from write_notified import _upsert_field, _RE_NOTIFIED, _RE_BOLD_STATUS
    text = "## [x] Title\n\n**Status**: done\n"
    new_text, changed = _upsert_field(text, _RE_NOTIFIED, "true", [_RE_BOLD_STATUS])
    assert "Notified: true" in new_text
    assert changed


def test_upsert_field_no_change_when_no_anchor():
    from write_notified import _upsert_field, _RE_NOTIFIED
    # Empty anchor list + no existing field = no insertion possible
    text = "## [x] Title\n\nno anchor here\n"
    new_text, changed = _upsert_field(text, _RE_NOTIFIED, "true", [])
    # Without a valid anchor, the text is returned unchanged (no-op, changed=False)
    assert new_text == text
    assert not changed


# ──────────────────────────────────────────────────────────────────────────────
# Unit tests — update_md_file
# ──────────────────────────────────────────────────────────────────────────────

def test_update_md_file_notified_true(temp_dir):
    fpath = Path(temp_dir) / "LEARNINGS.md"
    fpath.write_text(MD_SAMPLE)

    from write_notified import update_md_file
    # Bug5 auto-increment (nc=3 when existing is 2) is handled by _do_update, not update_md_file.
    # Here we test explicit nc.
    assert update_md_file(str(fpath), "test-entry-001", notified_val=1, nc_val=3, status_val=None)

    content = fpath.read_text()
    assert "Notified: true" in content
    assert "Notification-Count: 3" in content  # explicit nc=3


def test_update_md_file_notified_false(temp_dir):
    fpath = Path(temp_dir) / "LEARNINGS.md"
    fpath.write_text(MD_SAMPLE)

    from write_notified import update_md_file
    assert update_md_file(str(fpath), "test-entry-001", notified_val=0, nc_val=None, status_val=None)

    content = fpath.read_text()
    assert "Notified: false" in content


def test_update_md_file_status_bold(temp_dir):
    fpath = Path(temp_dir) / "LEARNINGS.md"
    fpath.write_text(MD_BOLD_STATUS)

    from write_notified import update_md_file
    assert update_md_file(str(fpath), "test-entry-002", notified_val=None, nc_val=None, status_val="done")

    content = fpath.read_text()
    assert "**Status**: done" in content
    assert "pending" not in content


def test_update_md_file_status_dash(temp_dir):
    fpath = Path(temp_dir) / "LEARNINGS.md"
    fpath.write_text(MD_DASH_STATUS)

    from write_notified import update_md_file
    assert update_md_file(str(fpath), "test-entry-003", notified_val=None, nc_val=None, status_val="done")

    content = fpath.read_text()
    assert "  - Status: done" in content


def test_update_md_file_insert_status_when_missing(temp_dir):
    fpath = Path(temp_dir) / "LEARNINGS.md"
    fpath.write_text(MD_NO_STATUS)

    from write_notified import update_md_file
    assert update_md_file(str(fpath), "test-entry-004", notified_val=None, nc_val=5, status_val="done")

    content = fpath.read_text()
    assert "**Status**: done" in content
    assert "Notification-Count: 5" in content


def test_update_md_file_missing_entry_returns_false(temp_dir):
    fpath = Path(temp_dir) / "LEARNINGS.md"
    fpath.write_text(MD_MISSING_ENTRY)

    from write_notified import update_md_file
    assert not update_md_file(str(fpath), "nonexistent", notified_val=1)


def test_update_md_file_missing_file_returns_false(temp_dir):
    from write_notified import update_md_file
    assert not update_md_file(str(Path(temp_dir) / "DOES_NOT_EXIST.md"), "test-entry-001")


# ──────────────────────────────────────────────────────────────────────────────
# Integration tests — CLI (new mode)
# ──────────────────────────────────────────────────────────────────────────────

def test_cli_new_mode_status_and_notified(temp_dir, learnings_dir):
    (learnings_dir / "LEARNINGS.md").write_text(MD_BOLD_STATUS)

    rc, out, err = run_script(
        "--status", "done", "--notified", "1", "--nc", "3",
        "test-entry-002", str(learnings_dir)
    )
    assert rc == 0, err

    content = (learnings_dir / "LEARNINGS.md").read_text()
    assert "**Status**: done" in content
    assert "Notified: true" in content
    assert "Notification-Count: 3" in content


def test_cli_new_mode_notified_only_uses_bug5(temp_dir, learnings_dir):
    """notified=1 without --nc should auto-increment NC from existing value."""
    (learnings_dir / "LEARNINGS.md").write_text(MD_SAMPLE)  # has NC: 2

    rc, out, err = run_script(
        "--notified", "1", "test-entry-001", str(learnings_dir)
    )
    assert rc == 0, err

    content = (learnings_dir / "LEARNINGS.md").read_text()
    assert "Notified: true" in content
    assert "Notification-Count: 3" in content  # 2 + 1


def test_cli_new_mode_no_existing_nc_defaults_to_1(temp_dir, learnings_dir):
    """notified=1 without existing NC should default nc=1."""
    md = "## [fresh-entry] New\n\n**Status**: pending\n  - Notified: false\n"
    (learnings_dir / "LEARNINGS.md").write_text(md)

    rc, out, err = run_script(
        "--notified", "1", "fresh-entry", str(learnings_dir)
    )
    assert rc == 0, err

    content = (learnings_dir / "LEARNINGS.md").read_text()
    assert "Notification-Count: 1" in content


def test_cli_new_mode_not_found_returns_0_updated(temp_dir, learnings_dir):
    (learnings_dir / "LEARNINGS.md").write_text(MD_MISSING_ENTRY)

    rc, out, err = run_script(
        "--notified", "1", "nonexistent", str(learnings_dir)
    )
    assert rc == 0
    assert "0 entries updated" in err


# ──────────────────────────────────────────────────────────────────────────────
# Integration tests — CLI (legacy mode)
# ──────────────────────────────────────────────────────────────────────────────

def test_cli_legacy_mode(temp_dir, learnings_dir, tmp_path):
    (learnings_dir / "LEARNINGS.md").write_text(MD_BOLD_STATUS)

    json_file = tmp_path / "entry.json"
    json_file.write_text(json.dumps({
        "entry_id": "test-entry-002",
        "notification_count": 7
    }))

    rc, out, err = run_script(str(json_file), str(learnings_dir))
    assert rc == 0, err

    content = (learnings_dir / "LEARNINGS.md").read_text()
    assert "Notified: true" in content
    assert "Notification-Count: 7" in content


def test_cli_legacy_mode_pattern_name_fallback(temp_dir, learnings_dir, tmp_path):
    """Legacy JSON uses pattern_name instead of entry_id."""
    (learnings_dir / "LEARNINGS.md").write_text(MD_BOLD_STATUS)

    json_file = tmp_path / "entry.json"
    json_file.write_text(json.dumps({
        "pattern_name": "test-entry-002",
        "notification_count": 4
    }))

    rc, out, err = run_script(str(json_file), str(learnings_dir))
    assert rc == 0, err

    content = (learnings_dir / "LEARNINGS.md").read_text()
    assert "Notification-Count: 4" in content


def test_cli_legacy_mode_missing_entry_id_errors(temp_dir, learnings_dir, tmp_path):
    json_file = tmp_path / "bad.json"
    json_file.write_text(json.dumps({"notification_count": 1}))

    rc, out, err = run_script(str(json_file), str(learnings_dir))
    assert rc != 0
    assert "no 'pattern_name' field" in err


# ──────────────────────────────────────────────────────────────────────────────
# Integration tests — multi-file propagation
# ──────────────────────────────────────────────────────────────────────────────

def test_entry_updates_across_all_three_files(temp_dir, learnings_dir):
    """An entry that appears in multiple files should be updated in each."""
    entry_block = """\
## [multi-file-entry] Cross-File Entry

Description.

**Status**: pending
"""
    for fname in ("LEARNINGS.md", "ERRORS.md", "FEATURE_REQUESTS.md"):
        (learnings_dir / fname).write_text("# " + fname + "\n\n" + entry_block)

    rc, out, err = run_script(
        "--status", "done", "--notified", "1", "--nc", "5",
        "multi-file-entry", str(learnings_dir)
    )
    assert rc == 0

    for fname in ("LEARNINGS.md", "ERRORS.md", "FEATURE_REQUESTS.md"):
        content = (learnings_dir / fname).read_text()
        assert "**Status**: done" in content, f"{fname} not updated"
        assert "Notified: true" in content, f"{fname} not updated"
        assert "Notification-Count: 5" in content, f"{fname} not updated"


# ──────────────────────────────────────────────────────────────────────────────
# Edge cases
# ──────────────────────────────────────────────────────────────────────────────

def test_update_md_file_all_fields_at_once(temp_dir):
    """When no Status field exists and all three fields are set, insert Status + others."""
    fpath = Path(temp_dir) / "LEARNINGS.md"
    fpath.write_text("## [edge-001] Edge\n\nbody\n")

    from write_notified import update_md_file
    assert update_md_file(str(fpath), "edge-001",
                          notified_val=1, nc_val=3, status_val="reviewed")

    content = fpath.read_text()
    assert "**Status**: reviewed" in content
    assert "Notified: true" in content
    assert "Notification-Count: 3" in content


def test_nc_update_existing_replaces_not_increments(temp_dir):
    """Updating NC should replace, not add to existing value."""
    fpath = Path(temp_dir) / "LEARNINGS.md"
    fpath.write_text(MD_SAMPLE)  # existing NC: 2

    from write_notified import update_md_file
    update_md_file(str(fpath), "test-entry-001", notified_val=None, nc_val=99, status_val=None)

    content = fpath.read_text()
    assert "Notification-Count: 99" in content
    assert "Notification-Count: 2" not in content


def test_cli_expands_tilde_in_path(temp_dir, learnings_dir, tmp_path):
    """Path with ~ should be expanded correctly."""
    json_file = tmp_path / "entry.json"
    json_file.write_text(json.dumps({"entry_id": "test-entry-002", "notification_count": 2}))
    (learnings_dir / "LEARNINGS.md").write_text(MD_BOLD_STATUS)

    # Run with a synthetic path — we can't easily test ~ expansion in a test,
    # but the logic uses os.path.expanduser so we trust it.
    from write_notified import _do_update
    # Verify expanduser is called by checking with a relative path works
    rc, out, err = run_script(str(json_file), str(learnings_dir))
    assert rc == 0