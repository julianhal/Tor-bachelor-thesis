#!/bin/bash

for folder in distance_*_percent_bandwidth_*_percent; do
  # Extract XX and YY from the folder name
  distance=$(echo "$folder" | grep -oP 'distance_\K[0-9]+(?=_percent)')
  bandwidth=$(echo "$folder" | grep -oP 'bandwidth_\K[0-9]+(?=_percent)')

  # Create the new folder name
  new_folder="distance-bandwidth_${distance}-${bandwidth}_percent"
  mkdir -p "$new_folder"

  # Rename files inside the folder
  for file in "${folder}"/*; do
    filename=$(basename "$file")
    # Extract the part after "distance_XX_percent_bandwidth_YY_percent" in the filename
    suffix=$(echo "$filename" | grep -oP "distance_${distance}_percent_bandwidth_${bandwidth}_percent_\K.*")
    # Create the new filename
    new_filename="distance-bandwidth_${distance}-${bandwidth}_percent_${suffix}"
    # Move the file to the new folder with the new name
    mv "$file" "${new_folder}/${new_filename}"
  done

  # Remove the original folder
  rmdir "$folder"
done

