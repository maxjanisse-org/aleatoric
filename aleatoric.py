import scipy.io.wavfile as wav
import sounddevice as sd
import mido
import argparse

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

def main(args):
    pass

def tempo(value):
    if type(value) is not int:
        raise argparse.ArgumentTypeError(f"Illegal value type for tempo provided; integer value expected.")
    ivalue = int(value)
    if 80 < ivalue < 160: return ivalue
    raise argparse.ArgumentTypeError(f"Illegal value for tempo provided ({value}); value expected to be between 80 and 160.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Program that procedurally generates Aleatoric music.")
    parser.add_argument(
        "-o", "--output", 
        nargs=1, required=False, default=None, type=str,
        help="save the generated music to a WAV file with the given name. By default, the music will be played through through the sound system.",
        metavar="FILENAME.wav"
    )
    parser.add_argument(
        "-k", "--key", 
        nargs=1, required=False, default=None,
        choices=['A3', 'B3', 'C3', 'D3', 'E3', 'F3', 'G3', 'A4'], 
        help="set the key of the generated music. By default, this will be randomly selected."
    )
    parser.add_argument(
        "-t", "--tempo",
        nargs=1, required=True, type=tempo,
        help="set the tempo of the generated music. Value must be between 80 and 160. By default, this will be randomly chosen."
    )
    parser.add_argument(
        "-m", "--melody",
        nargs=1, required=False,
        help="By default, eighth-notes will be used."
    )
    # Extras
    parser.add_argument(
        "--bass",
        required=False, action="store_true",
        help="play the chord root as a whole note two octaves lower."
    )
    parser.add_argument(
        "--harmony",
        required=False, action="store_true",
        help="for each melody note, also play the closest chord note below."
    )
    parser.add_argument(
        "--rhythm",
        required=False, action="store_true",
        help="pick a random note pattern for the verse, and another for the chorus. The same pattern will be used for each line of the verse, and for each line of the chorus."
    )
    parser.add_argument(
        "--drums",
        required=False, action="store_true",
        help="add a drum track using white noise."
    )
    parser.add_argument(
        "--midi",
        required=False, action="store_true",
        help="make the program act as a MIDI controller rather than playing sounds itself."
    )
    parser.add_argument(
        "--midi-port",
        nargs=1, required=False, type=int,
        help="use this port number for connecting to the MIDI controller."
    )
    main(parser.parse_args())