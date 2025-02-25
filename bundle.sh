#!/bin/bash

# Check if the output file name and directories to exclude are provided
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <output_filename.txt> [excluded_directories...]"
  exit 1
fi

# Assign the output file name
output_file="$1"
shift # Shift to exclude the first argument and keep the rest as directories to exclude

# Create a pattern to exclude directories from the tree and ls-tree commands
exclude_pattern='.git'
for dir in "$@"; do
  exclude_pattern+="|$dir"
done

# Generate the project structure excluding the specified directories
tree -I "$exclude_pattern" > structure.txt

# Process the list of files in the repository, excluding specified directories
git ls-tree -r HEAD --name-only | while read filename; do
  # Check if the file is in one of the excluded directories
  skip=0
  for dir in "$@"; do
    if [[ "$filename" == "$dir/"* ]]; then
      skip=1
      break
    fi
  done

  # Skip directories and files in excluded directories
  if [[ $skip -eq 1 ]]; then
    continue
  fi

  # Check if the current item is a regular file (not a directory)
  if [[ -f "$filename" ]]; then
    # Index key files and skip others (like requirements.txt)
    if [[ "$filename" =~ \.(py|md|json|yml)$ ]]; then
      echo "### $filename ###" >> "$output_file"
      # Extract the first 50 lines of the file
      head -n 50 "$filename" >> "$output_file"
      echo -e "\n\n" >> "$output_file"
    elif [[ "$filename" == "requirements.txt" ]]; then
      echo "### $filename ###" >> "$output_file"
      echo "(Content omitted: external dependencies)" >> "$output_file"
      # Optionally include the first 5 lines of the requirements.txt file
      head -n 5 requirements.txt >> "$output_file"
      echo -e "\n\n" >> "$output_file"
    fi
  fi
done

# Add the project structure to the output file
cat structure.txt >> "$output_file"

# Notify the user of successful completion
echo "Bundle generated and saved to $output_file"

