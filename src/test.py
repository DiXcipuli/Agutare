import guitarpro as gm

splits = [([(0, 6), (2, 5)], 4),
          ([(3, 6), (5, 5)], 4),
          ([(5, 6), (7, 5)], 4)]

base_song = gm.Song()
track = gm.Track(base_song, measures=[])
base_song.tracks.append(track)

m = 0  # number of measure to be edited
header = base_song.measureHeaders[m]
measure = gm.Measure(track, header)
track.measures.append(measure)

voice = measure.voices[0]

for i, (notes, duration) in enumerate(splits):
    new_duration = gm.Duration(value=duration)
    new_beat = gm.Beat(voice,
                       duration=new_duration,
                       status=gm.BeatStatus.normal)
    for value, string in notes:
        new_note = gm.Note(new_beat,
                           value=value,
                           string=string,
                           type=gm.NoteType.normal)
        new_beat.notes.append(new_note)
    voice.beats.append(new_beat)

gm.write(base_song, 'tarpalsus.gp5')