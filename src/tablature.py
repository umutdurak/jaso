import re
import json
from .optimizer import find_optimal_melody_path

def generate_tablature(melody_events, parsed_chords, sections, optimal_chord_voicings, output_file):
    # Generates the tablature and writes it to the output file.
    
    # Load configuration
    with open("app_config.json", "r") as f:
        app_config = json.load(f)
    with open("instrument_guitar_standard.json", "r") as f:
        instrument_config = json.load(f)

    ordered_strings = instrument_config.get("string_order", ["e", "B", "G", "D", "A", "E"])
    
    layout_cfg = app_config.get("layout", {})
    BEATS_PER_MEASURE = layout_cfg.get("beats_per_measure", 4)
    MEASURES_PER_LINE = layout_cfg.get("measures_per_line", 2)
    GLOBAL_CPQN = layout_cfg.get("global_cpqn", 12)

    # --- Melody Optimization ---
    # Find the most playable path for the melody notes
    optimal_melody_fingerings = find_optimal_melody_path(melody_events)
    
    # --- Timeline Creation ---
    timeline = []
    
    # Calculate implied duration by checking distance to next chord
    optimizer_cfg = app_config.get("optimizer", {})
    default_chord_dur = optimizer_cfg.get("default_chord_duration", 4.0)

    for i, chord in enumerate(parsed_chords):
        if optimal_chord_voicings[i]:
            start_time = chord.get('time', 0.0)
            
            # Determine how long this chord lasts (until the next chord starts)
            if i < len(parsed_chords) - 1:
                next_start = parsed_chords[i+1].get('time', start_time)
                implied_duration = next_start - start_time
            else:
                # Default for the very last chord
                implied_duration = default_chord_dur

            timeline.append({
                'time': start_time,
                'type': 'chord',
                'duration': implied_duration,
                'name': chord['name'],
                'voicing': optimal_chord_voicings[i]
            })

    # Add melody events to timeline
    if melody_events:
        note_idx = 0
        for event in melody_events:
            if event['type'] == 'note':
                fingering = optimal_melody_fingerings[note_idx] if note_idx < len(optimal_melody_fingerings) else None
                if fingering:
                    timeline.append({
                        'time': event['time'],
                        'type': 'melody_note',
                        'name': event['name'],
                        'duration': event['duration'],
                        'string_idx': fingering['string_idx'],
                        'fret': fingering['fret']
                    })
                note_idx += 1
            
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
    total_duration = max(event['time'] + event['duration'] for event in timeline) if timeline else 0
    num_measures = int(total_duration / BEATS_PER_MEASURE) + 1

    print(f"Using Fixed Global CPQN: {GLOBAL_CPQN} (Uniform measure width: {GLOBAL_CPQN * BEATS_PER_MEASURE})")

    output_lines = ["--- Chord Tablature ---"]
    
    for line_start_m in range(0, num_measures, MEASURES_PER_LINE):
        line_end_m = min(line_start_m + MEASURES_PER_LINE, num_measures)
        
        line_section = ""
        LABEL_WIDTH = 8
        line_chords_label = "Chords: ".ljust(LABEL_WIDTH)
        line_chord_tab = {s: f"{s.upper()}:".ljust(LABEL_WIDTH) for s in ordered_strings}
        line_melody_tab = {s: f"{s.upper()}:".ljust(LABEL_WIDTH) for s in ordered_strings}
        line_lyrics = "Lyrics: ".ljust(LABEL_WIDTH)

        for cur_m in range(line_start_m, line_end_m):
            measure_start_time = cur_m * BEATS_PER_MEASURE
            measure_end_time = (cur_m + 1) * BEATS_PER_MEASURE
            measure_width = GLOBAL_CPQN * BEATS_PER_MEASURE

            # Grids for this specific measure
            m_chord_grid = {s: ['-'] * measure_width for s in ordered_strings}
            m_chord_names = [' '] * measure_width
            m_melody_grid = {s: ['-'] * measure_width for s in ordered_strings}
            m_lyrics_grid = [' '] * measure_width
            
            # Populate grids
            for event in timeline:
                if measure_start_time <= event['time'] < measure_end_time:
                    pos = int((event['time'] - measure_start_time) * GLOBAL_CPQN)
                    
                    if event['type'] == 'section':
                        line_section += f"[{event['name']}] "
                    
                    elif event['type'] == 'chord':
                        for i, char in enumerate(event['name']):
                            if pos + i < measure_width:
                                m_chord_names[pos + i] = char
                        voicing = event['voicing']
                        for i, s_name in enumerate(ordered_strings):
                            fret = voicing['frets'][i]
                            fret_char = str(fret) if fret != -1 else 'x'
                            for char_idx, char in enumerate(fret_char):
                                if pos + char_idx < measure_width:
                                    m_chord_grid[s_name][pos + char_idx] = char

                    elif event['type'] == 'melody_note':
                        # Find string index from the string_order
                        s_idx = event['string_idx']
                        # The timeline 'string_idx' is 0-5 mapping to e-E
                        s_name = ordered_strings[s_idx]
                        fret_str = str(event['fret'])
                        for char_idx, char in enumerate(fret_str):
                            if pos + char_idx < measure_width:
                                m_melody_grid[s_name][pos + char_idx] = char

                    elif event['type'] == 'lyric':
                        lyric_text = event['text']
                        if not lyric_text: continue
                        if not lyric_text.endswith('-') and not lyric_text.endswith(' '):
                            lyric_text += ' '
                        for i, char in enumerate(lyric_text):
                            if pos + i < measure_width:
                                m_lyrics_grid[pos + i] = char

            # Append measure grids
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
        if any(c != ' ' and c != '|' for c in line_lyrics[LABEL_WIDTH:]):
             output_lines.append(line_lyrics + "|")

    # --- Write to File ---
    with open(output_file, 'w') as f:
        f.write("\n".join(output_lines))

    print(f"Tablature generated and saved to {output_file}")
