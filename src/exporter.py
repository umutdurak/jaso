import json
import xml.etree.ElementTree as ET
from music21 import articulations, chord, note, stream, clef, instrument

def export_to_musicxml(score, melody_events, optimal_melody_fingerings, parsed_chords, optimal_chord_voicings, output_xml_path):
    """
    Exports the optimized arrangement back to a MusicXML file with technical markings.
    """
    if not score:
        print("Error: No music21 score object available for export.")
        return

    # Load instrument config for accompaniment MIDI calculation
    with open("instrument_guitar_standard.json", "r") as f:
        instrument_config = json.load(f)
    open_string_midi = instrument_config.get("open_string_midi", {})
    string_order = instrument_config.get("string_order", ["e", "B", "G", "D", "A", "E"])
    string_midi_values = [open_string_midi.get(s, 0) for s in string_order]

    # 1. Apply Melody Fingerings to existing objects
    note_idx = 0
    for event in melody_events:
        if event['type'] == 'note' and 'obj' in event:
            fingering = optimal_melody_fingerings[note_idx] if note_idx < len(optimal_melody_fingerings) else None
            if fingering:
                m21_note = event['obj']
                string_val = fingering['string_idx'] + 1
                fret_val = fingering['fret']
                
                f_ind = articulations.FretIndication(fret_val)
                s_ind = articulations.StringIndication(string_val)
                m21_note.articulations = [a for a in m21_note.articulations 
                                          if not isinstance(a, (articulations.FretIndication, articulations.StringIndication))]
                m21_note.articulations.append(f_ind)
                m21_note.articulations.append(s_ind)
            note_idx += 1

    # Rename the original parts and assign proper guitar instruments
    if len(score.parts) > 0:
        score.parts[0].id = 'P1'
        score.parts[0].partName = 'Melody (Tab)'
        score.parts[0].partAbbreviation = 'Mel'
        for i_obj in score.parts[0].getInstruments():
            i_obj.instrumentName = 'Acoustic Guitar'
            i_obj.instrumentAbbreviation = 'Ac Gtr'
            i_obj.midiProgram = 25  # Steel String Guitar
        score.parts[0].insert(0, clef.TabClef())

    # 2. Create Accompaniment Part using Chord objects
    accompaniment_part = stream.Part()
    accompaniment_part.partName = 'Chords (Tab)'
    accompaniment_part.partAbbreviation = 'Chd'

    # Sync basic attributes from the template part (Time sig, Key sig)
    # Only copy the FIRST instance of each at offset 0 to avoid duplicating
    # attributes at all their original offsets, which causes extra empty measures.
    template_part = score.parts[0] if score.parts else None
    if template_part:
        from music21 import meter, key
        ts_list = template_part.flat.getElementsByClass(meter.TimeSignature)
        ks_list = template_part.flat.getElementsByClass(key.KeySignature)
        if ts_list:
            accompaniment_part.insert(0, ts_list[0])
        if ks_list:
            accompaniment_part.insert(0, ks_list[0])

    gtr = instrument.AcousticGuitar()
    gtr.midiProgram = 25
    accompaniment_part.insert(0, gtr)
    accompaniment_part.insert(0, clef.TabClef())

    # Build a mapping of chord technical data for post-processing.
    # Key: (offset, sorted tuple of MIDI pitches) -> list of (string, fret) tuples
    chord_technical_data = {}

    for i, chord_event in enumerate(parsed_chords):
        if i < len(optimal_chord_voicings) and optimal_chord_voicings[i]:
            voicing = optimal_chord_voicings[i]
            
            # Determine duration (time until next chord)
            if i < len(parsed_chords) - 1:
                dur = max(0.25, parsed_chords[i+1]['time'] - chord_event['time'])
            else:
                dur = 4.0  # Default

            # Cap duration at the next measure boundary to prevent ties
            # In the accompaniment stream, measures are at [0,4), [4,8), [8,12), ...
            t = chord_event['time']
            next_bar = (int(t / 4) + 1) * 4.0
            remaining_in_bar = next_bar - t
            dur = min(dur, remaining_in_bar)

            # Collect all fretted notes for this chord
            pitches = []
            # Build midi -> (string, fret) mapping for this chord
            midi_to_tech = {}
            for s_idx, fret in enumerate(voicing['frets']):
                if fret != -1:
                    pitch_midi = string_midi_values[s_idx] + fret
                    pitches.append(pitch_midi)
                    midi_to_tech[pitch_midi] = (s_idx + 1, fret)  # 1-indexed string

            if pitches:
                # Create a proper Chord object — all notes in one voice
                c = chord.Chord(pitches)
                c.duration.quarterLength = dur
                accompaniment_part.insert(chord_event['time'], c)

                # Store tech data keyed by offset, with midi->tech mapping
                chord_technical_data[chord_event['time']] = midi_to_tech

    score.append(accompaniment_part)

    # 3. Save the modified score
    # Count melody part measures to ensure accompaniment matches
    melody_measure_count = len(score.parts[0].getElementsByClass('Measure')) if score.parts else 0
    try:
        score.write('musicxml', fp=output_xml_path)
        # Apply Post-Processing to inject native Tab metadata and fix technical tags
        post_process_xml_for_tab(output_xml_path, chord_technical_data, melody_measure_count)
        print(f"Optimized MusicXML exported to: {output_xml_path}")
    except Exception as e:
        print(f"Failed to export MusicXML: {e}")
        import traceback
        traceback.print_exc()


