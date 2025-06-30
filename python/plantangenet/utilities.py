# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

def smtpe_from_stamp(stamp, fps):
    """Return simulation stamp formatted as SMPTE timecode."""
    total_seconds = int(stamp)
    frames = int((stamp % 1.0) * fps)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02}:{minutes:02}:{seconds:02}:{frames:03}"


def midi_time_from_stamp(stamp, fps):
    """Return stamp as MIDI-style timecode (HH:MM:SS.FFFF)."""
    total_seconds = int(stamp)
    fractional = (stamp % 1.0) * fps
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02}:{minutes:02}:{seconds:02}:{fractional:06.3f}"


def samples_from_stamp(stamp, rate):
    """Return stamp in samples based on a given sample rate."""
    return int(stamp * rate)


def tick_count_from_stamp(stamp, ppqn, bpm) -> int:
    """Return stamp in notes based on pulses per quarter note."""
    return int(beat_count_from_stamp(stamp, bpm) * ppqn)


def beat_count_from_stamp(stamp, bpm) -> float:
    """Return stamp in beats based on pulses per quarter note."""
    return stamp * (bpm / 60.0)


def conductor_time_from_stamp(stamp, bpm, ppqn, time_sig):
    beats = beat_count_from_stamp(stamp, bpm)
    bars = int(beats // time_sig[0])
    beat_in_bar = int(beats % time_sig[0])
    tick = int((beats % 1.0) * ppqn)

    full_beats_to_next_bar = (bars + 1) * time_sig[0] - beats
    ticks_until_next_downbeat = int(full_beats_to_next_bar * ppqn)

    next_bar_starts = (bars + 1) * time_sig[0]
    return {
        "bar": bars + 1,
        "beat": beat_in_bar + 1,
        "tick": tick,
        "time_signature": time_sig,
        "bars_beats_ticks": f"{(bars + 1):02}:{(beat_in_bar + 1):02}:{tick:03}",
        "beats_until_next_bar": full_beats_to_next_bar,
        "beats_elapsed": beats,
        "next_bar_at_beat": next_bar_starts,
        "ticks_until_next_downbeat": f"{ticks_until_next_downbeat}"
    }
