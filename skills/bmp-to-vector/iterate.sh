#!/bin/bash
# Aider-driven iterative code improvement for the photo-to-vector pipeline.
# Uses a local LLM via Ollama to refine pipeline code.

MODEL="${1:-qwen3.5:4b}"
INPUT_PATH="${2:-tmp.bmp}"
OUTPUT_PATH="${3:-test_output.svg}"

if [ ! -f "$INPUT_PATH" ]; then
    echo "[ERROR] Input bitmap not found: $INPUT_PATH"
    exit 1
fi

# Determine Aider model configuration
AIDER_FLAGS=""
if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$OPENAI_API_KEY" ] && [ -z "$OPENROUTER_API_KEY" ] && [ -z "$GEMINI_API_KEY" ]; then
    echo "[INFO] No API keys detected. Running locally via Ollama."
    AIDER_FLAGS="--model ollama_chat/$MODEL"
    if [ -n "$AIDER_EDIT_FORMAT" ]; then
        AIDER_FLAGS="$AIDER_FLAGS --edit-format $AIDER_EDIT_FORMAT"
    else
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

# Pipeline modules to include in Aider's context
PIPELINE_FILES="trace.py quality.py render.py refine.py diagnose.py prescribe.py pipeline.py"

aider $AIDER_FLAGS --no-stream --no-pretty --yes-always --max-chat-history-tokens 100000 \
  --message-file SKILL.md \
  --message "Improve the tracing pipeline. Test by running 'python pipeline.py trace $INPUT_PATH $OUTPUT_PATH -n 16' and checking the SVG output. Focus on trace.py and quality.py." \
  $PIPELINE_FILES < /dev/null

AIDER_EXIT_CODE=$?
echo "[INFO] Aider execution completed with exit code: $AIDER_EXIT_CODE"
exit $AIDER_EXIT_CODE
