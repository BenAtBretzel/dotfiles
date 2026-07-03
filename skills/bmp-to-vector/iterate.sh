#!/bin/bash

# Ensure a test bitmap exists
if [ ! -f "test_input.bmp" ]; then
    echo "Please provide a test_input.bmp"
    exit 1
fi

MODEL="${1:-qwen3.5:4b}"

# Launch Aider with the architect skill and the target script
aider \
  --message-file SKILL.md \
  --message "Implement the merge_semantics function in pipeline.py. Test your changes by running 'python pipeline.py $MODEL test_input.bmp test_output.svg' and checking the resulting SVG structure. Ensure text nodes are actually created." \
  pipeline.py

