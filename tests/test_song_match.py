#!/usr/bin/env python3
"""
Test script to check if a song with special characters can be found in Apple Music playlists.
This script tests the song_exists function with the song title "I've been in love".
"""

import sys
from update_playlist import song_exists, strings_match, normalize_string

def main():
    """Test the song_exists function with a specific song title."""
    # Song title with apostrophe to test
    song_title = "I've been in love"
    
    print(f"Testing song_exists function with title: '{song_title}'")
    
    # Display normalized version for debugging
    normalized_title = normalize_string(song_title)
    print(f"Normalized title: '{normalized_title}'")
    
    # Print string matching test results
    print(f"String match (strict): {strings_match(song_title, 'i\'ve been in love', strict=True)}")
    print(f"String match (normal): {strings_match(song_title, 'i\'ve been in love', strict=False)}")
    
    # Try some variations to test string matching
    variations = [
        "I've Been In Love",
        "I've been in love",
        "Ive been in love",
        "I'VE BEEN IN LOVE",
        "I've  been in  love"  # extra spaces
    ]
    
    print("\nTesting string matching with variations:")
    for var in variations:
        strict_match = strings_match(song_title, var, strict=True)
        normal_match = strings_match(song_title, var, strict=False)
        print(f"'{var}': strict={strict_match}, normal={normal_match}")
    
    # Test the actual song_exists function
    print("\nChecking if song exists in Apple Music playlist:")
    exists = song_exists(song_title)
    
    if exists:
        print(f"✅ SUCCESS: Song '{song_title}' was found in Apple Music playlist")
    else:
        print(f"❌ FAILURE: Song '{song_title}' was NOT found in Apple Music playlist")
    
    return 0 if exists else 1

if __name__ == "__main__":
    sys.exit(main())

