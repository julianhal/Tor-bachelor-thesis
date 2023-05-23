#!/bin/bash

for folder in distance-bandwidth_*/*_percent; do
  for file in "${folder}"/*; do
    if [[ $(basename "$file") == *"_percent_" ]]; then
      # Extract the folder name
      folder_name=$(dirname "$file")
      # Create the new filename by removing the trailing underscore and adding .json
      new_filename=$(basename "$file" | sed 's/_percent_$/_percent.json/')
      mv "$file" "${folder_name}/${new_filename}"
    fi
  done
done

