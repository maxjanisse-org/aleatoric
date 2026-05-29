# Aleatoric
_Created by Max Janisse_

## Description
This program is an Aleatoric music generator. By default, without any arguments, it will randomly select:
* A key in the range of `A3-A4`
* A tempo in the range of `80-160` beats-per-minute
* One of the following song structures: `AABB/CC`, `ABAB/CD`, `AB/CDDD` (the backslash (`/`) separates the verse from the chorus, which is relevant to the `--rhythm` feature)
* A unique chord progression for each measure of the selected song structure (eg. `I-vi-ii-V`)

Once the selections are made, the program with generate a melody and will automatically play the music through your system's speakers **on an infinite loop**. Use `Control + C` to interrupt the loop and force the program to exit.

## Usage

### Python Environment
Run the provided script to set up and/or activate a Python environment. Use the command below to execute the script; notice that it starts with a period. This allows the activation of the Python environment to update the terminal used to execute the script.
```bash
. ./env-setup.bash
```
* If the directory hasn't been initialized, then the environment will be created, activated, and the required packages will be installed. 
* If the environment is initialized, but has not been activated, that will be taken care of.
* If the environment is initialized and activated, nothing will be done
* If you would like to remove the environment, using the `-R` argument.

### Running the Program
Use the following command to execute the program:
```bash
python3 aleatoric.py
```
Configuration options are available as well (can also be seen by using `python3 aleatoric.py -h`):
```bash
usage: aleatoric.py [-h] [-v] [-o FILENAME.wav] [-k KEY] [-t TEMPO] [-m {whole,half,quarter,eighth,sixteenth}] [--bass] [--harmony] [--rhythm] [--drums] [--midi] [--midi-port MIDI_PORT] [--midi-devices] [--volume VOLUME]

Program that procedurally generates Aleatoric music.

options:
  -h, --help            show this help message and exit
  -v, --verbose         enable the program to have more detailed output.
  -o, --output FILENAME.wav
                        save the generated music to a WAV file with the given name. By default, the music will be played through through the sound system.
  -k, --key KEY         set the key of the generated music in the form of a MIDI key. By default, this will be randomly selected.
  -t, --tempo TEMPO     set the tempo of the generated music. Value must be between 80 and 160. By default, this will be randomly chosen.
  -m, --melody {whole,half,quarter,eighth,sixteenth}
                        By default, eighth-notes will be used.
  --bass                play the chord root as a whole note two octaves lower.
  --harmony             for each melody note, also play the closest chord note below.
  --rhythm              pick a random note pattern for the verse, and another for the chorus. The same pattern will be used for each line of the verse, and for each line of the chorus.
  --drums               add a drum track using white noise.
  --midi                make the program act as a MIDI controller rather than playing sounds itself.
  --midi-port MIDI_PORT
                        use this port number for connecting to the MIDI controller.
  --midi-devices        list available MIDI input devices to connect to and exit the program. Use associated number as argument to `--midi-port` to select device.
  --volume VOLUME       adjust the volume in decibels (dB). Default is -3dB.
```
#### MIDI Support
To enable MIDI support you will probably first want to include `--midi --midi-devices` in the argument list. This will ensure the application is in "MIDI mode" and will then display a list of MIDI devices connected to your system and designated by a number (see below for an example), then the program will exit. 

```bash
MIDI Output Devices:
    [1] Midi Through:Midi Through Port-0 14:0
    [2] VMPK Input:in 128:0
```
_example output on my machine with VMPK running and waiting for a connection_

Based on this list, you can then rerun the program with `--midi --midi-port <number>`, where `<number>` is the order number associated with the device. In the above example, I would use `--midi --midi-port 2` to connect the program to my configured instance of VMPK.

## My Story
> This project was fascinating to work on and it put a smile on my face once it started producing something even close to music but, in all honesty, I wouldn't have been able to do anything without collaborating with AI tools like _Google Search AI Summary_ and, especially, _Claude_. However, I'd like it known that, while I _looked_ at a lot of AI-generated code, I only rarely copy-pasted it directly into my program with the exception of one function that still (as well as historically in Git) looks very different from anything else I've written.

I felt so out of my comfort zone that the first task I undertook was to add in all the arguments and necessary validators I planned on supporting (including both basic and extras), as well as any information from the assignment document I could hardcode in (ie. chord progressions, song structures, etc.). My initial stab at generating the melody was to:
1. Translate the chord progressions to notes within the key's major scale
1. Use `np.piecewise()` to build the array of frequencies that I then fed into the `scipy.sawtooth()` function to generate my signal

This approach _seemed to work_, so I decided to just copy-paste this same approach for implementing support for generating a bass line via the `--bass` argument. Again, it _seemed to work_, so I did the same approach for `--harmony`. It was once `--harmony` was implemented that I started noticing something odd about the playback I heard... it wasn't complete. I had gotten used to the often unsettling tone that `--bass` added to the music, but when I also used `--harmony`, the bass track was no longer being played. This lead me to the realization that the `sounddevice` module was treating my 2D-array of tracks as individual channels, so my bass track was being played on "channel 3", which is outside the range of my two-channel stereo setup, hence it "missing". I researched various ways to resolve this issue and settled on a "mixing" approach where the channels are added together and then averaged. Playing the music on a smooth, infinite loop was simple by setting the `loop` and `blocking` arguments for the `sounddevice.play()` function to `True`. In fact, I realized only recently that using the `loop` argument somehow ensures a less jagged transition between loops than manually blocking the program with `sounddevice.wait()` and allowing a `while True:` infinite loop start the song over again.

