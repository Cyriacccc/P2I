import numpy as np


def normalize_signal(signal):
    if len(signal) == 0:
        return signal

    min_val = np.min(signal)
    max_val = np.max(signal)

    if max_val - min_val == 0:
        return signal

    return (signal - min_val) / (max_val - min_val)


def moving_average(data, window_size=7):
    return np.convolve(data, np.ones(window_size) / window_size, mode='same')


def merge_close_segments(segments, max_gap_frames):
    if not segments:
        return []

    segments = sorted(segments, key=lambda x: x[0])
    merged = [segments[0]]

    for current_start, current_end in segments[1:]:
        last_start, last_end = merged[-1]

        if current_start - last_end <= max_gap_frames:
            merged[-1] = (last_start, max(last_end, current_end))
        else:
            merged.append((current_start, current_end))

    return merged