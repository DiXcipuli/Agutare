import argparse
import guitarpro as pygp

parser = argparse.ArgumentParser()
parser.add_argument("--path", "-p")
args = parser.parse_args()



if args.path == None:
    print("You must give a path to a tab to convert !")
    exit()

tab_path = args.path
song = pygp.parse(tab_path)
print("Tempo = ", song.tempo)
print("Number of tracks = ", len(song.tracks))
print("Number of measures = ", len(song.tracks[0].measures))
print("Denominator = ", song.tracks[0].measures[0].header.timeSignature.denominator)
measure_number = 0
beats_per_bar = song.measureHeaders[0].timeSignature.numerator
for measure in song.tracks[0].measures:
    measure_time = measure_number * 60 * beats_per_bar / song.tempo
    for voice in measure.voices:
        beat_time = 0
        for beat in voice.beats:
            note_time = measure_time + beat_time
            #print(beat.duration.time)
            beat_time = beat_time + (beat.duration.time/960)* (60/song.tempo)
            if beat.notes:
                last_timer = note_time
                for note in beat.notes:
                    #self.events.append(Timer(note_time, self.servo_manager.trigger_servo, [note.string - 1]))
                    pass