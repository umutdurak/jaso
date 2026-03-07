from music21 import converter, note, chord, harmony, text, expressions
from .lily_parser import parse_lilypond_file

def parse_score_file(file_path):
    """
    Dispatcher to choose the right parser based on file extension.
    """
    if file_path.endswith('.ly'):
        return parse_lilypond_file(file_path)
    else:
        # Default to MusicXML for .mxl, .xml, .musicxml
        return parse_musicxml_file(file_path)

def parse_musicxml_file(file_path):
    # Parses a MusicXML file using music21 and extracts notes and chords.

    # :param file_path: The absolute path to the .musicxml file.
    # :return: A tuple containing lists: (melody_events, chord_events, section_events).
    melody_events = []
    chord_events = []
    section_events = []
    try:
        # music21 can parse MusicXML natively without external executables
        score = converter.parse(file_path)

        # Use .flat to get a single, iterable stream of all elements
        for element in score.flat.notesAndRests:
            # Check for explicitly assigned lyrics
            lyric_text = element.lyric if hasattr(element, 'lyric') and element.lyric else None
            
            if isinstance(element, note.Note):
                melody_events.append({'time': float(element.offset), 'type': 'note', 'name': element.nameWithOctave, 'duration': element.duration.quarterLength, 'lyric': lyric_text})
            elif isinstance(element, note.Rest):
                melody_events.append({'time': float(element.offset), 'type': 'rest', 'name': element.name, 'duration': element.duration.quarterLength, 'lyric': lyric_text})
            elif isinstance(element, chord.Chord):
                # This handles melodic chords, not chord symbols
                melody_events.append({'time': float(element.offset), 'type': 'melodic_chord', 'name': element.pitchedCommonName, 'duration': element.duration.quarterLength, 'lyric': lyric_text})

        # To get chord symbols, we need to find them specifically.
        # They are often in a different part of the stream.
        for element in score.flat.getElementsByClass(harmony.Harmony):
            chord_events.append({'name': element.figure, 'time': float(element.offset), 'duration': element.duration.quarterLength})

        # Find Rehearsal Marks (e.g. A, B, C sections) and Text annotations
        for element in score.flat.getElementsByClass(expressions.RehearsalMark):
            section_events.append({'name': element.content, 'time': float(element.offset)})
            
        if not melody_events and not chord_events:
            print("Warning: Could not find any notes or chords in the file.")

        return melody_events, chord_events, section_events

    except FileNotFoundError:
        print(f"Error: MusicXML file not found at {file_path}")
        return None, None, None
    except Exception as e:
        print(f"An error occurred with music21 during MusicXML parsing: {e}")
        return None, None, None
