import scipy.io.wavfile as wav
import sounddevice as sd
import mido
import argparse

def main(args):
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Program that procedurally generates Aleatoric music.")
    parser.add_argument("-o", "--output", nargs=1, required=False, type=str, default=None, help="save the generated music to a WAV file with the given name, otherwise automatically play the music through the sound system.")
    main(parser.parse_args())