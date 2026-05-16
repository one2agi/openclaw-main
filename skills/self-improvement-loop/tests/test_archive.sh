#!/bin/bash
# Unit tests for archive.sh
# Run: bash tests/test_archive.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ARCHIVE_SH="$SCRIPT_DIR/../scripts/archive.sh"
TEST_TMPDIR=""
TESTS_PASSED=0
TESTS_FAILED=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_pass() { echo -e "${GREEN}[PASS]${NC} $1"; ((TESTS_PASSED++)) || true; }
log_fail() { echo -e "${RED}[FAIL]${NC} $1"; ((TESTS_FAILED++)) || true; }
log_info() { echo -e "${YELLOW}[INFO]${NC} $1"; }

setup() {
    TEST_TMPDIR=$(mktemp -d)
    mkdir -p "$TEST_TMPDIR/.learnings/archive"
    mkdir -p "$TEST_TMPDIR/.learnings/.pending_notifications"
    export HOME="$TEST_TMPDIR"  # override HOME for test
}

teardown() {
    if [ -n "$TEST_TMPDIR" ] && [ -d "$TEST_TMPDIR" ]; then
        rm -rf "$TEST_TMPDIR"
    fi
}

# ── Source the script functions (isolate for testing) ─────────
source_functions() {
    # Re-source with test HOME
    WORKSPACE="$TEST_TMPDIR/.openclaw/workspace"
    LEARNINGS_DIR="$WORKSPACE/.learnings"
    ARCHIVE_DIR="$LEARNINGS_DIR/archive"
    mkdir -p "$ARCHIVE_DIR"
}

# ── Helper functions from archive.sh extracted ─────────────────
source_tag() {
    case "$1" in
        *LEARNINGS*)       echo "LEARNINGS" ;;
        *ERRORS*)          echo "ERRORS" ;;
        *FEATURE*)         echo "FEATURE" ;;
        *)                 echo "UNKNOWN" ;;
    esac
}

normalize_outcome() {
    case "$1" in
        promoted)  echo "promoted" ;;
        resolved)  echo "resolved" ;;
        *)         echo "resolved" ;;
    esac
}

json_escape() {
    python3 -c "import sys,json; s=sys.stdin.read(); print(json.dumps(s)[1:-1])"
}

extract_field() {
    local entry="$1"
    local field="$2"
    local val
    val=$(echo "$entry" | awk -v f="### $field" 'index($0,f)==1{getline; print}')
    [ -z "$val" ] && val=$(echo "$entry" | awk -v f="$field" 'index($0,f)==1{ sub(/.*:[[:space:]]*/,""); print }')
    echo "$val" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//'
}

extract_meta() {
    local entry="$1"
    local key="$2"
    local val
    val=$(echo "$entry" | grep "^[[:space:]]*- $key:" | sed 's/.*:[[:space:]]*//')
    [ -z "$val" ] && val=$(echo "$entry" | grep "^[[:space:]]*\*\*$key" | sed 's/.*\*://')
    echo "$val" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//'
}

# ── TEST: source_tag ──────────────────────────────────────────
test_source_tag() {
    log_info "Testing source_tag()"

    result=$(source_tag "/path/to/LEARNINGS.md")
    [ "$result" = "LEARNINGS" ] && log_pass "source_tag: LEARNINGS.md → LEARNINGS" || log_fail "source_tag: LEARNINGS.md → LEARNINGS"

    result=$(source_tag "/path/to/ERRORS.md")
    [ "$result" = "ERRORS" ] && log_pass "source_tag: ERRORS.md → ERRORS" || log_fail "source_tag: ERRORS.md → ERRORS"

    result=$(source_tag "/path/to/FEATURE_REQUESTS.md")
    [ "$result" = "FEATURE" ] && log_pass "source_tag: FEATURE_REQUESTS.md → FEATURE" || log_fail "source_tag: FEATURE_REQUESTS.md → FEATURE"

    result=$(source_tag "/path/to/OTHER.md")
    [ "$result" = "UNKNOWN" ] && log_pass "source_tag: OTHER.md → UNKNOWN" || log_fail "source_tag: OTHER.md → UNKNOWN"
}

