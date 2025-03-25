from appscript import app
import subprocess
import appscript
import spotipy
import colorama
import unicodedata
import re
from colorama import Fore
from spotipy.oauth2 import SpotifyOAuth
import sys


def get_spotify_playlist_track_data(playlist_uri):
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            scope="playlist-modify-public playlist-modify-private playlist-read-private"
        )
    )
    playlist_id = playlist_uri
    tracks = []
    results = sp.playlist_tracks(playlist_id)
    tracks.extend(results["items"])

    while results["next"]:
        print("more tracks exist...")
        results = sp.next(results)
        tracks.extend(results["items"])

    track_data = {item["track"]["name"]: item["track"]["uri"] for item in tracks}
    return track_data


def get_apple_playlist_track_name(apple_playlist):
    try:
        print(f"\nTrying to access Music app...")
        music = appscript.app("Music")
        print(f"Successfully connected to Music app")

        print(f"Trying to access playlist: {apple_playlist}")
        playlist = music.playlists[apple_playlist]

        # Verify playlist exists
        try:
            name = playlist.name.get()
            print(f"Found playlist: {name}")
        except Exception as e:
            print(f"Error accessing playlist name: {e}")
            raise

        print("Attempting to access tracks...")
        try:
            tracks = playlist.tracks.get()
            track_names = [track.name.get() for track in tracks]
            print(f"Successfully retrieved {len(track_names)} tracks")
            return track_names
        except Exception as e:
            print(f"Error accessing tracks: {e}")
            raise
    except Exception as e:
        print(f"An error occurred: {e}")
        raise


# Helper functions for improved string matching
def normalize_string(s):
    """
    Normalize a string by:
    1. Converting to lowercase
    2. Removing diacritics (accents)
    3. Removing special characters except alphanumeric and spaces
    """
    # Convert to lowercase
    s = s.lower()
    # Normalize Unicode characters (NFKD decomposition)
    s = unicodedata.normalize("NFKD", s)
    # Remove diacritics (accents)
    s = "".join([c for c in s if not unicodedata.combining(c)])
    # Remove special characters, keep only alphanumeric and spaces
    s = re.sub(r"[^\w\s]", "", s)
    # Remove extra whitespace
    s = " ".join(s.split())
    return s


def strings_match(str1, str2, strict=False):
    """
    Compare two strings with improved matching for special characters.

    Parameters:
        str1, str2: The strings to compare
        strict: If True, only normalize case, otherwise do full normalization

    Returns:
        True if strings match according to the comparison method
    """
    if strict:
        # Case-insensitive comparison only
        return str1.lower() == str2.lower()
    else:
        # Full normalization for more lenient comparison
        return normalize_string(str1) == normalize_string(str2)


# def song_exists(song_name):
#     music = app("Music")
#     tracks = music.tracks.get()
#     print("\n")
#     print(f"Checking if song '{song_name}' exists in Apple Music...")
#     # print(f"Original search term: '{song_name}'")
#     # print(f"Normalized search term: '{normalize_string(song_name)}'")
#
#     # Debug counter to limit output for large libraries
#     debug_count = 0
#     max_debug_tracks = 5
#
#     for track in tracks:
#         track_name = track.name()
#         normalized_track_name = normalize_string(track_name)


