from threading import Timer
from typing import overload
from RPi import GPIO
from time import sleep

GPIO.setmode(GPIO.BCM)


class Metronome():
    SEC_IN_MIN = 60
    DEFAULT_TEMPO = 60
    DEFAULT_BEATS_PER_LOOP = 4

    def __init__(self, tempo = DEFAULT_TEMPO, beats_per_loop = DEFAULT_BEATS_PER_LOOP, tempo_factor = 5, buzzer_pin=12, \
        buzzer_freq=440, buzzer_duration=0.07):
        self.tempo = tempo
        self.beats_per_loop = beats_per_loop
        self.tempo_factor = tempo_factor

        self.is_metronome_active = False
        self.current_beat = 0

        self.buzzer_pin = buzzer_pin
        self.buzzer_freq = buzzer_freq
        self.buzzer_duration = buzzer_duration
        GPIO.setup(self.buzzer_pin, GPIO.OUT)
        self.buzzer_pwm = GPIO.PWM(self.buzzer_pin, self.buzzer_freq)

    @property
    def is_metronome_active(self):
        return self._is_metronome_active

    @is_metronome_active.setter
    def is_metronome_active(self, bool):
        self._is_metronome_active = bool

    @property
    def tempo(self):
        return self._tempo

    @tempo.setter
    def tempo(self, new_tempo):
        self._tempo = new_tempo

    @property
    def current_beat(self):
        return self._current_beat

    @current_beat.setter
    def current_beat(self, cb):
        self._current_beat = cb

    def increase_tempo(self):
        self.tempo += self.tempo_factor

    def decrease_tempo(self):
        self.tempo -= self.tempo_factor

    def reset_tempo(self):
        self.tempo = self.DEFAULT_TEMPO

    def increase_beats_per_loop(self):
        self.beats_per_loop += 1

    def decrease_beats_per_loop(self):
        self.beats_per_loop -= 1

    def reset_beats_per_loop(self):
        self.beats_per_loop = self.DEFAULT_BEATS_PER_LOOP

    def start_metronome(self, func = None):
        if not self.is_metronome_active:
            self.current_beat = 0
            self.is_metronome_active = True
            self.metronome_thread(func)

    def stop_metronome(self):
        self.is_metronome_active = False

    def metronome_thread(self, func = None):
        if self.is_metronome_active:
            overflow = False
            timer = self.SEC_IN_MIN / self.tempo
            Timer(timer, self.metronome_thread, [func]).start()

            self.current_beat += 1
            if self.current_beat > self.beats_per_loop:
                self.current_beat = 1
                overflow = True

            if func != None:
                func(overflow)

            #Trigger the buzzer to a specify pwm frequency
            self.buzzer_pwm.start(50) # Duty cycle, between 0 and 100
            sleep(self.buzzer_duration)
            self.buzzer_pwm.stop()
            #Uncomment to check th number of Thread object running
            #print(threading.active_count())

metronome = Metronome()