def post_process_xml_for_tab(xml_path, chord_technical_data=None, melody_measure_count=0):
    """
    Post-processes the MusicXML file to:
    1. Normalize part IDs to P1, P2, ...
    2. Inject <staff-details>/<staff-tuning> for native TAB recognition
    3. Inject <technical> tags (fret/string) for accompaniment chord notes
    Also restores the DOCTYPE which ElementTree strips.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    # MusicXML staff-tuning: line 1 = bottom of staff = lowest string (low E)
    # line 6 = top of staff = highest string (high E)
    tuning_data = [
        ('E', 2), ('A', 2), ('D', 3), ('G', 3), ('B', 3), ('E', 4)
    ]

    # --- Step 1: Normalize part IDs ---
    part_list = root.find('part-list')
    parts = root.findall('part')
    
    if part_list is not None:
        score_parts = part_list.findall('score-part')
        for idx, sp in enumerate(score_parts):
            old_id = sp.get('id')
            new_id = f'P{idx + 1}'
            sp.set('id', new_id)
            
            # Also update instrument IDs within score-part
            for si in sp.findall('score-instrument'):
                si.set('id', f'I{new_id}')
            for mi in sp.findall('midi-instrument'):
                mi.set('id', f'I{new_id}')
            
            # Update matching <part> element
            for part in parts:
                if part.get('id') == old_id:
                    part.set('id', new_id)
                    break

    # --- Step 2: Force TAB clef and inject staff-details/tuning ---
    for part in root.findall('.//part'):
        for attributes in part.findall('.//attributes'):
            clef_el = attributes.find('clef')
            if clef_el is not None:
                sign = clef_el.find('sign')
                if sign is not None: sign.text = 'TAB'
                line = clef_el.find('line')
                if line is not None: line.text = '5'
            
            staff_details = attributes.find('staff-details')
            if staff_details is None:
                staff_details = ET.SubElement(attributes, 'staff-details')
            
            staff_lines = staff_details.find('staff-lines')
            if staff_lines is None:
                staff_lines = ET.SubElement(staff_details, 'staff-lines')
            staff_lines.text = '6'
            
            for existing_tuning in staff_details.findall('staff-tuning'):
                staff_details.remove(existing_tuning)
            
            for i, (step, octave) in enumerate(tuning_data):
                st = ET.SubElement(staff_details, 'staff-tuning', line=str(i+1))
                tun_step = ET.SubElement(st, 'tuning-step'); tun_step.text = step
                tun_octave = ET.SubElement(st, 'tuning-octave'); tun_octave.text = str(octave)

    # --- Step 3: Trim excess measures from accompaniment part ---
    if melody_measure_count > 0 and len(parts) > 1:
        for part in parts[1:]:  # All non-melody parts
            measures = part.findall('measure')
            for m in measures[melody_measure_count:]:
                part.remove(m)

    # --- Step 4: Inject <technical> tags for accompaniment chord notes ---
    if chord_technical_data:
        # The accompaniment is the last part (P2)
        accomp_part = root.findall('.//part')[-1] if len(root.findall('.//part')) > 1 else None
        
        if accomp_part is not None:
            _inject_chord_technical_tags(accomp_part, chord_technical_data, tuning_data)

    # --- Write back with DOCTYPE ---
    xml_str = ET.tostring(root, encoding='unicode')
    doctype = '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.1 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">\n'
    final_output = '<?xml version="1.0" encoding="UTF-8"?>\n' + doctype + xml_str
    
    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write(final_output)


def _inject_chord_technical_tags(part_el, chord_technical_data, tuning_data):
    """
    Walk through the accompaniment part's measures and inject <technical> tags
    for each chord note.
    
    chord_technical_data: { beat_offset: { midi_pitch: (string_num, fret) } }
    
    Strategy: Track the current beat position through each measure. For each note,
    calculate its MIDI pitch and look up the exact (string, fret) from the optimizer's
    data at the matching beat offset.
    """
    import xml.etree.ElementTree as ET
    
    # String open MIDI values for fallback calculation
    string_open_midi = [64, 59, 55, 50, 45, 40]  # string 1=E4 to 6=E2
    step_to_semitone = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
    
    divisions = 10080  # default
    measure_start_beat = 0.0
    beats_per_measure = 4.0
    
    # Pre-compute: round all offset keys to avoid float precision issues
    rounded_tech_data = {}
    for offset, midi_map in chord_technical_data.items():
        rounded_tech_data[round(offset, 4)] = dict(midi_map)  # copy
    
    for measure in part_el.findall('measure'):
        mnum = measure.get('number', '?')
        
        div_el = measure.find('.//divisions')
        if div_el is not None:
            divisions = int(div_el.text)
        
        ts_el = measure.find('.//time')
        if ts_el is not None:
            b = ts_el.find('beats')
            if b is not None:
                beats_per_measure = float(b.text)
        
        current_offset_divs = 0
        pending_dur = 0  # Duration of the current "first note" to defer
        
        for note_el in measure.findall('note'):
            # Skip rests — but first, apply any pending duration
            rest_el = note_el.find('rest')
            if rest_el is not None:
                current_offset_divs += pending_dur
                pending_dur = 0
                dur_el = note_el.find('duration')
                if dur_el is not None:
                    current_offset_divs += int(dur_el.text)
                continue
            
            chord_tag = note_el.find('chord')
            pitch_el = note_el.find('pitch')
            dur_el = note_el.find('duration')
            
            if pitch_el is None:
                if dur_el is not None and chord_tag is None:
                    current_offset_divs += pending_dur
                    pending_dur = 0
                    current_offset_divs += int(dur_el.text)
                continue
            
            # For a new "first note" (no <chord/> tag), apply any pending
            # duration from the previous first note before computing position
            if chord_tag is None:
                current_offset_divs += pending_dur
                pending_dur = 0
            
            # Calculate MIDI pitch from XML
            step = pitch_el.find('step').text
            octave = int(pitch_el.find('octave').text)
            alter_el = pitch_el.find('alter')
            alter = int(float(alter_el.text)) if alter_el is not None else 0
            midi_val = (octave + 1) * 12 + step_to_semitone[step] + alter
            
            # Calculate current beat position (same for all <chord/> notes)
            beat_pos = round(measure_start_beat + current_offset_divs / divisions, 4)
            
            # Look up this beat's chord technical data
            best_string = None
            best_fret = None
            
            if beat_pos in rounded_tech_data:
                midi_map = rounded_tech_data[beat_pos]
                if midi_val in midi_map:
                    best_string, best_fret = midi_map[midi_val]
            
            # Fallback: try nearby beat positions (float rounding tolerance)
            if best_string is None:
                for offset_key, midi_map in rounded_tech_data.items():
                    if abs(offset_key - beat_pos) < 0.25:
                        if midi_val in midi_map:
                            best_string, best_fret = midi_map[midi_val]
                            break
            
            # Last resort fallback: compute from MIDI (pick lowest fret)
            if best_string is None:
                for s_idx, open_midi in enumerate(string_open_midi):
                    fret = midi_val - open_midi
                    if 0 <= fret <= 24:
                        if best_fret is None or fret < best_fret:
                            best_string = s_idx + 1
                            best_fret = fret
            
            if best_string is not None and best_fret is not None:
                # Find or create <notations>
                notations = note_el.find('notations')
                if notations is None:
                    notations = ET.SubElement(note_el, 'notations')
                
                # Find or create <technical>
                technical = notations.find('technical')
                if technical is None:
                    technical = ET.SubElement(notations, 'technical')
                
                # Remove existing fret/string if any
                for existing in technical.findall('fret'):
                    technical.remove(existing)
                for existing in technical.findall('string'):
                    technical.remove(existing)
                
                fret_el = ET.SubElement(technical, 'fret')
                fret_el.text = str(best_fret)
                string_el = ET.SubElement(technical, 'string')
                string_el.text = str(best_string)
            
            # Defer offset advance for "first notes" — chord notes share the same offset
            if chord_tag is None and dur_el is not None:
                pending_dur = int(dur_el.text)
        
        # Apply any remaining pending duration at end of measure
        current_offset_divs += pending_dur
        
        measure_start_beat += beats_per_measure