def song_exists(search_term):
    """Search for tracks in the Apple Music library that match the search term.
    
    Args:
        search_term (str): Format should be 'track_name - artist_name'
    
    Returns:
        list: List of matching tracks with exact artist and title match
    """
    try:
        # Split search term into track and artist
        if ' - ' not in search_term:
            print(Fore.YELLOW + f"Warning: Search term '{search_term}' should be in format 'track_name - artist_name'")
            return []
            
        track_title, artist_name = search_term.split(' - ', 1)
        
        music = app("Music")
        library_tracks = music.tracks()
        matching_tracks = []

        # Normalize the search terms
        normalized_title = normalize_string(track_title)
        normalized_artist = normalize_string(artist_name)

        for track in library_tracks:
            try:
                # Get track metadata
                track_name = track.name.get() if hasattr(track, "name") else "Unknown Track"
                track_artist = track.artist.get() if hasattr(track, "artist") else "Unknown Artist"
                track_album = track.album.get() if hasattr(track, "album") else "Unknown Album"

                # Check for exact matches first
                title_matches = strings_match(track_name, track_title, strict=True)
                artist_matches = strings_match(track_artist, artist_name, strict=True)
                
                # If no exact match, try normalized matching
                if not (title_matches and artist_matches):
                    title_matches = strings_match(track_name, track_title)
                    artist_matches = strings_match(track_artist, artist_name)

                # Only include if both title and artist match
                if title_matches and artist_matches:
                    matching_tracks.append((track, track_name, track_artist, track_album))
                    
            except Exception as e:
                # Skip tracks that cause errors when accessing their properties
                continue

        if not matching_tracks:
            print(Fore.YELLOW + f"No exact matches found for '{track_title}' by '{artist_name}'")
            
        return matching_tracks
    except Exception as e:
        print(Fore.RED + f"Error searching tracks in library: {e}" + Fore.RESET)
        return []


def parse_selection(selection_str, max_value):
    """
    Parse user selection string with support for ranges and comma-separated values.
    Returns a sorted list of unique selected indices.

    Examples:
    - "1,3,5" returns [1, 3, 5]
    - "1-3,5" returns [1, 2, 3, 5]
    """
    selected = set()

    # Split by comma
    parts = selection_str.split(",")

    for part in parts:
        part = part.strip()

        # Handle range (e.g., "1-3")
        if "-" in part:
            try:
                start, end = map(int, part.split("-"))
                if 1 <= start <= end <= max_value:
                    selected.update(range(start, end + 1))
                else:
                    print(
                        Fore.RED
                        + f"Range {start}-{end} is out of bounds. Please use numbers between 1 and {max_value}."
                    )
            except ValueError:
                print(
                    Fore.RED + f"Invalid range format: {part}. Use 'start-end' format."
                )

            # Handle individual number
        else:
            try:
                num = int(part)
                if 1 <= num <= max_value:
                    selected.add(num)
                else:
                    print(
                        Fore.RED
                        + f"Number {num} is out of bounds. Please use numbers between 1 and {max_value}."
                    )
            except ValueError:
                print(Fore.RED + f"Invalid number: {part}")

    return sorted(list(selected))


def get_spotify_playlists():
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            scope="playlist-modify-public playlist-modify-private playlist-read-private"
        )
    )
    playlists = sp.current_user_playlists()
    spotify_playlists = {
        playlist["name"]: playlist["uri"] for playlist in playlists["items"]
    }
    return spotify_playlists


def get_apple_playlists():
    music = app("Music")
    playlists = music.user_playlists.get()
    apple_playlists = {
        playlist.name(): None for playlist in playlists if hasattr(playlist, "name")
    }
    return apple_playlists


def select_spotify_playlist():
    spotify_playlists = get_spotify_playlists()
    apple_playlists = get_apple_playlists()

    # Find playlists that exist in both services
    matching_playlists = {
        name: uri for name, uri in spotify_playlists.items() if name in apple_playlists
    }

    if not matching_playlists:
        print(
            Fore.RED
            + "No matching playlists found between Spotify and Apple Music!"
            + Fore.RESET
        )
        raise ValueError("No matching playlists available for sync")

    print(
        Fore.CYAN
        + "\nAvailable Playlists (Found in both Spotify and Apple Music):"
        + Fore.RESET
    )
    playlist_options = list(matching_playlists.items())

    for i, (name, uri) in enumerate(playlist_options, 1):
        print(f"{i}. {name}")

    while True:
        try:
            choice = int(input("\nSelect a playlist by number: ").strip())
            if 1 <= choice <= len(playlist_options):
                selected_name, selected_uri = playlist_options[choice - 1]
                print(f"Selected playlist: {selected_name}")
                return selected_name, selected_uri
            else:
                print(
                    Fore.RED
                    + f"Please enter a number between 1 and {len(playlist_options)}"
                    + Fore.RESET
                )
        except ValueError:
            print(Fore.RED + "Please enter a valid number" + Fore.RESET)


