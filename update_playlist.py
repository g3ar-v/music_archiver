from appscript import app
import subprocess
import appscript
import spotipy
import colorama
from colorama import Fore
from spotipy.oauth2 import SpotifyOAuth


def get_spotify_playlist_track_data(playlist_uri):
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope="playlist-read-private"))
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
    music = appscript.app("Music")
    playlist = music.playlists[apple_playlist]
    tracks = [track.name() for track in playlist.tracks()]
    return tracks


def song_exists(song_name):
    music = app("Music")
    tracks = music.tracks.get()
    print("\n")
    print(f"Checking if song '{song_name}' exists in Apple Music...")
    for track in tracks:
        if track.name() == song_name:
            print(Fore.GREEN + f"Song '{song_name}' found in Apple Music." + Fore.RESET)
            return True
    print(Fore.RED + f"Song '{song_name}' not found in Apple Music." + Fore.RESET)
    return False


def get_user_playlists():
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope="playlist-read-private"))
    playlists = sp.current_user_playlists()
    user_playlists = {
        playlist["name"]: playlist["uri"] for playlist in playlists["items"]
    }
    return user_playlists


def select_spotify_playlist():
    user_playlists = get_user_playlists()
    print("Available Spotify Playlists:")
    for index, (name, uri) in enumerate(user_playlists.items(), start=1):
        print(f"{index}. {name} - {uri}")

    choice = int(input("Select a playlist by number: ")) - 1
    selected_playlist_name = list(user_playlists.keys())[choice]
    selected_playlist_uri = user_playlists[selected_playlist_name]
    return selected_playlist_name.strip(), selected_playlist_uri


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


def main():
    colorama.init()
    selected_playlist_name, spotify_playlist_uri = select_spotify_playlist()
    apple_playlist_name = selected_playlist_name

    apple_track = get_apple_playlist_track_name(apple_playlist_name)
    spotify_track_data = get_spotify_playlist_track_data(spotify_playlist_uri)

    diff_uri = {
        track: f"https://open.spotify.com/track/{uri.split(':')[-1]}"
        for track, uri in spotify_track_data.items()
        if track not in apple_track
    }

    in_apple = {}
    not_in_apple = {}
    
    # Check each song once and categorize
    for track, uri in diff_uri.items():
        if song_exists(track):
            in_apple[track] = uri
        else:
            not_in_apple[track] = uri

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
    main()