# ── TEST: normalize_outcome ───────────────────────────────────
test_normalize_outcome() {
    log_info "Testing normalize_outcome()"

    result=$(normalize_outcome "promoted")
    [ "$result" = "promoted" ] && log_pass "normalize_outcome: promoted → promoted" || log_fail "normalize_outcome: promoted → promoted"

    result=$(normalize_outcome "resolved")
    [ "$result" = "resolved" ] && log_pass "normalize_outcome: resolved → resolved" || log_fail "normalize_outcome: resolved → resolved"

    result=$(normalize_outcome "anything_else")
    [ "$result" = "resolved" ] && log_pass "normalize_outcome: unknown → resolved" || log_fail "normalize_outcome: unknown → resolved"
}

# ── TEST: json_escape ──────────────────────────────────────────
test_json_escape() {
    log_info "Testing json_escape()"

    # echo adds trailing newline - json_escape properly escapes it as \n
    result=$(echo 'hello' | json_escape)
    [ "$result" = "hello\n" ] && log_pass "json_escape: simple string (echo adds newline)" || log_fail "json_escape: simple string (got: $result)"

    # printf preserves exact characters
    result=$(printf 'line1\nline2' | json_escape)
    [ "$result" = "line1\\nline2" ] && log_pass "json_escape: newline escaped" || log_fail "json_escape: newline escaped (got: $result)"

    result=$(printf 'say "hello"' | json_escape)
    [ "$result" = "say \\\"hello\\\"" ] && log_pass "json_escape: quotes escaped" || log_fail "json_escape: quotes escaped (got: $result)"

    result=$(printf 'a\\b' | json_escape)
    [ "$result" = "a\\\\b" ] && log_pass "json_escape: backslash escaped" || log_fail "json_escape: backslash escaped (got: $result)"
}

# ── TEST: extract_field ────────────────────────────────────────
test_extract_field() {
    log_info "Testing extract_field()"

    entry="Some text
### What Happened
This is the summary
More text"

    result=$(extract_field "$entry" "What Happened")
    [ "$result" = "This is the summary" ] && log_pass "extract_field: standard header" || log_fail "extract_field: standard header"

    entry="### Root Cause
Analysis of the bug"
    result=$(extract_field "$entry" "Root Cause")
    [ "$result" = "Analysis of the bug" ] && log_pass "extract_field: Root Cause" || log_fail "extract_field: Root Cause"
}

# ── TEST: extract_meta ─────────────────────────────────────────
test_extract_meta() {
    log_info "Testing extract_meta()"

    entry="## [learning] Title
- Tags: bash, testing
- Pattern-Key: test-pattern"

    result=$(extract_meta "$entry" "Tags")
    [ "$result" = "bash, testing" ] && log_pass "extract_meta: Tags with dash prefix" || log_fail "extract_meta: Tags with dash prefix"

    result=$(extract_meta "$entry" "Pattern-Key")
    [ "$result" = "test-pattern" ] && log_pass "extract_meta: Pattern-Key" || log_fail "extract_meta: Pattern-Key"
}

# ── TEST: process_file with resolved entry ────────────────────
test_process_file_resolved() {
    log_info "Testing process_file() with resolved entries"

    mkdir -p "$LEARNINGS_DIR"

    cat > "$LEARNINGS_DIR/LEARNINGS.md" << 'EOF'
## [bash] Test Entry 1
- Logged: 2024-01-01
- Tags: test

### What Happened
A test happened

### Root Cause
Root cause here

### How To Avoid Next Time
Use tests

**Status**: resolved
EOF

    # Source the script but don't run main logic
    # Instead, manually test process_file logic
    local src_tag="LEARNINGS"
    local TIMESTAMP="2024-01-01T12:00:00+08:00"

    # Call the extract functions directly to verify parsing
    result=$(extract_meta "$(cat "$LEARNINGS_DIR/LEARNINGS.md")" "Tags")
    [ "$result" = "test" ] && log_pass "process_file: extract Tags from MD" || log_fail "process_file: extract Tags from MD"

    result=$(extract_field "$(cat "$LEARNINGS_DIR/LEARNINGS.md")" "What Happened")
    [ "$result" = "A test happened" ] && log_pass "process_file: extract summary from MD" || log_fail "process_file: extract summary from MD"
}