def add_songs_to_apple_playlist(playlist_name, songs):
    for song in songs:
        add_choice = (
            input(
                f"Do you want to add '{song}' to playlist '{playlist_name}'? (yes/no): "
            )
            .strip()
            .lower()
        )
        if add_choice == "yes":
            try:
                print(f"Adding song '{song}' to playlist '{playlist_name}'")
                subprocess.run(["./add_music.sh", song, playlist_name], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error adding song '{song}' to playlist '{playlist_name}': {e}")


def remove_from_apple_playlist(playlist_name, song_name):
    music = app("Music")
    playlist = music.playlists[playlist_name]
    for track in playlist.tracks():
        # Try both matching methods: strict (case-insensitive) first, then normalized if needed
        if strings_match(track.name(), song_name, strict=True) or strings_match(
            track.name(), song_name
        ):
            # Using the actual track.name() to ensure we're deleting the right track
            playlist.tracks[track.name()].delete()
            print(
                Fore.YELLOW
                + f"Removed '{song_name}' from playlist '{playlist_name}'"
                + Fore.RESET
            )
            return True
            
    print(
        Fore.YELLOW
        + f"Could not find '{song_name}' in the playlist '{playlist_name}'"
        + Fore.RESET
    )
    return False


def remove_from_apple_music(song_name, artist_name=None, dry_run=False, batch_mode=False):
    """Remove track(s) from Apple Music library with improved safety checks.

    Args:
        song_name (str): Name of the song to remove
        artist_name (str, optional): Artist name for additional verification
        dry_run (bool): If True, only preview what would be deleted
        batch_mode (bool): If True, delete all matching tracks without individual confirmation

    Returns:
        bool: True if operation was successful, False otherwise
    """
    music = app("Music")
    tracks = music.tracks()
    matching_tracks = []

    # Find all matching tracks
    for track in tracks:
        track_name = track.name()
        track_artist = track.artist()
        
        # Check if track name matches
        name_matches = strings_match(track_name, song_name, strict=True) or strings_match(track_name, song_name)
        
        # If artist is provided, verify artist match
        artist_matches = True if not artist_name else (
            strings_match(track_artist, artist_name, strict=True) or 
            strings_match(track_artist, artist_name)
        )
        
        if name_matches and artist_matches:
            matching_tracks.append((track, track_name, track_artist))

    if not matching_tracks:
        print(Fore.RED + f"\nCould not find '{song_name}'{' by ' + artist_name if artist_name else ''} in your Apple Music library" + Fore.RESET)
        return False

    # Preview matches
    print(f"\nFound {len(matching_tracks)} matching track{'s' if len(matching_tracks) > 1 else ''}:")
    for i, (track, name, artist) in enumerate(matching_tracks, 1):
        print(f"{i}. '{name}' by {artist}")

    if dry_run:
        print(Fore.YELLOW + "\nDry run - no tracks will be deleted" + Fore.RESET)
        return True

    # Confirm deletion
    if not batch_mode:
        print(
            Fore.RED + 
            "\nWARNING: This will permanently delete the track(s) from your Apple Music library!" +
            Fore.RESET
        )
        confirm = input(
            Fore.RED + 
            f"Type 'DELETE' to remove {len(matching_tracks)} track{'s' if len(matching_tracks) > 1 else ''}, or 'CANCEL' to abort: " +
            Fore.RESET
        ).strip()
        
        if confirm != "DELETE":
            print(Fore.YELLOW + "\nDeletion cancelled" + Fore.RESET)
            return False

    # Perform deletion
    success_count = 0
    for track, name, artist in matching_tracks:
        try:
            if not batch_mode:
                print(f"\nDeleting '{name}' by {artist}...")
            track.delete()
            success_count += 1
        except Exception as e:
            print(Fore.RED + f"Failed to delete '{name}': {str(e)}" + Fore.RESET)

    # Report results
    if success_count == len(matching_tracks):
        print(Fore.GREEN + f"\nSuccessfully deleted {success_count} track{'s' if success_count > 1 else ''}" + Fore.RESET)
        return True
    elif success_count > 0:
        print(Fore.YELLOW + f"\nPartially successful: deleted {success_count}/{len(matching_tracks)} tracks" + Fore.RESET)
        return True
    else:
        print(Fore.RED + "\nFailed to delete any tracks" + Fore.RESET)
        return False


def batch_remove_from_playlist(playlist_name, tracks_to_remove):
    """Remove multiple tracks from a playlist at once"""
    if not tracks_to_remove:
        print(Fore.YELLOW + "No tracks selected for removal.")
        return

    print(
        Fore.YELLOW
        + f"\nYou are about to remove {len(tracks_to_remove)} tracks from '{playlist_name}':"
    )
    for i, track in enumerate(tracks_to_remove, 1):
        print(f"{i}. {track}")

    confirm = (
        input(
            f"\nAre you sure you want to remove these {len(tracks_to_remove)} tracks? (yes/no): "
        )
        .strip()
        .lower()
    )

    if confirm != "yes":
        print(Fore.YELLOW + "Batch removal cancelled.")
        return

    success_count = 0
    error_count = 0

    # Process each track in the batch
    for track in tracks_to_remove:
        try:
            if remove_from_apple_playlist(playlist_name, track):
                success_count += 1
                print(Fore.GREEN + f"Removed: {track}")
            else:
                error_count += 1
                print(Fore.RED + f"Error removing '{track}'")
        except Exception as e:
            error_count += 1
            print(Fore.RED + f"Error removing '{track}': {e}")

    print(
        Fore.GREEN
        + f"\nBatch removal complete: {success_count} tracks removed successfully, {error_count} failed."
    )

    # Ask if user wants to delete any of these from the library as well
    if success_count > 0:
        delete_from_lib = (
            input(
                "\nDo you also want to try deleting any of these tracks from your Apple Music library? (yes/no): "
            )
            .strip()
            .lower()
        )
        if delete_from_lib == "yes":
            # Show list of successfully removed tracks and let user select for library deletion
            print(
                Fore.YELLOW
                + "\nWARNING: Library deletion will permanently remove songs from your Apple Music!"
            )
            print(
                "\nSelect tracks to delete from library (same format as before, or 'none' to skip):"
            )

            # Get list of successfully removed tracks
            successful_tracks = tracks_to_remove  # Using the original list as we already tracked success separately

            for i, track_name in enumerate(successful_tracks, 1):
                print(f"{i}. {track_name}")

            lib_selection = input("\nYour selection: ").strip()

            if lib_selection.lower() == "none":
                print(Fore.YELLOW + "No tracks will be deleted from the library.")
            else:
                if lib_selection.lower() == "all":
                    selected_indices = list(range(1, len(successful_tracks) + 1))
                else:
                    selected_indices = parse_selection(
                        lib_selection, len(successful_tracks)
                    )

                if selected_indices:
                    for idx in selected_indices:
                        track_name = successful_tracks[idx - 1]
                        remove_from_apple_music(track_name)


def handle_removed_tracks(apple_playlist_name, removed_tracks):
    """
    Interactive handling of tracks removed from Spotify but present in Apple Music playlist
    with comprehensive removal options for both playlist and library management.
    """
    if not removed_tracks:
        print(Fore.GREEN + "\nNo tracks to remove - playlist is in sync!")
        return

    print(
        Fore.YELLOW
        + "\nThe following songs were removed from Spotify playlist but exist in Apple Music:"
    )

    # Display the tracks with numbers for selection
    for i, track in enumerate(removed_tracks, 1):
        print(f"{i}. {track}")

    # Present comprehensive options
    print("\nRemoval options:")
    print("1. Keep all songs (no changes)")
    print("2. Remove selected songs from playlist only")
    print("3. Remove selected songs from both playlist and library")
    print("4. Remove all songs from playlist only")
    print("5. Remove all songs from both playlist and library")

    while True:
        choice = input("\nEnter your choice (1-5): ").strip()
        if choice in ['1', '2', '3', '4', '5']:
            break
        print(Fore.RED + "Invalid choice. Please enter a number between 1 and 5.")

    if choice == '1':
        print(Fore.GREEN + "Keeping all songs in Apple Music playlist")
        return

    # Function to handle actual removal
    def find_playlist_track(playlist_name, track_name):
        """Find the exact track in the playlist to get its metadata"""
        music = app("Music")
        playlist = music.playlists[playlist_name].get()
        playlist_tracks = playlist.tracks.get()
        
        for track in playlist_tracks:
            if strings_match(track.name.get(), track_name, strict=True):
                return {
                    'track': track,
                    'name': track.name.get(),
                    'artist': track.artist.get(),
                    'album': track.album.get(),
                    'duration': track.duration.get(),
                    'track_number': track.track_number.get(),
                    'disc_number': track.disc_number.get()
                }
        return None

    def find_matching_tracks(playlist_track_info):
        """Find matching tracks in the library using detailed metadata"""
        music = app("Music")
        tracks = music.tracks()
        matching_tracks = []
        
        # Extract metadata from playlist track
        name = playlist_track_info['name']
        artist = playlist_track_info['artist']
        album = playlist_track_info['album']
        duration = playlist_track_info['duration']
        track_number = playlist_track_info['track_number']
        disc_number = playlist_track_info['disc_number']

        for track in tracks:
            # Basic metadata
            track_name = track.name.get()
            track_artist = track.artist.get()
            track_album = track.album.get()
            track_duration = track.duration.get()
            track_track_number = track.track_number.get()
            track_disc_number = track.disc_number.get()
            
            # Score-based matching
            score = 0
            
            # Name match (most important)
            if strings_match(track_name, name, strict=True):
                score += 5
            elif strings_match(track_name, name):
                score += 3
            else:
                continue  # If name doesn't match at all, skip this track
            
            # Artist match
            if strings_match(track_artist, artist, strict=True):
                score += 4
            elif strings_match(track_artist, artist):
                score += 2
            
            # Album match
            if strings_match(track_album, album, strict=True):
                score += 3
            elif strings_match(track_album, album):
                score += 1
            
            # Duration match (within 1 second)
            if abs(track_duration - duration) <= 1:
                score += 2
            
            # Track/disc number match
            if track_track_number == track_number:
                score += 1
            if track_disc_number == disc_number:
                score += 1
            
            # Only include if it's a reasonably good match
            if score >= 7:  # Requires at least name match and either strict artist match or multiple other matches
                matching_tracks.append({
                    'track': track,
                    'name': track_name,
                    'artist': track_artist,
                    'album': track_album,
                    'score': score
                })
        
        # Sort by match score
        matching_tracks.sort(key=lambda x: x['score'], reverse=True)
        return matching_tracks

    def remove_tracks(tracks_to_remove, remove_from_lib=False):
        print(f"\nRemoving {len(tracks_to_remove)} tracks...")
        for track in tracks_to_remove:
            try:
                # Always remove from playlist first
                remove_from_apple_playlist(apple_playlist_name, track)
                print(f"Removed '{track}' from playlist")
                
                # Optionally remove from library
                if remove_from_lib:
                    # First find the exact track in the playlist to get its metadata
                    playlist_track = find_playlist_track(apple_playlist_name, track)
                    if not playlist_track:
                        print(Fore.YELLOW + f"Could not find '{track}' in playlist to get metadata")
                        continue

                    # Find matching tracks using detailed metadata
                    matching_tracks = find_matching_tracks(playlist_track)
                    
                    if not matching_tracks:
                        print(Fore.YELLOW + f"No matching tracks found in library for '{track}'")
                        continue
                    
                    if len(matching_tracks) == 1:
                        # If only one match, delete it directly
                        track_obj = matching_tracks[0]['track']
                        track_obj.delete()
                        print(f"Removed '{track}' from library")
                    else:
                        # If multiple matches, let user choose
                        print(f"\nFound {len(matching_tracks)} matching tracks for '{track}':")
                        for i, t in enumerate(matching_tracks, 1):
                            print(f"{i}. {t['name']} - {t['artist']} (Album: {t['album']})")
                        print("0. Skip this track")
                        
                        while True:
                            try:
                                choice = input(f"Select which track to remove (0-{len(matching_tracks)}): ").strip()
                                if choice == '0':
                                    print(Fore.YELLOW + "Skipping track")
                                    break
                                
                                idx = int(choice) - 1
                                if 0 <= idx < len(matching_tracks):
                                    track_obj = matching_tracks[idx]['track']
                                    track_obj.delete()
                                    print(f"Removed '{matching_tracks[idx]['name']} - {matching_tracks[idx]['artist']}'")
                                    break
                                else:
                                    print(Fore.RED + "Invalid selection, try again")
                            except ValueError:
                                print(Fore.RED + "Invalid input, please enter a number")
                    
            except Exception as e:
                print(Fore.RED + f"Error removing '{track}': {e}")

    # Handle different choices
    if choice in ['2', '3']:  # Interactive selection
        print("\nEnter the numbers of the songs you want to remove (e.g., '1,2,3' or '1-3' or '1,3-5'):")
        selection = input("> ").strip()
        try:
            indices = parse_selection(selection, len(removed_tracks))
            selected_tracks = [removed_tracks[i-1] for i in indices]
            if selected_tracks:
                remove_tracks(selected_tracks, remove_from_lib=(choice == '3'))
            else:
                print(Fore.YELLOW + "No tracks selected")
        except ValueError as e:
            print(Fore.RED + f"Error: {e}")
            return

    elif choice in ['4', '5']:  # Remove all
        confirm = input(f"\nAre you sure you want to remove ALL {len(removed_tracks)} tracks? (yes/no): ").strip().lower()
        if confirm == 'yes':
            remove_tracks(removed_tracks, remove_from_lib=(choice == '5'))
        else:
            print(Fore.YELLOW + "Operation cancelled")

    print(Fore.GREEN + "\nTrack removal completed")


def main():
    colorama.init()
    selected_playlist_name, spotify_playlist_uri = select_spotify_playlist()
    apple_playlist_name = selected_playlist_name

    apple_tracks = get_apple_playlist_track_name(apple_playlist_name)
    spotify_track_data = get_spotify_playlist_track_data(spotify_playlist_uri)

    # Find tracks to add to Apple Music
    tracks_to_add = {
        track: f"https://open.spotify.com/track/{uri.split(':')[-1]}"
        for track, uri in spotify_track_data.items()
        if track not in apple_tracks
    }

    # Find tracks that were removed from Spotify but exist in Apple Music
    removed_tracks = [
        track for track in apple_tracks if track not in spotify_track_data
    ]

    if removed_tracks:
        handle_removed_tracks(apple_playlist_name, removed_tracks)

    diff_uri = tracks_to_add

    in_apple = {}
    not_in_apple = {}

    # Check each song once and categorize
    for track, uri in diff_uri.items():
        if song_exists(track):
            in_apple[track] = uri
            print(f"✅ SUCCESS: Song '{track}' was found in Apple Music playlist")
        else:
            not_in_apple[track] = uri
            # print(f"❌ FAILURE: Song '{track}' was NOT found in Apple Music playlist")

    print("\n")
    print(
        f"Songs found in Apple Music that can be added to playlist: {in_apple.keys()}"
    )

    if in_apple:
        add_songs_to_apple_playlist(apple_playlist_name, in_apple.keys())

    print("Songs that will be added to Apple Music playlist:")
    for song, uri in in_apple.items():
        print(f"- {song}: {uri}")

    print("\nSongs not found in Apple Music (skipped):")
    for song, uri in not_in_apple.items():
        print(f"- {song}: {uri}")


if __name__ == "__main__":
    try:
        while True:
            main()
            input("\nPress Enter to run again or Ctrl+C to exit...")
    except KeyboardInterrupt:
        print("\nExiting program.")
