from enum import Enum

class MetronomeState(Enum):
    IDLE = 1
    DEFINING_TEMPO = 2

class TabCreatorState(Enum):
    IDLE = 1
    DEFINING_TEMPO = 2
    DEFINING_BEATS = 3

class SessionRecorderState(Enum):
    NOT_ARMED = 1
    ARMED = 2
    RECORDING = 3
    SAVING = 4