import guitarpro

song = guitarpro.base.Song()
track = guitarpro.base.Track(name='Track 1')
track.strings = [guitarpro.base.GuitarString(n, v)
                 for n, v in enumerate([64, 59, 55, 50, 45, 40], start=1)]
measure = guitarpro.base.Measure()
measure.voices = [guitarpro.base.Voice(), guitarpro.base.Voice()]
for voice in measure.voices:
    voice.addBeat(guitarpro.base.Beat())
track.addMeasure(measure)
song.addTrack(track)

guitarpro.write(song, 'blank.gp5')