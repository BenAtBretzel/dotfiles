#!/bin/bash

MODEL="${1:-qwen3.5:4b}"
INPUT_PATH="${2:-test_input.bmp}"
OUTPUT_PATH="${3:-test_output.svg}"

# Ensure input bitmap exists
if [ ! -f "$INPUT_PATH" ]; then
    echo "Please provide a valid input bitmap at $INPUT_PATH"
    exit 1
fi

# Launch Aider with the architect skill and the target script
aider \
  --message-file SKILL.md \
  --message "Implement the merge_semantics function in pipeline.py. Test your changes by running 'python pipeline.py $MODEL $INPUT_PATH $OUTPUT_PATH' and checking the resulting SVG structure. Ensure text nodes are actually created." \
  pipeline.py


