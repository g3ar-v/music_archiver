on run {input_file, playlist_name}
    -- Check if input parameters are provided
    if input_file is "" or playlist_name is "" then
        error "Both file path and playlist name are required."
    end if
    
    try
        -- Convert POSIX path to alias and verify file exists
        set track_file to (POSIX file input_file) as alias
        
        tell application "Music"
            -- Ensure Music is running
            if not running then
                error "Apple Music is not running. Please launch it first."
            end if
            
            -- Check if playlist exists
            if not (exists playlist playlist_name) then
                error "Playlist '" & playlist_name & "' does not exist."
            end if
            
            -- Add the track to playlist
            add track_file to playlist playlist_name
            
            return "Successfully added '" & (POSIX path of track_file) & "' to playlist '" & playlist_name & "'"
        end tell
        
    on error error_message
        error "Error: " & error_message
    end try
end run

