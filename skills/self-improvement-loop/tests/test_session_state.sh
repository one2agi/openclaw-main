#!/bin/bash
# test_session_state.sh — TDD tests for session_state.sh
# Run: bash tests/test_session_state.sh
#
# RED phase: tests written BEFORE fixes exist

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SESSION_STATE_SH="$SCRIPT_DIR/../scripts/session_state.sh"
TEST_TMPDIR=""
TESTS_PASSED=0
TESTS_FAILED=0

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log_pass() { echo -e "${GREEN}[PASS]${NC} $1"; ((TESTS_PASSED++)) || true; }
log_fail() { echo -e "${RED}[FAIL]${NC} $1"; ((TESTS_FAILED++)) || true; }
log_info() { echo -e "${YELLOW}[INFO]${NC} $1"; }

setup() {
    TEST_TMPDIR=$(mktemp -d)
    mkdir -p "$TEST_TMPDIR/.openclaw/workspace/agents/test-agent/.learnings"
    mkdir -p "$TEST_TMPDIR/.openclaw/workspace/agents/main/.learnings"
    export HOME="$TEST_TMPDIR"
}

teardown() {
    [ -n "$TEST_TMPDIR" ] && [ -d "$TEST_TMPDIR" ] && rm -rf "$TEST_TMPDIR"
}

# ─────────────────────────────────────────────────────────────
# BUG TEST 1 (RED): should_trigger works after completion-word trigger + review completed
#
# Scenario:
#   - Message count grows to 8 (below threshold of 10)
#   - Completion word fires → trigger_review() called (count→9, triggered=true)
#   - User keeps chatting → count reaches 10+ while review is pending
#   Expected during pending: "no" (can't double-trigger pending review)
#   After user does another task → complete() → count reaches 10 again
#   Expected after complete: "yes" (new task can re-trigger)
# ─────────────────────────────────────────────────────────────
test_should_trigger_after_review_completed() {
    log_info "BUG TEST 1: should_trigger works after review completes"
    local AGENT="test-agent"

    # Clean slate
    bash "$SESSION_STATE_SH" "$AGENT" reset 2>/dev/null || true

    # Simulate messages 1-8 (below threshold)
    for i in $(seq 1 8); do
        bash "$SESSION_STATE_SH" "$AGENT" inc > /dev/null
    done

    # State: count=8, triggered=false, should="no"
    local before
    before=$(bash "$SESSION_STATE_SH" "$AGENT" should)
    [ "$before" = "no" ] || { log_fail "BUG1 setup: before should be no (count=8), got $before"; return; }

    # Completion word fires → trigger() increments count→9, triggered=true
    bash "$SESSION_STATE_SH" "$AGENT" trigger > /dev/null

    # More messages arrive while review is in progress (count 9→11)
    for i in $(seq 1 2); do
        bash "$SESSION_STATE_SH" "$AGENT" inc > /dev/null
    done

    # During pending review: should return "no" (can't double-trigger)
    local during
    during=$(bash "$SESSION_STATE_SH" "$AGENT" should)
    [ "$during" = "no" ] || { log_fail "BUG1 during: should be 'no' while review pending, got $during"; return; }
    log_pass "BUG1: correctly returns 'no' while review is pending (count=11, triggered=true)"

    # Complete the review — resets triggered=false
    bash "$SESSION_STATE_SH" "$AGENT" complete > /dev/null

    # After complete, count still 11, triggered=false, should="yes" (count >= 10)
    local after
    after=$(bash "$SESSION_STATE_SH" "$AGENT" should)
    if [ "$after" = "yes" ]; then
        log_pass "BUG1: should_trigger returns 'yes' after review complete (PASS = fix works)"
    else
        log_fail "BUG1: should_trigger should return 'yes' after review complete, got '$after'"
    fi

    bash "$SESSION_STATE_SH" "$AGENT" reset 2>/dev/null || true
}

