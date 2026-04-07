import numpy as np

# Normalise un signal entre 0 et 1 
def normalize_signal(signal):
    # Gestion du cas d'un signal vide
    if len(signal) == 0:
        return signal

    min_val = np.min(signal)
    max_val = np.max(signal)

    # Évite la division par zéro si le signal est constant
    if max_val - min_val == 0:
        return signal

    # Normalisation : (x - min) / (max - min)
    return (signal - min_val) / (max_val - min_val)


def moving_average(data, window_size=7):
    return np.convolve(data, np.ones(window_size) / window_size, mode='same')

# Fusionne les segments proches pour éviter des coupures trop fréquentes
def merge_close_segments(segments, max_gap_frames):
    # Cas sans segments
    if not segments:
        return []
    
    # Tri des segments par ordre chronologique
    segments = sorted(segments, key=lambda x: x[0])
    merged = [segments[0]]

    for current_start, current_end in segments[1:]:
        last_start, last_end = merged[-1]
        # Si deux segments sont suffisamment proches, on les fusionne
        if current_start - last_end <= max_gap_frames:
            merged[-1] = (last_start, max(last_end, current_end))
        else:
            # Sinon, on ajoute un nouveau segment
            merged.append((current_start, current_end))

    return merged