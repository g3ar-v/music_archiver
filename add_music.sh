#!/bin/bash

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No color

# Check if search term is provided
if [ $# -eq 0 ]; then
  echo -e "${RED}Error: Please provide a search term${NC}"
  echo "Usage: $0 <search term>"
  exit 1
fi

MUSIC_DIR="$HOME/Music/Music"
SEARCH_TERM="$1"
# Check if music directory exists
if [ ! -d "$MUSIC_DIR" ]; then
  echo -e "${RED}Error: Music directory not found: $MUSIC_DIR${NC}"
  exit 1
fi

# Search for m4a files and store in array
echo "Searching in: $MUSIC_DIR"
echo "Looking for files matching: $SEARCH_TERM"
results=()
while IFS= read -r line; do
  results+=("$line")
done < <(find "$MUSIC_DIR" -type f -name "*.m4a" \( -iname "*$(printf "%q" "$SEARCH_TERM")*" \) 2>/dev/null)

# Check if any files were found
if [ ${#results[@]} -eq 0 ]; then
  echo -e "${RED}No m4a files found matching: $SEARCH_TERM${NC}"
  exit 1
fi

# Display numbered results
echo "Found ${#results[@]} matching files:"
for i in "${!results[@]}"; do
  echo "$((i + 1)). ${results[$i]##*/}"
done

# Get user selection
while true; do
  read -p "Enter the number of the song to add (1-${#results[@]}), or 'c' to cancel: " selection
  if [[ "$selection" =~ ^[0-9]+$ ]] && [ "$selection" -ge 1 ] && [ "$selection" -le "${#results[@]}" ]; then
    break
  elif [[ "$selection" = "c" ]]; then
    echo -e "${RED}Cancelled${NC}"
    exit 1
  fi
  echo -e "${RED}Invalid selection. Please enter a number between 1 and ${#results[@]}, or 'c' to cancel${NC}"
done

# Get playlist name
playlist_name=$2

if [ -z "$playlist_name" ]; then
  echo -e "${RED}Error: Playlist name cannot be empty${NC}"
  exit 1
fi

# Get the selected file path
selected_file="${results[$((selection - 1))]}"

# Add to playlist using AppleScript
if osascript add_to_playlist.scpt "$selected_file" "$playlist_name"; then
  echo -e "${GREEN}Successfully added '${selected_file##*/}' to playlist '$playlist_name'${NC}"
else
  echo -e "${RED}Error: Failed to add song to playlist${NC}"
  exit 1
fi
