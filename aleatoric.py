# Max Janisse (c) 2026
# <mjanisse@pdx.edu>
import scipy.io.wavfile as wav
import numpy as np
import sounddevice as sd
import mido
import argparse
import random

song_structs = [
    "AABB/CC",
    "ABAB/CD",
    "AB/CDDD"
]

chord_loops = [
    "I-IV-ii-V",
    "I-vi-ii-V",
    "I-iii-IV-iv",
    "I-V-ii-V",
    "I-vi-IV-V",
    "IV-I-vi-IV",
    "I-V-vi-I",
    "I-IV-iv-I",
    "IV-V-I-I",
    "vi-IV-I-V"
]

notes = ['C', 'D♭/C♯', 'D', 'E♭/D♯', 'E', 'F', 'G♭/F♯', 'G', 'A♭/G♯', 'A', 'B♭/A♯', 'B']

note_durations = {
    "whole": (1920, 4.0, 1),
    "half": (960, 2.0, 2),
    "quarter": (480, 1.0, 4),
    "eighth": (240, 0.5, 8),
    "sixteenth": (120, 0.25, 16)
}

def midi_to_note(midi):
    note_idx = midi % 12
    octave = (midi // 12) - 1
    freq = midi_to_freq(midi)
    return (notes[note_idx], octave, freq, midi)

def midi_to_freq(midi): return 440 * (2 ** ((midi - 69) / 12))

def parse_progression(progression):
    for p in progression.split('-'):
        match p:
            case 'I': yield 0
            case 'ii': yield 1
            case 'iii': yield 2
            case 'IV' | 'iv': yield 3
            case 'V': yield 4
            case 'vi': yield 5
            case _: raise ValueError(f"unexpected progression '{p}'")

def generate_sawtooth(f, t, harmonics=50):
    sawtooth_fourier = np.zeros_like(t)

    for k in range(1, harmonics + 1):
        sawtooth_fourier += ((-1)**(k+1)) * (np.sin(2 * np.pi * k * f * t) / k)

    sawtooth_fourier *= (2 / np.pi)
    return sawtooth_fourier

def get_note_duration(note_type, bpm):
    """
    Calculates the duration of a note in seconds.

    note_type: 'whole', 'half', 'quarter', 'eighth', 'sixteenth'
    bpm: beats per minute (assuming 4/4 time)
    """
    beat_multipliers = { k: multiplier for k, [_, multiplier, _] in note_durations.items() }

    if note_type not in beat_multipliers:
        raise ValueError(f"Unknown note type: {note_type}")

    seconds_per_beat = 60.0 / bpm
    return seconds_per_beat * beat_multipliers[note_type]

def generate_midi_msgs(wave, values, channel, note_type):
    tick_durations = {k: ticks for k, [ticks, _, _] in note_durations.items()}
    for m,[v_on, v_off] in values:
        wave.append(mido.Message("note_on", note=m, velocity=v_on, channel=channel, time=0))
        wave.append(mido.Message("note_off", note=m, velocity=v_off, channel=channel, time=tick_durations[note_type]))

def determine_chord_scales(chords_by_label, major_scale):
    g = {}
    for line, chords in chords_by_label.items():
        g[line] = []
        for i in chords.split('-'):
            x = list(parse_progression(i))[0]
            w = (x + 2) % len(major_scale)
            u = (x + 4) % len(major_scale)
            a = [major_scale[j] for j in [x, w, u]]

            g[line].append(a)
    return g

def determine_amplitude(db): return 10 ** (db / 20)

def main(args):
    samplerate = 48000

    amplitude = determine_amplitude(args.volume) * np.iinfo(np.int16).max
    song_struct = song_structs[random.randint(0, len(song_structs)-1)]
    chords = random.sample(chord_loops, k=4)
    chords_by_label = {c[0]: c[1] for c in zip(['A','B','C','D'], chords)}

    note, octave, _, _ = midi_to_note(args.key)
    major_scale_midi = [args.key + i for i in [0, 2, 4, 5, 7, 9, 11]]
    major_scale = [midi_to_note(i) for i in major_scale_midi]

    note_types = list(note_durations.keys())
    note_type = args.melody if not args.rhythm else random.choice(note_types)
    chorus_note_type = random.choice(note_types)

    chord_scales_by_label = determine_chord_scales(chords_by_label, major_scale)

    if args.verbose:
        print(f"Key: {note}{octave} ({args.key})")
        print(f"Major Scale Notes: {[midi_to_note(i)[0] for i in major_scale_midi]}")
        print(f"Structure: {song_struct}")
        for k,v in chords_by_label.items():
            print(f"    {k}: {v:^11} -> {[d[0] for d in chord_scales_by_label[k]]}")
        print(f"Tempo: {args.tempo} bpm")
        if not args.rhythm:
            print(f"Note Type: {note_type.title()} notes")
        if not args.midi:
            print(f"Output: {args.output if args.output is not None else "Audio Out"}")
        else:
            print(f"Output: MIDI")
            print(f"    Device: '{args.midi_device}'")
        print(f"Generate Bass: {args.bass}")
        print(f"Generate Harmony: {args.harmony}")
        print(f"Generate Rhythm: {args.rhythm}")
        if args.rhythm:
            print(f"    Verse: {note_type.title()} notes")
            print(f"    Chorus: {chorus_note_type.title()} notes")
        print(f"Generate Drums: {args.drums}")
        print()

    chord_scale_note = np.linspace(
        0,
        get_note_duration("whole", args.tempo),
        int(samplerate * get_note_duration("whole", args.tempo)),
        endpoint=False
    )
    
    melody = []
    bass = []
    harmony = []
    drums = []
    line_cache = {}
    print("Generating music...")
    for label in song_struct:
        if label == "/":
            if args.rhythm:
                note_type = chorus_note_type
            continue

        t = np.linspace(
            0,
            get_note_duration(note_type, args.tempo),
            int(samplerate * get_note_duration(note_type, args.tempo)),
            endpoint=False
        ) if not args.midi else None

        wave = []
        chord_scales = chord_scales_by_label[label]
        note_type_count = note_durations[note_type][2]
        line_notes, harmony_notes = ([], []) if label not in line_cache else line_cache[label]
        if not line_notes and not harmony_notes:
            for chord_scale in chord_scales:
                for _ in range(note_type_count):
                    use_chord_note = random.random() < 0.8
                    chord_scale_note = random.choice(chord_scale)

                    line_notes.append(chord_scale_note if use_chord_note else random.choice(major_scale))

                    if args.harmony:
                        harmony_notes.append(chord_scale[0])
        if args.midi:
            values = [(midi, [64,64]) for _,_,_,midi in line_notes]
            generate_midi_msgs(wave, values, 0, note_type)
        else:
            wave = np.concatenate([generate_sawtooth(f, t) for _,_,f,_ in line_notes])

        melody.append(wave)

        if label not in line_cache:
            line_cache[label] = (line_notes, harmony_notes)

        if args.drums:
            wave = []
            n = [midi_to_note(35)] * 32
            if args.midi:
                values = [(i, [100,100]) for i in [midi for _,_,_,midi in n]]
                generate_midi_msgs(wave, values, 9, "eighth")
            else:
                raise ValueError("Not Implemented")

            drums.append(wave)

        if args.harmony:
            arg = 3 if args.midi else 2
            n = [y[arg] for y in harmony_notes]
            wave = []
            if args.midi:
                values = [(m, [64,64]) for m in n]
                print("harmony: ", len(values))
                generate_midi_msgs(wave, values, 1, note_type)
            else:
                wave = np.concatenate([generate_sawtooth(f, t) for f in n])
            harmony.append(wave)

        if args.bass:
            arg = 3 if args.midi else 2
            _, _, _, midi = line_notes[0]
            bass_note = midi_to_note(midi - 24)
            if args.verbose:
                print(f"{label} Bass Note: {bass_note[0]}{bass_note[1]} ({midi}) @ {bass_note[2]}Hz")

            wave = []
            if args.midi:
                values = [(midi, [64,64])] * 4
                generate_midi_msgs(wave, values, 2, "whole")
            else:
                wave = np.concatenate([generate_sawtooth(bass_note[arg], t)] * len(line_notes))
            bass.append(wave)

    tracks = [ np.concatenate(d) for d in [melody, bass, harmony, drums] if len(d) != 0]

    if args.midi:
        mid = mido.MidiFile()
        mid.tracks.append(mido.merge_tracks(tracks))

        with mido.open_output(name=args.midi_device) as port:
            try:
                while True:
                    for msg in mid.play():
                        port.send(msg)
                    print("Loop complete")
            except KeyboardInterrupt:
                port.send(mido.Message('control_change', channel=0, control=123, value=0))
            finally:
                port.close()
    else:
        mixed_track = np.zeros_like(tracks[0])
        for track in tracks:
            mixed_track += track.astype(np.float16)
        mixed_track /= len(tracks)

        mixed_track *= (amplitude / (np.max(np.abs(mixed_track))))

        if args.output is None:
            print("Playing music...")
            try:
                sd.play(mixed_track, samplerate, loop=True, blocking=True)
            except KeyboardInterrupt:
                print("\nPlayback complete, exiting...")
        else:
            print(f"Writing to file: {args.output}")
            wav.write(args.output, samplerate, mixed_track.astype(np.int16))

def tempo(value):
    try:
        ivalue = int(value)
        if 80 <= ivalue <= 160: return ivalue
        raise ValueError(f"Illegal value for tempo provided ({value}); value expected to be between 80 and 160.")
    except:
        raise argparse.ArgumentTypeError(f"Illegal value type provided; integer value expected.")

def key(value):
    try:
        ivalue = int(value)
        if 45 <= ivalue <= 127: return ivalue
        raise ValueError(f"Illegal value for key provided ({value}); value expected to be between 45 and 127.")
    except:
            raise argparse.ArgumentTypeError(f"Illegal value type provided; integer value expected.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Program that procedurally generates Aleatoric music.")
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="enable the program to have more detailed output."
    )
    parser.add_argument(
        "-o", "--output", type=str,
        help="save the generated music to a WAV file with the given name. By default, the music will be played through through the sound system.",
        metavar="FILENAME.wav"
    )
    parser.add_argument(
        "-k", "--key", type=key,
        help="set the key of the generated music in the form of a MIDI key. By default, this will be randomly selected."
    )
    parser.add_argument(
        "-t", "--tempo", type=tempo,
        help="set the tempo of the generated music. Value must be between 80 and 160. By default, this will be randomly chosen."
    )
    parser.add_argument(
        "-m", "--melody", type=str, default="eighth", choices=note_durations.keys(),
        help="By default, eighth-notes will be used."
    )
    # Extras
    parser.add_argument(
        "--bass", action="store_true",
        help="play the chord root as a whole note two octaves lower."
    )
    parser.add_argument(
        "--harmony", action="store_true",
        help="for each melody note, also play the closest chord note below."
    )
    parser.add_argument(
        "--rhythm", action="store_true",
        help="pick a random note pattern for the verse, and another for the chorus. The same pattern will be used for each line of the verse, and for each line of the chorus."
    )
    parser.add_argument(
        "--drums", action="store_true",
        help="add a drum track using white noise."
    )
    parser.add_argument(
        "--midi", action="store_true",
        help="make the program act as a MIDI controller rather than playing sounds itself."
    )
    parser.add_argument(
        "--midi-port", type=int,
        help="use this port number for connecting to the MIDI controller."
    )
    parser.add_argument(
        "--midi-devices", action="store_true",
        help="list available MIDI input devices to connect to and exit the program. Use associated number as argument to `--midi-port` to select device."
    )
    parser.add_argument(
        "--volume", type=int, default=-3,
        help="adjust the volume in decibels (dB). Default is -3dB."
    )

    args = parser.parse_args()

    key_midi = random.randint(57, 69) # A3 to A4

    if args.key is None:
        args.key = key_midi

    if args.tempo is None:
        args.tempo = random.randint(80, 160)

    if args.midi_devices:
        print("MIDI Output Devices:")
        for i, a in enumerate(mido.get_output_names()):
            print(f"    [{i+1}] {a}")
        exit(0)

    if args.midi and args.midi_port:
        args.midi_device = mido.get_output_names()[args.midi_port-1]

    main(args)