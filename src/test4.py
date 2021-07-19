import guitarpro as pygp

song = pygp.parse("tied.gp3")
i = 0
for measure in song.tracks[0].measures:
    print(song.measureHeaders[i])
    i += 1
    for voice in measure.voices:
        for beat in voice.beats:
            if beat.notes:
                print(beat.duration)