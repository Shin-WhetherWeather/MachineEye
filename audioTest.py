import pyaudio # Soundcard audio I/O access library
import wave # Python 3 module for reading / writing simple .wav files
import numpy as np
import speech_recognition as sr

from os import path

# Setup channel info
FORMAT = pyaudio.paInt16 # data type format
CHANNELS = 2 # Adjust to your number of channels
RATE = 48000 # Sample Rate
CHUNK = 1024 # Block Size
WAVE_OUTPUT_FILENAME = "file.wav"

SILENCE_TIMEOUT = 3         # Silence timer in seconds
SILENCE_THRESHOLD = 256     # Loudness threshold from 0 to 32767
MAX_DURATION = 15           # Maximum recording duration

COMP_THRESHOLD = 32         # Audio peak compression, set to 32767 to disable compression
COMP_RATIO = 1.3            # Compression ratio, >=1

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
    data_arr = data_arr.copy()

    #select the left channel of audio 
    #[1::CHANNELS] for right channel
    data_arr = data_arr[0::CHANNELS]
    maxVol = np.max(np.absolute(data_arr))

    #reset the counter if the audio input is detected longer than the specified duration
    if(maxVol < SILENCE_THRESHOLD):
        timeoutCounter = timeoutCounter + CHUNK/RATE
    else:
        timeoutCounter = 0

    #exit the loop if silent for longer than SILENCE_TIMEOUT
    if(timeoutCounter > SILENCE_TIMEOUT):
        #remove the last ~2s of audio since it is silent
        audio_frames = audio_frames[:-93 or None]
        break;

    #stops recording when max duration is reached, regardless of recording volume
    recordingCounter = recordingCounter + CHUNK/RATE
    if(recordingCounter > MAX_DURATION):
        break;
    
    #this compresses the peaks of the audio signal and balances out the final loudness
    for i, x in enumerate(data_arr):
        if np.absolute(x) > COMP_THRESHOLD:
            data_arr[i] = int(   COMP_THRESHOLD*np.sign(x) + (x - COMP_THRESHOLD*np.sign(x))/COMP_RATIO   )

    if(maxVol > SILENCE_THRESHOLD*0.8):
        #slightly boost the audio volume if it is not silent
        data_arr = data_arr*int(np.min([ 5000/np.max(data_arr) ,4]))
    audio_frames.append(data_arr)


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


# Speech recognition happens here!
r = sr.Recognizer()
with sr.AudioFile(WAVE_OUTPUT_FILENAME) as source:
    audio = r.record(source)

try:
    print("Google thinks you said " + r.recognize_google(audio))
except sr.UnknownValueError:
    print("Sphinx could not understand audio")
except sr.RequestError as e:
    print("Sphinx error; {0}".format(e))
