# Finds the optimal chord progression based on ease of playing.
import math

def calculate_transition_cost(voicing1, voicing2):
    # Calculates the cost of transitioning between two chord voicings.
    # The cost is the sum of the distances each finger travels.

    # Assumes voicings are dictionaries with a 'frets' key.
    # A value of -1 or 'x' can represent a muted string.
    cost = 0
    for fret1, fret2 in zip(voicing1['frets'], voicing2['frets']):
        # Ignore muted strings in the calculation
        if isinstance(fret1, int) and isinstance(fret2, int) and fret1 >= 0 and fret2 >= 0:
            cost += abs(fret1 - fret2)
    return cost


def find_optimal_progression(parsed_lilypond_chords, chord_library):
    # This function finds the optimal chord progression.
    # It uses a dynamic programming approach (Viterbi-like algorithm).

    # Map LilyPond chord symbols to standard chord names
    # For now, we assume the parsed chords are simple note names (e.g., 'c', 'g')
    # and convert them to uppercase to match the chord library keys.
    standard_chord_names = [lp_chord.upper() for lp_chord in parsed_lilypond_chords]

    print("\n--- Optimization Process ---")
    print(f"Standardized Chord Progression: {standard_chord_names}")

    # Initialize dynamic programming table
    # dp[i][j] will store the minimum cost to reach voicing j of chord i
    # and the path to get there.
    dp = []
    paths = []

    # First chord: no transition cost, so cost is 0 for all its voicings
    first_chord_name = standard_chord_names[0]
    if first_chord_name not in chord_library:
        print(f"Error: Chord {first_chord_name} not found in library.")
        return []

    first_chord_voicings = chord_library[first_chord_name]
    dp.append([(0, None)] * len(first_chord_voicings)) # (cost, previous_voicing_index)
    paths.append([[idx] for idx in range(len(first_chord_voicings))])

    # Iterate through the rest of the chords
    for i in range(1, len(standard_chord_names)):
        current_chord_name = standard_chord_names[i]
        if current_chord_name not in chord_library:
            print(f"Error: Chord {current_chord_name} not found in library.")
            return []

        current_chord_voicings = chord_library[current_chord_name]
        prev_chord_voicings = chord_library[standard_chord_names[i-1]]

        current_dp_row = []
        current_paths_row = []

        for j, current_voicing in enumerate(current_chord_voicings):
            min_cost = float('inf')
            best_prev_idx = -1

            for k, prev_voicing in enumerate(prev_chord_voicings):
                transition_cost = calculate_transition_cost(prev_voicing, current_voicing)
                total_cost = dp[i-1][k][0] + transition_cost

                if total_cost < min_cost:
                    min_cost = total_cost
                    best_prev_idx = k
            
            current_dp_row.append((min_cost, best_prev_idx))
            # Reconstruct path: take path of best_prev_idx and append current_voicing_idx
            current_paths_row.append(paths[i-1][best_prev_idx] + [j])
        
        dp.append(current_dp_row)
        paths.append(current_paths_row)

    # Find the overall minimum cost path in the last row
    last_row_costs = [item[0] for item in dp[-1]]
    min_total_cost = float('inf')
    best_last_voicing_idx = -1

    for idx, cost in enumerate(last_row_costs):
        if cost < min_total_cost:
            min_total_cost = cost
            best_last_voicing_idx = idx

    optimal_path_indices = paths[-1][best_last_voicing_idx]
    
    # Convert indices to actual voicings
    optimal_voicings = []
    for i, voicing_idx in enumerate(optimal_path_indices):
        chord_name = standard_chord_names[i]
        optimal_voicings.append(chord_library[chord_name][voicing_idx])

    print(f"Optimal Total Cost: {min_total_cost}")
    print(f"Optimal Voicing Path (indices): {optimal_path_indices}")
    # print(f"Optimal Voicing Path (details): {optimal_voicings}") # Too verbose for now

    return optimal_voicings