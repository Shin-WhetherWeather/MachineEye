import pyaudio # Soundcard audio I/O access library
import wave # Python 3 module for reading / writing simple .wav files
import numpy as np

# Setup channel info
FORMAT = pyaudio.paInt16 # data type formate
CHANNELS = 2 # Adjust to your number of channels
RATE = 48000 # Sample Rate
CHUNK = 1024 # Block Size
RECORD_SECONDS = 5 # Record time
WAVE_OUTPUT_FILENAME = "file.wav"

# Startup pyaudio instance
audio = pyaudio.PyAudio()

# start Recording
stream = audio.open(format=FORMAT, channels=CHANNELS,
                                    rate=RATE, input=True,
                                    frames_per_buffer=CHUNK)
print("recording...")
frames = []
TIMEOUT_COUNTER = 3

# Record for RECORD_SECONDS
for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    

    data = stream.read(CHUNK)
    data_arr = np.fromstring(data, dtype='int16')
    channel0 = data_arr[0::CHANNELS]
    channel0 = channel0*24

    data=channel0.tostring()
    frames.append(data)


# Stop Recording
stream.stop_stream()
stream.close()
audio.terminate()

# Write your new .wav file with built in Python 3 Wave module
waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
waveFile.setnchannels(1)
waveFile.setsampwidth(audio.get_sample_size(FORMAT))
waveFile.setframerate(RATE)
waveFile.writeframes(b''.join(frames))
waveFile.close()
