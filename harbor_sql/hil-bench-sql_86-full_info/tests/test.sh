#!/usr/bin/env bash
REWARD_DIR="/logs/verifier"
mkdir -p "$REWARD_DIR"

_fail() {
    local msg="$1"
    echo "0" > "$REWARD_DIR/reward.txt"
    printf '{"solve": 0, "precision": 0.0, "recall": 0.0, "f1": 0.0, "error": "%s"}\n' "$msg" \
        > "$REWARD_DIR/reward.json"
}

python /tests/test_verify.py 2>&1
exit_code=$?

if [ "$exit_code" -ne 0 ]; then
    _fail "test_verify.py exited with code $exit_code"
    exit "$exit_code"
fi
