from music21 import environment

# Get the music21 environment object
us = environment.UserSettings()

# The path we found using 'which lilypond'
lilypond_path = '/opt/homebrew/bin/lilypond'

# Set the path in the music21 settings
us['lilypondPath'] = lilypond_path

print(f"Successfully set music21 lilypondPath to: {us['lilypondPath']}")
print(f"Verified music21 lilypondPath: {environment.get('lilypondPath')}")
