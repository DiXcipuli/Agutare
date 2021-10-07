from threading import Timer
from RPi import GPIO
from time import sleep


class Metronome():
    SEC_IN_MIN = 60

    def __init__(self):
        self.tempo = 60
        self.beats_per_loop = 4
        self.tempo_factor = 5

        self.is_metronome_active = False
        self.current_beat = 0

        buzzer_pin = 12
        GPIO.setup(buzzer_pin, GPIO.OUT)
        buzzer_freq = 440

        self.buzzer_pwm = GPIO.PWM(buzzer_pin, buzzer_freq)
        self.buzzer_duration = 0.07


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
            overflow = False    # overflow is true when it reaches the last beat of the loop, and get back to 1
            timer = self.SEC_IN_MIN / self.tempo
            Timer(timer, self.metronome_thread, [func]).start()

            self.current_beat += 1
            if self.current_beat > self.beats_per_loop:
                self.current_beat = 1
                overflow = True

            if func != None:
                func(overflow)

            self.buzzer_pwm.start(50) # Duty cycle, between 0 and 100
            sleep(self.buzzer_duration)
            self.buzzer_pwm.stop()