# ── TEST: count archived occurrences ─────────────────────────
test_count_archived_occurrences() {
    log_info "Testing count_archived_occurrences()"

    mkdir -p "$ARCHIVE_DIR"

    # Create test archive JSONL
    echo '{"pattern_key":"test-pattern"}' > "$ARCHIVE_DIR/2024-01.jsonl"
    echo '{"pattern_key":"test-pattern"}' >> "$ARCHIVE_DIR/2024-01.jsonl"
    echo '{"pattern_key":"other-pattern"}' >> "$ARCHIVE_DIR/2024-01.jsonl"

    count_archived_occurrences() {
        local pk="$1"
        [ -z "$pk" ] && echo "1" && return
        local count=0
        for jsonl_file in "$ARCHIVE_DIR"/*.jsonl; do
            [ -f "$jsonl_file" ] || continue
            local result
            result=$(grep -c "pattern_key.*$pk" "$jsonl_file" 2>/dev/null)
            [ -z "$result" ] && result=0
            count=$(( count + result ))
        done
        echo "$(( count + 1 ))"
    }

    result=$(count_archived_occurrences "test-pattern")
    [ "$result" = "3" ] && log_pass "count_archived_occurrences: test-pattern (2+1=3)" || log_fail "count_archived_occurrences: test-pattern (2+1=3), got $result"

    result=$(count_archived_occurrences "other-pattern")
    [ "$result" = "2" ] && log_pass "count_archived_occurrences: other-pattern (1+1=2)" || log_fail "count_archived_occurrences: other-pattern (1+1=2), got $result"

    result=$(count_archived_occurrences "nonexistent")
    [ "$result" = "1" ] && log_pass "count_archived_occurrences: nonexistent (0+1=1)" || log_fail "count_archived_occurrences: nonexistent (0+1=1), got $result"

    result=$(count_archived_occurrences "")
    [ "$result" = "1" ] && log_pass "count_archived_occurrences: empty key → 1" || log_fail "count_archived_occurrences: empty key → 1, got $result"
}

# ── TEST: remove_archived_entries logic ───────────────────────
test_remove_archived_entries() {
    log_info "Testing remove_archived_entries logic"

    cat > "$LEARNINGS_DIR/LEARNINGS.md" << 'EOF'
## [bash] Keep This
- Logged: 2024-01-01

### What Happened
Keep this entry

**Status**: pending

## [python] Archive This
- Logged: 2024-01-02

### What Happened
Archive this entry

**Status**: resolved
EOF

    # Simulate the removal logic
    local tmpfile="$TEST_TMPDIR/temp_md.md"
    local in_entry=false
    local current_status=""
    local entry_lines=""
    local entry_id=""

    while IFS= read -r line; do
        case "$line" in
            "## ["*)
                if $in_entry && [ -n "$entry_id" ]; then
                    case "$current_status" in
                        resolved|promoted) ;;  # skip
                        *) printf '%s\n' "$entry_lines" >> "$tmpfile" ;;
                    esac
                fi
                in_entry=true
                entry_id="$line"
                entry_lines="$line"$'\n'
                current_status=""
                ;;
            *)
                if $in_entry; then
                    entry_lines="$entry_lines$line"$'\n'
                    if echo "$line" | grep -qi "^[[:space:]]*\*\*Status"; then
                        current_status=$(echo "$line" | sed 's/\*\*/./g; s/.*://' | sed 's/^[[:space:]]*//; s/[[:space:]].*//' | tr -d '[:space:]' | tr "[:upper:]" "[:lower:]")
                    fi
                fi
                ;;
        esac
    done < "$LEARNINGS_DIR/LEARNINGS.md"

    if $in_entry && [ -n "$entry_id" ]; then
        case "$current_status" in
            resolved|promoted) ;;  # skip
            *) printf '%s\n' "$entry_lines" >> "$tmpfile" ;;
        esac
    fi

    # Verify: resolved entry removed, pending entry kept
    if grep -q "Archive This" "$tmpfile" 2>/dev/null; then
        log_fail "remove_archived_entries: should remove resolved entry"
    else
        log_pass "remove_archived_entries: resolved entry removed"
    fi

    if grep -q "Keep This" "$tmpfile" 2>/dev/null; then
        log_pass "remove_archived_entries: pending entry kept"
    else
        log_fail "remove_archived_entries: should keep pending entry"
    fi
}

