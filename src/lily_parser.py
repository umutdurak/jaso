import re
from music21 import pitch

def parse_lilypond_file(file_path):
    """
    Rudimentary LilyPond parser focused on OpenBook style structures.
    Extracts chords from \chordmode and melody from \relative/Voice blocks.
    """
    with open(file_path, 'r') as f:
        content = f.read()

    # 1. Extract Chords
    chord_events = []
    chord_match = re.search(r'\\chordmode\s*\{([^}]+)\}', content, re.DOTALL)
    if chord_match:
        chord_block = chord_match.group(1)
        chord_events = parse_lily_chords(chord_block)

    # 2. Extract Melody
    melody_events = []
    # Find content inside the melody block
    melody_match = re.search(r'\\new Staff="Melody"\s*\{[^}]+\\relative\s+[a-g][,\']*\s*\{([^}]+)\}', content, re.DOTALL)
    if not melody_match:
        melody_match = re.search(r'\\relative\s+[a-g][,\']*\s*\{([^}]+)\}', content, re.DOTALL)
        
    if melody_match:
        melody_block = melody_match.group(1)
        melody_events = parse_lily_melody(melody_block)

    return melody_events, chord_events, []

def clean_lily_block(block):
    # Remove comments
    block = re.sub(r'%.*?\n', '', block)
    # Remove specific meta-commands and their arguments precisely
    block = re.sub(r'\\tempo\s+("[^"]+"\s+)?[\d./]+\s*=\s*[\d.]+', '', block)
    block = re.sub(r'\\time\s+[\d./]+', '', block)
    block = re.sub(r'\\key\s+\w+\s+\\\w+', '', block)
    block = re.sub(r'\\partial\s+[\d./]+', '', block)
    # Remove any other backslash commands (one-word macros)
    block = re.sub(r'\\(?:repeat|alternative|relative|clef|transpose|start\w+|end\w+|my\w+)\b', '', block)
    block = re.sub(r'\\\w+', '', block)
    # Remove strings
    block = re.sub(r'"[^"]+"', '', block)
    return block

def parse_lily_chords(block):
    events = []
    current_time = 0.0
    current_duration = 4.0 
    
    block = clean_lily_block(block)
    
    # Tokenize: chords (bes2:7), durations (1*2), and sync bars
    tokens = re.findall(r'\b[a-g][es]*[\d.]*(?:\*[\d.]+)?(?::[\w.]*)?\b|[|]', block)
    
    root_map = {
        'a': 'A', 'ais': 'A#', 'aes': 'A-', 'as': 'A-',
        'b': 'B', 'bis': 'B#', 'bes': 'B-', 'beses': 'B--',
        'c': 'C', 'cis': 'C#', 'ces': 'C-',
        'd': 'D', 'dis': 'D#', 'des': 'D-',
        'e': 'E', 'eis': 'E#', 'ees': 'E-',
        'f': 'F', 'fis': 'F#', 'fes': 'F-',
        'g': 'G', 'gis': 'G#', 'ges': 'G-',
    }

    for token in tokens:
        if token == '|':
            continue
        
        match = re.match(r'([a-g][es]*)([\d.]*)(\*[\d.]+)?(?::([\w.]*))?', token)
        if match:
            root_ly = match.group(1)
            dur_ly = match.group(2)
            multiplier = match.group(3)
            modifier = match.group(4) or ""
            
            root = root_map.get(root_ly, root_ly.capitalize())

            if dur_ly:
                val = int(re.sub(r'\D', '', dur_ly))
                current_duration = 4.0 / val
                if '.' in dur_ly: current_duration *= 1.5
            
            if multiplier:
                m_val = float(multiplier[1:])
                current_duration *= m_val
                
            chord_name = f"{root}{modifier}"
            chord_name = chord_name.replace('7', '7').replace('maj7', 'maj7').replace('dim7', 'o7').replace('m7', 'm7').replace(':', '')
            
            events.append({
                'name': chord_name,
                'time': current_time,
                'duration': current_duration
            })
            current_time += current_duration
            
    return events

def parse_lily_melody(block):
    events = []
    current_time = 0.0
    current_duration = 1.0
    prev_midi = 60 # C4
    
    block = clean_lily_block(block)
    # Remove braces left from stripped commands
    block = re.sub(r'[{}]', '', block)
    
    tokens = re.findall(r'\b[a-gr][es]*[\',]*[\d.]*\b|[|]', block)
    
    base_map = {'c': 0, 'd': 2, 'e': 4, 'f': 5, 'g': 7, 'a': 9, 'b': 11}

    for token in tokens:
        if token == '|':
            continue
            
        match = re.match(r'([a-gr][es]*)([\',]*)([\d.]*)', token)
        if match:
            pitch_ly = match.group(1)
            octave_mod = match.group(2)
            dur_ly = match.group(3)
            
            if dur_ly:
                val = int(re.sub(r'\D', '', dur_ly))
                current_duration = 4.0 / val
                if '.' in dur_ly: current_duration *= 1.5
            
            if pitch_ly == 'r':
                events.append({
                    'type': 'rest',
                    'name': 'rest',
                    'time': current_time,
                    'duration': current_duration
                })
            else:
                accidental = pitch_ly[1:]
                step = pitch_ly[0]
                
                midi_base = base_map[step]
                if accidental == 'es': midi_base -= 1
                elif accidental == 'is': midi_base += 1
                
                # Find the octave that puts us closest to prev_midi
                best_midi = -1
                min_dist = 999
                for trial_octave in range(2, 8):
                    trial_midi = (trial_octave + 1) * 12 + midi_base
                    dist = abs(trial_midi - prev_midi)
                    if dist < min_dist:
                        min_dist = dist
                        best_midi = trial_midi
                
                if octave_mod:
                    best_midi += 12 * octave_mod.count("'")
                    best_midi -= 12 * octave_mod.count(",")
                
                p = pitch.Pitch()
                p.ps = best_midi
                
                events.append({
                    'type': 'note',
                    'name': p.nameWithOctave,
                    'time': current_time,
                    'duration': current_duration,
                    'lyric': None
                })
                prev_midi = best_midi
            
            current_time += current_duration
            
    return events
