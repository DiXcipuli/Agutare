import argparse
from posixpath import join
import guitarpro as pygp
import os

parser = argparse.ArgumentParser()
parser.add_argument("--path", "-p")
parser.add_argument("--output", "-o", default=".")
args = parser.parse_args()

print("This programs convert gpX files into loop file")
print("It is possible to have a gpX file with multiple bars, it will creat as much loop files")

if args.path == None:
    print("You must give a path to a tab !")
    exit()


output_path = args.output
if not os.path.exists(output_path):
    os.mkdir(output_path)

tab_path = args.path
allowed_format = ("gp3", "gp4", "gp5")
if tab_path[-3:] not in allowed_format:
    print("Tab format must be either gp3, gp4 or gp5")
    exit()

default_loop_name = "Loop_"
loop_id = 1
meta_file_name = "Meta.agu"


string_dict = {1:5, 2:4, 3:3, 4:2, 5:1, 6:0}

# Associate a time signature denominator (1: full, 2: half, 4: quarter, 8: 8th)
# to a value of 'pulses per quarter note'. Each note duration is given of this ppqn term,
# so, in order to get the real time value, we need to divide each note by this reference which represents
# the duration of 1 beat
allowed_denominator = (1, 2, 4, 8)
signature_to_ppqn = {1 : 3840, 2: 1920, 4:960, 8: 1440}


song = pygp.parse(tab_path)
time_sig_denominator = song.tracks[0].measures[0].header.timeSignature.denominator.value

if time_sig_denominator not in allowed_denominator:
    print("Tab time signature not supported, must be either 1, 2, 4, or 8")
    exit()

ppqn_per_beat = signature_to_ppqn[time_sig_denominator]
SECS_IN_MIN = 60


tempo = song.tempo
print("Tempo = ", song.tempo)
print("Number of tracks = ", len(song.tracks))
print("Number of measures = ", len(song.tracks[0].measures))
print("Denominator = ", song.tracks[0].measures[0].header.timeSignature.denominator.value)
measure_number = 0
beats_per_bar = song.measureHeaders[0].timeSignature.numerator

with open(os.path.join(output_path, meta_file_name), 'a') as saved_tab_file:
    saved_tab_file.write("tempo," + str(tempo) + '\n' + "beats," + str(beats_per_bar) + '\n')


for measure in song.tracks[0].measures:
    note_array = []
    for voice in measure.voices:
        beat_time = 0
        for beat in voice.beats:
            if beat.notes:
                for note in beat.notes:
                    note_array.append((string_dict[note.string], beat_time / (beats_per_bar * (SECS_IN_MIN/tempo))))
            beat_time = beat_time + (beat.duration.time / ppqn_per_beat) * (SECS_IN_MIN / song.tempo)

    while os.path.exists(os.path.join(output_path, default_loop_name + str(loop_id))):
        loop_id += 1

    with open(os.path.join(output_path, meta_file_name), 'a') as saved_tab_file:
        saved_tab_file.write(default_loop_name + str(loop_id) + '\n')

    with open(os.path.join(output_path, default_loop_name + str(loop_id)), 'w') as loop_file:
        for string, time in note_array:
            loop_file.write(str(string) + "," + str(time) + '\n')