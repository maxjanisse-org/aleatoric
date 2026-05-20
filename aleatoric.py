import scipy.signal as signal
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
] # Can add more, possibly as an argument (waaaaay extra credit)

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

keys = ['A', 'B♭/A♯', 'B', 'C', 'D♭/C♯', 'D', 'E♭/D♯', 'E', 'F', 'G♭/F♯', 'G', 'A♭/G♯']

def note(base_freq, i): 
    return base_freq * 2 ** (i/12)

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

def main(args):
    song_struct = song_structs[random.randint(0, len(song_structs)-1)]
    chords = random.sample(chord_loops, k=4)
    chords_by_label = {c[0]: c[1] for c in zip(['A','B','C','D'], chords)}
    key_index = random.randint(0, len(keys)-1)

    if args.key is None:
        args.key = keys[key_index]
    else:
        key_index = keys.index(args.key)

    if args.verbose:
        print(f"Key: {args.key}{args.octave}")
        print(f"Structure: {song_struct}")
        for k,v in chords_by_label.items():
            print(f"    {k}: {v}")
        print(f"Tempo: {args.tempo} bpm")
        print(f"Output: {args.output if args.output is not None else "Audio Out"}")
        print(f"Generate Bass: {args.bass}")
        print(f"Generate Harmony: {args.harmony}")
        print(f"Generate Rhythm: {args.rhythm}")
        print(f"Generate Drums: {args.drums}")
        print(f"MIDI Support: {args.midi}")
        if args.midi:
            print(f"MIDI Port: {args.midi_port}")
        print()
    
    samplerate = 48000
    #freqs = [55 << i for i in range(args.octave + 1)]
    #freq = note(freqs[-2], key_index)

    scale = [note(55*args.octave, i) for i in range(len(keys) + 1)]
    x = dict(zip(keys, scale))
    #print(x)
    major_scale = [scale[n] for n in [0, 2, 4, 5, 7, 9, 11]]
    #print(major_scale)

    beat_duration = (60/args.tempo) * args.melody

    melody = []
    bass = []
    harmony = []
    is_chorus = False
    for label in song_struct:
        if label == "/": 
            is_chorus = True
            continue

        chord_progression = chords_by_label[label]
        t = np.linspace(0, beat_duration * 4, int(samplerate * beat_duration * 4))
        y = [major_scale[y] for y in parse_progression(chord_progression)]

        frequencies = np.piecewise(
            t,
            [
                t < beat_duration,
                (t >= beat_duration) & (t < beat_duration * 2),
                (t >= beat_duration * 2) & (t < beat_duration * 3),
                t >= beat_duration * 3
            ],
            y
        ) # type: ignore
        wave = signal.sawtooth(2 * np.pi * np.cumsum(frequencies) / samplerate)
        melody.append(wave)

        if args.harmony:
            n = y[0] if is_chorus else 0
            frequencies = np.piecewise(
                t,
                [
                    t < beat_duration,
                    (t >= beat_duration) & (t < beat_duration * 2),
                    (t >= beat_duration * 2) & (t < beat_duration * 3),
                    t >= beat_duration * 3
                ],
                [n] * 4
            ) # type: ignore
            wave = signal.sawtooth(2 * np.pi * np.cumsum(frequencies) / samplerate)
            harmony.append(wave)

        if args.bass:
            # Drop the octave of the current chord's base key by 2; divide the frequency by 4
            n = y[0] / 4
            frequencies = np.piecewise(
                t,
                [
                    t < beat_duration,
                    (t >= beat_duration) & (t < beat_duration * 2),
                    (t >= beat_duration * 2) & (t < beat_duration * 3),
                    t >= beat_duration * 3
                ],
                [n] * 4
            ) # type: ignore
            wave = signal.sawtooth(2 * np.pi * np.cumsum(frequencies) / samplerate)
            bass.append(wave)

    x = np.column_stack([ np.concatenate(d) for d in [melody, bass, harmony] if len(d) != 0])

    if args.output is None:
        print("Playing music...")
        try:
            #x = np.concatenate(data) #[np.concatenate(d) for d in data]
            sd.play(x, samplerate, loop=True, blocking=True)
            print("Playback: Loop complete")
        except KeyboardInterrupt:
            print("Playback complete, exiting...")
    else:
        print(f"Writing to file: {args.output}")
        wav.write(args.output, samplerate, [])

def tempo(value):
    try:
        ivalue = int(value)
        if 80 <= ivalue <= 160: return ivalue
        raise ValueError(f"Illegal value for tempo provided ({value}); value expected to be between 80 and 160.")
    except:
        raise argparse.ArgumentTypeError(f"Illegal value type provided; integer value expected.")

def octave(value):
    try:
        ivalue = int(value)
        if 1 <= ivalue <= 8: return ivalue
        raise ValueError(f"Illegal value for octave provided ({value}); value expected to be between 1 and 8.")
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
        "-k", "--key", choices=keys, 
        help="set the key of the generated music. By default, this will be randomly selected."
    )
    parser.add_argument(
        "-t", "--tempo", type=tempo,
        help="set the tempo of the generated music. Value must be between 80 and 160. By default, this will be randomly chosen."
    )
    parser.add_argument(
        "-m", "--melody", type=float, default=0.5,
        help="By default, eighth-notes will be used."
    )
    # Extras
    parser.add_argument(
        "--octave", type=octave, default=3,
        help="the octave of the base key. Value must be between 1 and 8. If `--bass` argument is used, then value must be between 3 and 8."
    )
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

    args = parser.parse_args()

    if args.bass and args.octave < 3:
        raise ValueError("Cannot generate bass track for octave's less than 3.")

    if args.tempo is None:
        args.tempo = random.randint(80, 160)

    main(args)