# ─────────────────────────────────────────────────────────────
# BUG TEST 2 (RED): completion word trigger should also increment message count
#
# Scenario:
#   - Message count at 8
#   - Completion word fires → trigger() called BUT count NOT incremented
#   - count stays at 8 (not 9)
#   Expected: count becomes 9 (same as normal message processing)
#   Actual (BUG): count stays same; subsequent inc makes it 9, not 10
# ─────────────────────────────────────────────────────────────
test_completion_word_increments_count() {
    log_info "BUG TEST 2: completion word trigger increments message count"
    local AGENT="test-agent"

    bash "$SESSION_STATE_SH" "$AGENT" reset 2>/dev/null || true

    # Count to 8
    for i in $(seq 1 8); do
        bash "$SESSION_STATE_SH" "$AGENT" inc > /dev/null
    done

    # Completion word fires — simulates handler.js calling trigger() (NOT inc)
    bash "$SESSION_STATE_SH" "$AGENT" trigger > /dev/null

    # Read count after trigger
    local count_after_trigger
    count_after_trigger=$(bash "$SESSION_STATE_SH" "$AGENT" get | python3 -c "import sys,json; print(json.load(sys.stdin)['message_count'])")

    # BUG: count is still 8 (trigger() doesn't inc)
    # EXPECTED (after fix): count should be 9
    if [ "$count_after_trigger" = "9" ]; then
        log_pass "BUG2: message_count is 9 after completion trigger (PASS = fix works)"
    else
        log_fail "BUG2: message_count should be 9 after completion trigger, got '$count_after_trigger' (FAIL = bug confirmed)"
    fi

    bash "$SESSION_STATE_SH" "$AGENT" reset 2>/dev/null || true
}

# ─────────────────────────────────────────────────────────────
# BUG TEST 3 (BEHAVIORAL): review_completed should allow re-trigger
#
# Scenario:
#   - User does completion word trigger (triggered=true)
#   - User says "是" → skill created → review_completed=true
#   - Later in same session, user completes another task
#   Expected: should_trigger returns "yes" again for the new task
#   Actual: currently returns "no" because triggered=true and completed=true
# ─────────────────────────────────────────────────────────────
test_retrigger_after_review_completed() {
    log_info "BUG TEST 3: can re-trigger self-review after completing one"
    local AGENT="test-agent"

    bash "$SESSION_STATE_SH" "$AGENT" reset 2>/dev/null || true

    # First task: count to 10 → should trigger
    for i in $(seq 1 10); do
        bash "$SESSION_STATE_SH" "$AGENT" inc > /dev/null
    done
    bash "$SESSION_STATE_SH" "$AGENT" trigger > /dev/null
    bash "$SESSION_STATE_SH" "$AGENT" complete > /dev/null

    # State: review_completed=true, message_count=10, triggered=true

    # Simulate continuing work — new messages come in
    for i in $(seq 1 10); do
        bash "$SESSION_STATE_SH" "$AGENT" inc > /dev/null
    done

    # BUG: should returns "no" because triggered=true (can't re-trigger)
    # EXPECTED (after fix): should returns "yes" for the new task
    local should
    should=$(bash "$SESSION_STATE_SH" "$AGENT" should)
    if [ "$should" = "yes" ]; then
        log_pass "BUG3: should_trigger returns 'yes' for second task (PASS = fix works)"
    else
        log_fail "BUG3: should_trigger should return 'yes' for second task, got '$should' (FAIL = bug confirmed)"
    fi

    bash "$SESSION_STATE_SH" "$AGENT" reset 2>/dev/null || true
}

main() {
    trap teardown EXIT
    echo ""
    log_info "=== TDD RED Phase: session_state.sh Bug Tests ==="
    echo ""

    setup

    test_completion_word_increments_count
    test_should_trigger_after_review_completed
    test_retrigger_after_review_completed

    echo ""
    log_info "=== Test Results ==="
    echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    echo ""

    if [ "$TESTS_FAILED" -eq 0 ]; then
        echo -e "${GREEN}All tests passed — bugs are fixed!${NC}"
        exit 0
    else
        echo -e "${YELLOW}Tests failed as expected in RED phase — proceeding to GREEN phase${NC}"
        exit 1
    fi
}

main "$@"