# ── TEST: pending notification cleanup (>7 days) ──────────────
test_pending_cleanup() {
    log_info "Testing pending notification cleanup"

    PENDING_DIR="$LEARNINGS_DIR/.pending_notifications"
    mkdir -p "$PENDING_DIR"

    # Create old file (>7 days)
    touch -d "8 days ago" "$PENDING_DIR/old.json"
    # Create recent file (<7 days)
    touch -d "3 days ago" "$PENDING_DIR/recent.json"

    stale_count=$(find "$PENDING_DIR" -name "*.json" -mtime +7 -print 2>/dev/null | wc -l)

    [ "$stale_count" -ge 1 ] && log_pass "pending_cleanup: detects stale files" || log_fail "pending_cleanup: should detect stale files"

    find "$PENDING_DIR" -name "*.json" -mtime +7 -delete 2>/dev/null

    if [ -f "$PENDING_DIR/recent.json" ] && [ ! -f "$PENDING_DIR/old.json" ]; then
        log_pass "pending_cleanup: removes only old files"
    else
        log_fail "pending_cleanup: incorrect file removal"
    fi
}

# ── TEST: dry-run mode ─────────────────────────────────────────
test_dry_run() {
    log_info "Testing dry-run mode (syntax only)"

    # Check that --dry-run is handled
    if grep -q 'DRY_RUN=true' "$ARCHIVE_SH"; then
        log_pass "dry-run: DRY_RUN flag defined"
    else
        log_fail "dry-run: DRY_RUN flag not found"
    fi

    if grep -q 'if \[ "$DRY_RUN" = true \];' "$ARCHIVE_SH"; then
        log_pass "dry-run: dry-run check exists"
    else
        log_fail "dry-run: dry-run check not found"
    fi
}

# ── TEST: write-notified mode ─────────────────────────────────
test_write_notified() {
    log_info "Testing --write-notified mode"

    if grep -q '\-\-write-notified' "$ARCHIVE_SH"; then
        log_pass "write-notified: flag defined"
    else
        log_fail "write-notified: flag not found"
    fi

    if grep -q 'write_notified.py' "$ARCHIVE_SH"; then
        log_pass "write-notified: calls write_notified.py"
    else
        log_fail "write-notified: write_notified.py not called"
    fi
}

# ── MAIN ──────────────────────────────────────────────────────
main() {
    trap teardown EXIT

    log_info "=== archive.sh Unit Tests ==="
    echo ""

    setup
    source_functions

    test_source_tag
    test_normalize_outcome
    test_json_escape
    test_extract_field
    test_extract_meta
    test_process_file_resolved
    test_count_archived_occurrences
    test_remove_archived_entries
    test_pending_cleanup
    test_dry_run
    test_write_notified

    echo ""
    log_info "=== Test Results ==="
    echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    echo ""

    if [ "$TESTS_FAILED" -eq 0 ]; then
        echo -e "${GREEN}All tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}Some tests failed!${NC}"
        exit 1
    fi
}

main "$@"