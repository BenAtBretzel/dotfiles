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
    echo "No API keys detected (ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.)."
    echo "Defaulting Aider to run locally with Ollama model: ollama/$MODEL"
    AIDER_FLAGS="--model ollama/$MODEL --edit-format whole"
fi

# Launch Aider with the architect skill and the target script
aider $AIDER_FLAGS --yes-always --message-file SKILL.md --message "Implement the merge_semantics function in pipeline.py. Test your changes by running 'python pipeline.py $MODEL $INPUT_PATH $OUTPUT_PATH' and checking the resulting SVG structure. Ensure text nodes are actually created." pipeline.py