At this point, my program was surely generating something that _sounded_ like music, maybe not consistently given it's random nature, but it was a start. To be honest, it feels like I've ended up tweaking things a bunch of times in the hopes of improving the quality of the sound. The first one, I think, was realizing that I was hearing a bunch of aliasing happening and, after a brief bit of research and (more than likely) conversation with an AI, I learned that the `scipy.sawtooth()` function used the quick-and-dirty equation to calculate the wave and, therefore, had the unfortunate side effect of causing aliasing (it was now that I remember this being mentioned in class). I resolved this by, instead, implementing the sum-of-sines equation that was also brought up in class. 

I _think_ I've covered the base requirements for this assignment but, as I alluded to earlier, I was definitely going to attempt as many of the extras as I could and, therein lies the bulk of my time on this project.

### Further Development Efforts
As I mentioned at the top of my story, I began by just copy-pasting my base approach to the other features of: `--bass` and `--melody`. The pasted solutions then, for the most part, just needed to be tweaked to behave as defined in the assignment document. Once I felt that I had successfully implemented those features I consolidated the repetitious code into a function.

Implementing `--rhythm`, allowed my music to have the _potential_ to sound fancy (really depended on the note durations that were randomly selected). This feature meshed well with the other features, but definitely not once I decided to switch gears and see what it would take to implement MIDI support. Yeah... I did this whole thing backwards, which really goes to show how out of my element I am.

Thankfully, getting MIDI support _started_ wasn't all that difficult. I had retrofitted my `--key` argument to take the MIDI code of the desired key earlier in the development process and had a function that could reverse engineer other values of the note in question (eg. its octave, display-friendly scale note, and frequency). Having this support already allowed me to refactor other aspects of the code such that everything always started with MIDI codes, which I could then expand out and use in either MIDI-mode or normal-mode. However, I pretty quickly ran into problems with reconciling note durations in normal-mode to the number of `note_on` messages to send (and their proper durations) to the MIDI device. I had issues with both of the `--bass` and `--rhythm` features causing tracks to drop out early or play on _waaaay_ too long. This problem seem most pronounced when a "whole note" duration was selected for one of the sections. Other than those inconsistencies, my MIDI support seemed to work pretty well and it was really nice to hear the generated music played as something other than a series of harsh digital tones.

It was about this point in the assignment where I really turned to _Claude_ to help ensure that I was understanding the nuances of the assignment correctly. My first conversation with it was to [help clarify some basics about the assignment](https://claude.ai/share/fb9f7199-a9ce-47a3-b74c-52f1bd62d083). It was extremely helpful to have it generate that flow UI with clickable spot that would spawn followup questions. This conversation lead me to realize that I had **completely missed** the part about randomly selecting a note from either the chord or major scale, fortunately, _Claude_ made it pretty digestible and implementation went smoothly enough. When I got to the issues surrounding my MIDI support, I went back to _Claude_ to have another [conversation with it](https://claude.ai/share/3fbcfa29-fe0c-45b3-b96a-269c11b231dd) in the hopes that my confusion would be cleared up. 

Oddly enough, my biggest challenge of all (and still alludes me as of this writing) has been what seems to me the most basic of the extra features: **percussion**. To be clear, percussion over MIDI is, in fact, very straight-forward but, for whatever reason, I have failed to make anything work when trying to generate a single to represent a drum track. You can see in my last conversation with _Claude_ that I was asking it for pointers and clarification but, in the end, I started getting myself all confused, again, about whether or not I had even been doing things correctly from the start. It's very possible that, of all the extra features, this one may elude me. I'll add an update to this if I manage to get it working before I turn this project in but, otherwise, expect this feature to throw a `Not Implemented` exception unless the program is being run in MIDI-mode.

**Update: 05-28-2026**  
I made a somewhat last minute refactor that came about because, once again, I [struck up a conversation with _Claude_](https://claude.ai/share/ccc211a6-2eac-46c1-9543-520b1b66c3ff) in a bid to untangle my understanding of notes, beats, and measures. The conversation made me realize that, once again, I had misunderstood a fundamental part of generating the music. My new approach now generates the chord scales per line based on the assigned chord progression. Now, as each line is processed I determine the notes of the melody and, if `--harmony` has been enabled, also generating the harmony notes based on the expected note length. In order to ensure that lines of the same letter share the same melody and harmony notes, the generated values are stored in a dictionary and reused if they exist. This modification allowed me to rely solely on iterating over existing arrays of notes instead of my prior approach which often failed to work consistently with the `--rhythm` feature functionality.

### What's Next?
The first thing I would continue working on would be to complete the implementation of the `--drums` feature so that both modes of the program support it. After that, I would implement little embellishments like ASDR envelopes for normal-mode notes and some variation logic for the velocities used in some of the features. Also, improving the `--drums` feature to emulate a basic 3 piece drum set with snare and kick drums and a high-hat would be really cool but, realistically, if I'm having the issues I am just trying to generate the basic version, making it more complex is not likely to be any easier to do.

As someone else brought up in Zulip, there's also a question of properly handling the lowercase chord designations in some of the possible progressions. At the moment, I am only using the major scale, but I believe that is not _quite_ how it's supposed to be.