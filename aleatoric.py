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

note_types = ['whole', 'half', 'quarter', 'eighth', 'sixteenth']

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
    # Number of quarter-note beats each note type receives
    beat_multipliers = {
        'whole': 4.0,
        'half': 2.0,
        'quarter': 1.0,
        'eighth': 0.5,
        'sixteenth': 0.25
    }
    
    if note_type not in beat_multipliers:
        raise ValueError(f"Unknown note type: {note_type}")
        
    seconds_per_beat = 60.0 / bpm
    return seconds_per_beat * beat_multipliers[note_type]

def generate_midi_msgs(wave, values, channel, xx):
    tempo = mido.bpm2tempo(args.tempo)
    delta = mido.second2tick(get_note_duration(xx, args.tempo), 480, tempo)
    for m,v in values:
        wave.append(mido.Message("note_on", note=m, velocity=v[0], channel=channel, time=0))
        wave.append(mido.Message("note_off", note=m, velocity=v[1], channel=channel, time=delta))

def determine_chord_scales(chords_by_label, major_scale_midi):     
    major_scale = [midi_to_note(i) for i in major_scale_midi]   
    chord_scales = []

    g = {}
    for line, chords in chords_by_label.items():
        g[line] = []
        for i in chords.split('-'):
            x = list(parse_progression(i))[0]
            w = (x + 2) % len(major_scale_midi)
            u = (x + 4) % len(major_scale_midi)
            a = [midi_to_note(major_scale_midi[j]) for j in [x, w, u]]
            chord_scales.append((i, a)) 

            s = random.choice(a) if random.random() < 0.8 else random.choice(major_scale)
            g[line].append(s)

    y = []
    for _, chord_scale in chord_scales:
        s = random.choice(chord_scale) if random.random() < 0.8 else random.choice(major_scale)
        y.append(s)

    return (chord_scales, y, g)

def determine_amplitude(db):
    return 10 ** (db / 20)

def main(args):
    samplerate = 48000
    amplitude = determine_amplitude(args.volume)
    song_struct = song_structs[random.randint(0, len(song_structs)-1)]
    chords = random.sample(chord_loops, k=4)
    chords_by_label = {c[0]: c[1] for c in zip(['A','B','C','D'], chords)}

    note, octave, _, _ = midi_to_note(args.key)
    major_scale_midi = [args.key + i for i in [0, 2, 4, 5, 7, 9, 11]]

    (chord_scales, y, g) = determine_chord_scales(chords_by_label, major_scale_midi)

    if args.verbose:
        print(f"Key: {note}{octave} ({args.key})")
        print(f"Major Scale Notes: {[midi_to_note(i)[0] for i in major_scale_midi]}")
        print(f"Structure: {song_struct}")
        for k,v in chords_by_label.items():
            print(f"    {k}: {v}")
        print(f"Structure: {song_struct}")
        for k,v in g.items():
            print(f"    {k}: {[d[0] for d in v]}")
        print(f"Tempo: {args.tempo} bpm")
        if not args.midi:
            print(f"Output: {args.output if args.output is not None else "Audio Out"}")
        else:
            print(f"Output: MIDI")
            print(f"    Device: '{args.midi_device}'")
        print(f"Generate Bass: {args.bass}")
        print(f"Generate Harmony: {args.harmony}")
        print(f"Generate Rhythm: {args.rhythm}")
        print(f"Generate Drums: {args.drums}")
        print()
    
    melody = []
    bass = []
    harmony = []
    drums = []
    xx = args.melody if not args.rhythm else random.choice(note_types)
    for label in song_struct:
        if label == "/":
            if args.rhythm:
                xx = random.choice(note_types)
            continue

        t = np.linspace(0, get_note_duration(xx, args.tempo), int(samplerate * get_note_duration(xx, args.tempo)), endpoint=False)

        wave = []
        if args.midi:
            values = []
            for _,_,_,n in y*2:
                values.append((n, [64]*2))
            generate_midi_msgs(wave, values, 0, xx)
        else:
            wave = np.concatenate([generate_sawtooth(f, t) for _, _, f, _ in y])

        melody.append(wave)

        if args.drums:
            wave = []
            if args.midi:
                values = []
                for n in [39]*16:
                    values.append((n, [100,0]))
                generate_midi_msgs(wave, values, 9, "eighth")
                drums.append(wave)

        if args.harmony:
            arg = 3 if args.midi else 2
            n = [note[arg] for note in g[label]] * 4
            wave = []
            if args.midi:
                values = []
                for m in n:
                    values.append((m, [64]*2))
                generate_midi_msgs(wave, values, 1, args.melody)
            else:
                wave = np.concatenate([generate_sawtooth(f, t) for f in n])

            harmony.append(wave)

        if args.bass:
            _, _, _, midi = g[label][0]
            note, oct, n, midi = midi_to_note(midi - 24)
            if args.verbose:
                print(f"{label} Bass Note: {note}{oct} @ {n}Hz ({midi})")
            
            wave = []
            if args.midi:
                values = []
                for m in [midi]*2:
                    values.append((m, [64]*2))
                generate_midi_msgs(wave, values, 2, "whole")
            else:
                wave = np.concatenate([generate_sawtooth(f, t) for f in [n]*16])

            bass.append(wave)

    x = [ np.concatenate(d) for d in [melody, bass, harmony, drums] if len(d) != 0]

    if args.midi:
        mid = mido.MidiFile()
        mid.tracks.append(mido.merge_tracks(x))

        with mido.open_output(name=args.midi_device) as port:
            try:
                for msg in mid.play():
                    port.send(msg)
            except KeyboardInterrupt:
                port.send(mido.Message('control_change', channel=0, control=123, value=0))
            finally:
                port.close()
    else:
        t = np.zeros_like(x[0])
        for y in x:
            t += y.astype(np.float32)
        x = t / len(x)

        x *= (amplitude / (np.max(np.abs(x))))

        if args.output is None:
            print("Playing music...")
            try:
                sd.play(x, samplerate, loop=True, blocking=True)
            except KeyboardInterrupt:
                print("\nPlayback complete, exiting...")
        else:
            print(f"Writing to file: {args.output}")
            wav.write(args.output, samplerate, x)

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
        "-m", "--melody", type=str, default="eighth", choices=note_types,
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
        help=""
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