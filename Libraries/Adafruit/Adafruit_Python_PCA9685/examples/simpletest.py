from __future__ import division
import time
import guitarpro
import Adafruit_PCA9685

pwm = Adafruit_PCA9685.PCA9685()

# Configure min and max servo pulse lengths
servo_min = 80
servo_neutral = 295
servo_max = 510

pos=[True, True, True, True, True, True]


pwm.set_pwm_freq(50)
cst = 140
timer = 1

def setToMin():
    pwm.set_pwm(0, 0, servo_min + cst)
    pwm.set_pwm(1, 0, servo_min + cst)
    pwm.set_pwm(2, 0, servo_min + cst)
    pwm.set_pwm(3, 0, servo_min + cst)
    pwm.set_pwm(4, 0, servo_min + cst)
    pwm.set_pwm(5, 0, servo_min + cst)

def setToNeutral():
    pwm.set_pwm(0, 0, servo_neutral)
    pwm.set_pwm(1, 0, servo_neutral)
    pwm.set_pwm(2, 0, servo_neutral)
    pwm.set_pwm(3, 0, servo_neutral)
    pwm.set_pwm(4, 0, servo_neutral)
    pwm.set_pwm(5, 0, servo_neutral)
    print("6")

def setToMax():
    pwm.set_pwm(0, 0, servo_max - cst)
    pwm.set_pwm(1, 0, servo_max - cst)
    pwm.set_pwm(2, 0, servo_max - cst)
    pwm.set_pwm(3, 0, servo_max - cst)
    pwm.set_pwm(4, 0, servo_max - cst)
    pwm.set_pwm(5, 0, servo_max - cst)

def loadTab():
    setToMin()
    events = []
    song = guitarpro.parse('test6.gp5')
    print("Tempo = ", song.tempo)
    print("Number of tracks = ", len(song.tracks))
    print("Number of measures = ", len(song.tracks[0].measures))
    print("Number of voices = ", len(song.tracks[0].measures[0].voices))
    measure_number = 0
    print("Number of beats per bar" , song.measureHeaders[0].timeSignature.numerator)
    beats_per_bar = song.measureHeaders[0].timeSignature.numerator
    for measure in song.tracks[0].measures:
        measure_time = measure_number * 60 * beats_per_bar / song.tempo
        for voice in measure.voices:
            print("Number of beats = ", len(voice.beats))
            beat_time = 0
            for beat in voice.beats:
                note_time = measure_time + beat_time
                beat_time = beat_time + (beat.duration.time/1000)* (60/song.tempo)
                print("Note time = ", note_time)
                if beat.notes:
                    for note in beat.notes:
                        if note.string == 1:
                            events.append(Timer(note_time, string(0)))
                        if note.string == 2:
                            events.append(Timer(note_time, string(1)))
                        if note.string == 3:
                            events.append(Timer(note_time, string(2)))
                        if note.string == 4:
                            events.append(Timer(note_time, string(3)))
                        if note.string == 5:
                            events.append(Timer(note_time, string(4)))
                        if note.string == 6:
                            events.append(Timer(note_time, string(5)))
                            

        measure_number = measure_number + 1

    for event in events:
        event.start()

def string(index):
    print("String",str(index)
    global pos

    if pos[index]:
        pwm.set_pwm(index, 0, servo_neutral + cst)
        pos[index] = False
    else:
        pwm.set_pwm(index, 0, servo_neutral - cst)
        pos[index] = True 

def main():
    setToMin()
    time.sleep(1)
    #setToMax()

if __name__ == "__main__":
    main()


