import re

def get_melody_fingering(note_name):
    # Simple mapping of note names (e.g., 'C4', 'G#5') to guitar strings/frets
    # prioritizing higher strings (e, B, G) for melody.
    
    # 0: 'e', 1: 'B', 2: 'G', 3: 'D', 4: 'A', 5: 'E'
    string_notes = [64, 59, 55, 50, 45, 40] 
    
    # Map note name to MIDI number
    from music21 import pitch
    try:
        p = pitch.Pitch(note_name)
        midi = p.ps
    except:
        return None
        
    # Find the first string where this note can be played (fret <= 15)
    for i, open_midi in enumerate(string_notes):
        fret = int(midi - open_midi)
        if 0 <= fret <= 15:
            return i, fret
            
    return None

def generate_tablature(melody_events, parsed_chords, sections, optimal_chord_voicings, output_file):
    # Generates the tablature and writes it to the output file.

    ordered_strings = ['e', 'B', 'G', 'D', 'A', 'E']

    # --- Timeline Creation ---
    timeline = []
    
    # Calculate implied duration by checking distance to next chord
    for i, chord in enumerate(parsed_chords):
        if optimal_chord_voicings[i]:
            start_time = chord.get('time', 0.0)
            
            # Determine how long this chord lasts (until the next chord starts)
            if i < len(parsed_chords) - 1:
                next_start = parsed_chords[i+1].get('time', start_time)
                implied_duration = next_start - start_time
            else:
                # Default for the very last chord
                implied_duration = 4.0 

            timeline.append({
                'time': start_time,
                'type': 'chord',
                'duration': implied_duration,
                'name': chord['name'],
                'voicing': optimal_chord_voicings[i]
            })

    # Add melody events to timeline
    if melody_events:
        for event in melody_events:
            if event['type'] == 'note':
                fingering = get_melody_fingering(event['name'])
                if fingering:
                    timeline.append({
                        'time': event['time'],
                        'type': 'melody_note',
                        'name': event['name'],
                        'duration': event['duration'],
                        'string_idx': fingering[0],
                        'fret': fingering[1]
                    })
            
            if event.get('lyric'):
                timeline.append({
                    'time': event['time'],
                    'type': 'lyric',
                    'text': event['lyric'],
                    'duration': event['duration']
                })
            
    # Add sections to timeline
    if sections:
        for section in sections:
            timeline.append({
                'time': section['time'],
                'type': 'section',
                'name': section['name'],
                'duration': 0.0
            })

    timeline.sort(key=lambda x: x['time'])

    print("--- Timeline Debug ---")
    for t in timeline:
        if t['type'] == 'chord':
            print(f"Chord: {t['name']:<15} Time: {t['time']:<5} Duration: {t['duration']}")
        elif t['type'] == 'section':
            print(f"Section: {t['name']:<13} Time: {t['time']:<5}")

    # --- Tablature Generation ---
    CHAR_PER_QUARTER_NOTE = 4 # 1/16th note resolution. 2 digits is 1/8th note width.
    BEATS_PER_MEASURE = 4
    MEASURES_PER_LINE = 4

    total_duration = max(event['time'] + event['duration'] for event in timeline) if timeline else 0
    num_measures = int(total_duration / BEATS_PER_MEASURE) + 1

    output_lines = ["--- Chord Tablature ---"]

    for line_start_measure in range(0, num_measures, MEASURES_PER_LINE):
        line_end_measure = min(line_start_measure + MEASURES_PER_LINE, num_measures)
        
        line_section = ""
        line_chords_label = "Chords: "
        line_chord_tab = {s: f"{s.upper()}:    " for s in ordered_strings}
        
        line_melody_tab = {s: f"{s.upper()}:    " for s in ordered_strings}
        line_lyrics = "Lyrics: "

        for m in range(line_start_measure, line_end_measure):
            measure_start_time = m * BEATS_PER_MEASURE
            measure_end_time = (m + 1) * BEATS_PER_MEASURE
            measure_width = CHAR_PER_QUARTER_NOTE * BEATS_PER_MEASURE

            # Grids for this specific measure
            m_chord_grid = {s: ['-'] * measure_width for s in ordered_strings}
            m_chord_names = [' '] * measure_width
            
            m_melody_grid = {s: ['-'] * measure_width for s in ordered_strings}
            m_lyrics_grid = [' '] * measure_width
            
            # Populate grids with events
            for event in timeline:
                if measure_start_time <= event['time'] < measure_end_time:
                    pos = int((event['time'] - measure_start_time) * CHAR_PER_QUARTER_NOTE)
                    
                    if event['type'] == 'section':
                        line_section += f"[{event['name']}] "
                    
                    elif event['type'] == 'chord':
                        # Chord name above its staff
                        for i, char in enumerate(event['name']):
                            if pos + i < measure_width:
                                m_chord_names[pos + i] = char
                        # Chord voicing on its staff
                        voicing = event['voicing']
                        for i, s_name in enumerate(ordered_strings):
                            fret = voicing['frets'][i]
                            fret_char = str(fret) if fret != -1 else 'x'
                            for char_idx, char in enumerate(fret_char):
                                if pos + char_idx < measure_width:
                                    m_chord_grid[s_name][pos + char_idx] = char

                    elif event['type'] == 'melody_note':
                        # Melody fret on its staff
                        s_idx = event['string_idx']
                        s_name = ordered_strings[s_idx]
                        fret_str = str(event['fret'])
                        for char_idx, char in enumerate(fret_str):
                            if pos + char_idx < measure_width:
                                m_melody_grid[s_name][pos + char_idx] = char

                    elif event['type'] == 'lyric':
                        lyric_text = event['text']
                        for i, char in enumerate(lyric_text):
                            if pos + i < measure_width:
                                m_lyrics_grid[pos + i] = char

            # Append measure grids to line strings
            line_chords_label += "|" + "".join(m_chord_names)
            for s in ordered_strings:
                line_chord_tab[s] += "|" + "".join(m_chord_grid[s])
                line_melody_tab[s] += "|" + "".join(m_melody_grid[s])
            line_lyrics += "|" + "".join(m_lyrics_grid)

        # Build final output block
        output_lines.append("")
        if line_section.strip():
            output_lines.append("        " + line_section.strip())
            
        output_lines.append("--- Chords (Accompaniment) ---")
        output_lines.append(line_chords_label + "|")
        for s in ordered_strings:
            output_lines.append(line_chord_tab[s] + "|")
            
        output_lines.append("--- Melody (Lead) ---")
        for s in ordered_strings:
            output_lines.append(line_melody_tab[s] + "|")
            
        if any(c != ' ' and c != '|' for c in line_lyrics[8:]):
             output_lines.append(line_lyrics + "|")

    # --- Write to File ---
    with open(output_file, 'w') as f:
        f.write("\n".join(output_lines))

    print(f"Tablature generated and saved to {output_file}")
