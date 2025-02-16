#!/bin/bash

# Check if search term is provided
if [ $# -eq 0 ]; then
    echo "Error: Please provide a search term"
    echo "Usage: $0 <search term>"
    exit 1
fi

MUSIC_DIR="$HOME/Music/Music"
SEARCH_TERM="$1"

# Check if music directory exists
if [ ! -d "$MUSIC_DIR" ]; then
    echo "Error: Music directory not found: $MUSIC_DIR"
    exit 1
fi

# Search for m4a files and store in array
echo "Searching in: $MUSIC_DIR"
echo "Looking for files matching: $SEARCH_TERM"
results=()
while IFS= read -r line; do
    results+=("$line")
done < <(find "$MUSIC_DIR" -type f -name "*.m4a" \( -iname "*${SEARCH_TERM}*" \) 2>/dev/null)

# Check if any files were found
if [ ${#results[@]} -eq 0 ]; then
    echo "No m4a files found matching: $SEARCH_TERM"
    exit 1
fi

# Display numbered results
echo "Found ${#results[@]} matching files:"
for i in "${!results[@]}"; do
    echo "$((i+1)). ${results[$i]##*/}"
done

# Get user selection
while true; do
    read -p "Enter the number of the song to add (1-${#results[@]}): " selection
    if [[ "$selection" =~ ^[0-9]+$ ]] && [ "$selection" -ge 1 ] && [ "$selection" -le "${#results[@]}" ]; then
        break
    fi
    echo "Invalid selection. Please enter a number between 1 and ${#results[@]}"
done

# Get playlist name
read -p "Enter the playlist name: " playlist_name

if [ -z "$playlist_name" ]; then
    echo "Error: Playlist name cannot be empty"
    exit 1
fi

# Get the selected file path
selected_file="${results[$((selection-1))]}"

# Add to playlist using AppleScript
if osascript add_to_playlist.scpt "$selected_file" "$playlist_name"; then
    echo "Successfully added '${selected_file##*/}' to playlist '$playlist_name'"
else
    echo "Error: Failed to add song to playlist"
    exit 1
fi

