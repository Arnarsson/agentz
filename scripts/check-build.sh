#!/bin/bash

# Function to extract error messages from Next.js output
parse_errors() {
  while IFS= read -r line; do
    if [[ $line == *"Failed to compile"* ]] || [[ $line == *"error"* ]] || [[ $line == *"Module not found"* ]]; then
      echo "BUILD ERROR: $line"
    fi
  done
}

# Run Next.js dev server and pipe output through error parser
npm run dev 2>&1 | parse_errors 