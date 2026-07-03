#!/bin/bash

MODEL="${1:-qwen3.5:4b}"
INPUT_PATH="${2:-test_input.bmp}"
OUTPUT_PATH="${3:-test_output.svg}"

# Ensure input bitmap exists
if [ ! -f "$INPUT_PATH" ]; then
    echo "Please provide a valid input bitmap at $INPUT_PATH"
    exit 1
fi

# Determine Aider model configuration based on environment variables
AIDER_FLAGS=""
if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$OPENAI_API_KEY" ] && [ -z "$OPENROUTER_API_KEY" ] && [ -z "$GEMINI_API_KEY" ]; then
    echo "[INFO] No API keys detected. Running locally via Ollama."
    AIDER_FLAGS="--model ollama_chat/$MODEL"
    if [ -n "$AIDER_EDIT_FORMAT" ]; then
        AIDER_FLAGS="$AIDER_FLAGS --edit-format $AIDER_EDIT_FORMAT"
    else
        # Default to whole format for local models to ensure formatting compliance
        AIDER_FLAGS="$AIDER_FLAGS --edit-format whole"
    fi
else
    echo "[INFO] API key detected. Running Aider in cloud mode."
fi

echo "[INFO] Starting Aider iteration..."
echo "       Model:       $MODEL"
echo "       Input Path:  $INPUT_PATH"
echo "       Output Path: $OUTPUT_PATH"
echo "       Aider Flags: $AIDER_FLAGS"

# Launch Aider with standard input redirected to /dev/null to prevent hangs
aider $AIDER_FLAGS --no-stream --no-pretty --yes-always --max-chat-history-tokens 100000 \
  --message-file SKILL.md \
  --message "Implement the merge_semantics function in merge.py. Test your changes by running 'python pipeline.py $MODEL $INPUT_PATH $OUTPUT_PATH' and checking the resulting SVG structure. Ensure text nodes are created." \
  merge.py < /dev/null


AIDER_EXIT_CODE=$?
echo "[INFO] Aider execution completed with exit code: $AIDER_EXIT_CODE"
exit $AIDER_EXIT_CODE









