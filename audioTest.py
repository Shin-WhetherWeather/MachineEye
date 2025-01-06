import pyaudio # Soundcard audio I/O access library
import wave # Python 3 module for reading / writing simple .wav files
import numpy as np

# Setup channel info
FORMAT = pyaudio.paInt16 # data type format
CHANNELS = 2 # Adjust to your number of channels
RATE = 48000 # Sample Rate
CHUNK = 1024 # Block Size
WAVE_OUTPUT_FILENAME = "file.wav"

SILENCE_TIMEOUT = 3         # Silence timer in seconds
SILENCE_THRESHOLD = 256     # Loudness threshold from 0 to 32767
MAX_DURATION = 60           # Maximum recording duration

audio_frames = []
timeoutCounter = 0
recordingCounter = 0

# Startup pyaudio instance
audio = pyaudio.PyAudio()

# start Recording
stream = audio.open(format=FORMAT, channels=CHANNELS,
                                    rate=RATE, input=True,
                                    frames_per_buffer=CHUNK)
print("recording...")

#Loops through the audio buffer chunk by chunk
while(1):
    data = stream.read(CHUNK)
    data_arr = np.frombuffer(data, dtype='int16')
    #extract the maximum volume of the current chunk
    maxVol = np.max(data_arr)

    #select the left channel of audio 
    #[1::CHANNELS] for right channel
    data_arr = data_arr[0::CHANNELS]

    audio_frames.append(data_arr)

    #reset the counter if the audio input is detected longer than the specified duration
    if(maxVol < SILENCE_THRESHOLD):
        timeoutCounter = timeoutCounter + CHUNK/RATE
    else:
        timeoutCounter = 0

    if(timeoutCounter > SILENCE_TIMEOUT):
        break

    #stops recording when max duration is reached, regardless of recording volume
    recordingCounter = recordingCounter + CHUNK/RATE

    if(recordingCounter > MAX_DURATION):
        break

print("recording complete")
# Stop recording
stream.stop_stream()
stream.close()
audio.terminate()

#remove first ~0.3s of audio where the microphone pops
audio_frames = audio_frames[14:]

#extract the overall maximum volume and use it to scale the entire audio file
absMaxVol = np.max(audio_frames)

scalingFactor = int(30000/absMaxVol)
loudFrames = np.array(audio_frames)*scalingFactor
loudFrames = np.clip(loudFrames, -32768, 32767)

# Write your new .wav file with built in Python 3 Wave module
waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
waveFile.setnchannels(1)
waveFile.setsampwidth(audio.get_sample_size(FORMAT))
waveFile.setframerate(RATE)
waveFile.writeframes(b''.join([loudFrames.tobytes()]))
waveFile.close()
