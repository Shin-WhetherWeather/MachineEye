from openai import OpenAI
from picamera2 import Picamera2
import base64
import time
import io
import random

import pyaudio # Soundcard audio I/O access library
import wave # Python 3 module for reading / writing simple .wav files
import numpy as np
import speech_recognition as sr
from subprocess import Popen, PIPE

p = Popen("python3 discordTest.py", stdin=PIPE, stdout=PIPE, shell=True)

from os import path

import serial

class MachineEye:

    # static -> 5-15mins -> take photo & listen -> 5-15mins -> asks for attention -> 5-15mins -> take photo & listen, etc
    # wait random amount of time after interaction before photos

    # currently, the workflow is
    # static -moved-> pickedUp & take photo, listen, generate response -> show results -> setDown1 -> setDown2 -> static
    # static will also transition into attention 
    # setDown1, setDown2, and static can transition into
    def __init__(self, gyroFrequency = 0.5, movementThreshold = 0.09, triggerRandom = 15, moveResetDuration = 10, setDownDuration1 = 10, setDownDuration2 = 10, attentionCooldown = 300, attentionRandom = 600, attentionReturnCooldown = 20,  resultsCooldown = 50):
        # gyroFrequency             how often the gyroscope is read, in seconds
        # movementThreshold         how sensitive movement is considered, lower is more sensitive
        # moveResetDuration         how long before movement is reset and considered no movement
        # resultsCooldown           wait time between results and setDown1
        # setDownDuration1          wait time between setDown1 and setDown2
        # setDownDuration2          wait time between setDown2 and static

        # attentionCooldown         minimum time before machineEye asks for attention
        # attentionRandom           random time added to attentionCooldown, total wait time is attentionCooldown + random(attentionRandom)
        # attentionReturnCooldown   wait time between attention to static


        self.ser = serial.Serial("/dev/ttyAMA0", baudrate = 115200)
        self.ser.close()
        time.sleep(0.05)

        self.LED("SOLID", 0, 55, 0)
        
        self.lastState = "static"
        self.LEDState = "static"
        self.state = "static"
        self.attentionState = 0

        self.stdFlushCooldown = 1
        self.stdFlushTimer = 0

        self.movementThreshold = movementThreshold
        self.gyroFrequency = gyroFrequency
        self.moved = False

        self.currentTime = 0
        self.movedTimer = 0
        self.moveResetDuration = moveResetDuration

        self.triggerRandom = triggerRandom
        self.triggerRandomCooldown = random.random()*triggerRandom


        self.idleTimer = 0
        self.setDownDuration1 = setDownDuration1
        self.setDownDuration2 = setDownDuration2
        self.resultsCooldown = resultsCooldown

        self.attentionCooldown = attentionCooldown
        self.attentionRandom = attentionRandom
        self.attentionReturnCooldown = attentionReturnCooldown
        self.attentionTotal = 0
        self.attentionTriggerState = 0

        self.lastX = 0
        self.lastY = 0
        self.lastZ = 0



        self.cam1 = Picamera2(0)
        self.cam2 = Picamera2(1)

        config1 = self.cam1.create_still_configuration(main={"size": (1920, 1080)})
        config2 = self.cam2.create_still_configuration(main={"size": (1920, 1080)})

        self.cam1.configure(config1)
        self.cam2.configure(config2)

        self.cam1.start()
        self.cam2.start()

        self.client = OpenAI(
            api_key = "APIKEYPLACEHOLDER"
        )



    def screenPrint(self, text):
        # prints a string of text to the screen, automatically scrolls
        self.ser.open()
        string = "T" + text.rstrip() + '\n'
        self.ser.write(string.encode('ascii', errors="ignore"))
        self.ser.close()
        time.sleep(0.05)

    def gyroRead(self):
        # reads the gyroscope values and returns them
        self.ser.open()
        self.ser.write(b'G\n')

        val = self.ser.read_until().decode('utf-8')
        self.ser.close()
        time.sleep(0.05)
        return [round(int(n)/32767, 4) for n in val.split(" ")]

    def LED(self, mode, r = 0, g = 0, b = 0, trail = 2, period = 8):
        # updates the LED states
        # r, g, b for color
        # trail is how wide the trail is for TRAIL mode
        # period is how fast the LED flashes/rotates, higher value is faster

        cmdString = "L"

        r = round(r)
        g = round(g)
        b = round(b)
        trail = round(trail)
        period = round(period)

        ran = range(0,255)
        if( (r not in ran) or (g not in ran) or (b not in ran) ):
            return 1

        if( (trail not in range(0,8)) or (period not in range(0,999)) ):
            return 1

        if(mode == "SOLID"):
            cmdString = cmdString + "0"

        if(mode == "TRAIL"):
            cmdString = cmdString + "1"

        if(mode == "PULSE"):
            cmdString = cmdString + "2"

        if(mode == "BLANK"):
            cmdString = cmdString + "9"

        cmdString = cmdString + str(r).zfill(3) + str(g).zfill(3) + str(b).zfill(3) + str(trail).zfill(2) + str(period).zfill(3)

        
        self.ser.open()
        self.ser.write(cmdString.encode())
        self.ser.close()
        time.sleep(0.05)


        return 0

    def buzzer(self, mode):
        # plays a tune on the buzzer
        # mode 0 ready
        # mode 1 attention
        # mode 2 results
        self.ser.open()
        string = "B" + mode + "\n"
        self.ser.write(string.encode("utf-8"))
        self.ser.close()
        time.sleep(0.05)

    
    def listen(self, max_duration = 15, silence_timeout = 3):
        # Setup channel info
        FORMAT = pyaudio.paInt16 # data type format
        CHANNELS = 2 # Adjust to your number of channels
        RATE = 48000 # Sample Rate
        CHUNK = 1024 # Block Size
        WAVE_OUTPUT_FILENAME = "file.wav"

        SILENCE_THRESHOLD = 64      # Loudness threshold from 0 to 32767

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

            #exit the loop if silent for longer than silence_timeout
            if(timeoutCounter > silence_timeout):
                #remove the last ~2s of audio since it is silent
                ###audio_frames = audio_frames[:-93 or None]
                break

            #stops recording when max duration is reached, regardless of recording volume
            recordingCounter = recordingCounter + CHUNK/RATE
            if(recordingCounter > max_duration):
                break
            
            """
            #this compresses the peaks of the audio signal and balances out the final loudness
            for i, x in enumerate(data_arr):
                if np.absolute(x) > COMP_THRESHOLD:
                    data_arr[i] = int(   COMP_THRESHOLD*np.sign(x) + (x - COMP_THRESHOLD*np.sign(x))/COMP_RATIO   )

            if(maxVol > SILENCE_THRESHOLD*0.8):
                #slightly boost the audio volume if it is not silent
                data_arr = data_arr*int(np.min([ 5000/np.max(data_arr) ,4]))
            """
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
        
        softFrames = np.array(audio_frames)

        is_silent = False
        if(absMaxVol < SILENCE_THRESHOLD):
            is_silent = True
        

        # Write your new .wav file with built in Python 3 Wave module
        waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        waveFile.setnchannels(1)
        waveFile.setsampwidth(audio.get_sample_size(FORMAT))
        waveFile.setframerate(RATE)
        waveFile.writeframes(b''.join([loudFrames.tobytes()]))
        #waveFile.writeframes(b''.join([np.array(audio_frames).tobytes()]))
        waveFile.close()

        audioFile = open(WAVE_OUTPUT_FILENAME, 'rb')

        transcription = self.client.audio.transcriptions.create(
            model="whisper-1",
            language="en",
            file=audioFile,
            response_format="verbose_json"
        )

        silent_probability = 0
        logprob = 0
        no_words = False

        for seg in transcription.segments:
            print("      " + str(seg.no_speech_prob))
            print("            " + str(seg.avg_logprob))
            silent_probability = max(silent_probability, seg.no_speech_prob)
            logprob = min(logprob, seg.avg_logprob)

        print(silent_probability)
        print(logprob)

        if(silent_probability > 0.8 and logprob < -0.8):
            no_words = True

        if(transcription.text == ""):
            no_words = True

        if(no_words):
            print("Could not recognise audio")
            return [1, "", is_silent]

        print("Audio transcription: " + transcription.text)
        return [0, transcription.text, is_silent]

        # Speech recognition happens here!
        """
        r = sr.Recognizer()
        with sr.AudioFile(WAVE_OUTPUT_FILENAME) as source:
            audio = r.record(source)
            
       
        try:
            print("Google thinks you said " + r.recognize_google(audio))
            #return [0, r.recognize_google(audio), is_silent]
        except sr.UnknownValueError:
            print("Could not understand audio")
            #return [1, "", is_silent]
        except sr.RequestError as e:
            print("Sphinx error; {0}".format(e))
            #return [1, "", is_silent]
        """

    #prompt, audio
    def lookAndThink(self, listen = False, returnState = ""):
        # takes 2 photos and uploads them to chatGPT
        # listen is whether the microphone is ran to listen for voices
        # returnState is what the current state is set to when the function is done running 
        self.state = "thinking"
        self.loop()


        img1 = io.BytesIO()
        img2 = io.BytesIO()

        self.cam1.capture_file(img1, format="jpeg")
        self.cam2.capture_file(img2, format="jpeg")

        with open("cam1.jpg", "wb") as c1:
            c1.write(img1.getbuffer())

        with open("cam2.jpg", "wb") as c2:
            c2.write(img2.getbuffer())

        promptString = "You'll see two images, give me a single description of the environment, structure it as a thought"

        if(listen):
            [state, text, is_silent] = self.listen()
            if(state):
                if(is_silent):

                    promptString = "You see two images and couldnʻt hear anything. Express through a short metaphor in response to what you feel about what you are observing in the style of a contemporary poet, in first-person"
                else:
                    promptString = "You see two images and hear some noises but couldnʻt make out words. Express through a short metaphor in response to what you feel about what you are observing in the style of a contemporary poet, in  first-person"
            else:
                #promptString = "You hear <" + text + "> and you see two images. Express through a short metaphor in response to what you feel about what you are observing, in first-person"
                #promptString = "You hear <" + text + "> and you see what is in two images. What is the person who took this image thinking, what are they feeling? Present your thoughts in the first person as an abstract stream of consciousness, keep keep this to around 50 words, with no special characters"
                #promptString = "You took these photos and you hear <" + text + ">. What are you thinking about? Present your thought in the first person, under 50 words"
                #promptString = "You took these photos and you hear <" + text + ">. What are you thinking about? Write down your thoughts in first person as an entry to your personal journal entry, under 50 words"
                promptString = "You are a philosopher, you took these photos and you hear <" + text + ">, what are you thinking about? Present your thoughts in first person under 50 words"

        img1_64 = base64.b64encode(img1.getvalue()).decode("utf-8")
        img2_64 = base64.b64encode(img2.getvalue()).decode("utf-8")

        response = self.client.responses.create(
            model = "gpt-4.1",
            input=[
                {
                    "role": "user",
                    "content":[
                        {
                            "type" : "input_text", "text": promptString
                        },{
                            "type" : "input_image",
                            "image_url": f"data:image/jpeg;base64,{img1_64}"
                        },
                        {
                            "type" : "input_image",
                            "image_url": f"data:image/jpeg;base64,{img2_64}"
                        }
                    ]
                }
            ]
        )

        if(returnState):
            self.state = returnState
            self.idleTimer = time.time()

        discordCommand = str(int(self.attentionTriggerState)) + response.output_text.replace("\n", "<br>") + "\n"

        p.stdin.write(  discordCommand.encode("utf-8")  )
        p.stdin.flush()

        print(response.output_text)
        return response.output_text.replace("\n", "")
    
    def init(self):
        # initialise machineEye!
        self.buzzer("0")
        self.attentionTotal = self.attentionCooldown + random.randrange(self.attentionRandom)
        [ self.lastX, self.lastY, self.lastZ ] = self.gyroRead()
        self.currentTime = time.time()
        self.idleTimer = time.time()
        self.LED("BLANK")
        


    
    def loop(self):

        # put functions here
        # functions here run only once, during state changes
        if(self.LEDState != self.state):
            print("Current State: " + self.state)
            self.LEDState = self.state

            match self.LEDState:
                case "static":
                    self.LED("BLANK")
                    self.screenPrint(".....")
                case "attention":
                    self.attentionTotal = self.attentionCooldown + random.randrange(self.attentionRandom)
                    self.LED("PULSE", 1, 7, 3, 2, 7)
                    self.buzzer("1")
                case "pickedUp":
                    self.LED("PULSE", 5, 1, 1, 25)
                case "triggered":
                    self.screenPrint(self.lookAndThink(True, "results"))
                    #time.sleep(2)
                    #self.state = "results"
                case "setDown1":
                    self.LED("PULSE", 6, 2, 2, 2, 8)
                case "setDown2":
                    self.LED("PULSE", 5, 1, 1, 2, 3)
                case "thinking":
                    self.LED("TRAIL", 2, 16, 12, 4, 8)
                case "results":
                    self.buzzer("2")
                    self.LED("PULSE", 0, 2, 6, 2, 13)


        #Checks the gyroscope periodically, sets self.moved to true if moved
        if(time.time() - self.currentTime > self.gyroFrequency):
            [newX, newY, newZ] = self.gyroRead()
            if( abs(newX - self.lastX) > self.movementThreshold or abs(newY - self.lastY) > self.movementThreshold or abs(newZ - self.lastZ) > self.movementThreshold):
                [ self.lastX, self.lastY, self.lastZ ] = [newX, newY, newZ]
                self.moved = True
                self.movedTimer = time.time()
            self.currentTime = time.time()

        if(self.moved):
            if( time.time() - self.movedTimer > self.moveResetDuration ):
                self.moved = False


        if(time.time() - self.stdFlushTimer > self.stdFlushCooldown):
            p.stdin.write(b"33333\n")
            p.stdin.flush()
            self.stdFlushTimer = time.time()


        # this match case is responsible for switching to different states
        # anything in here will run every loop, watch out!
        match self.state:
            case "static":
                
                if(self.moved):
                    self.state = "pickedUp"
                
                if(time.time() - self.idleTimer > self.attentionTotal):
                    self.idleTimer = time.time()
                    if(self.attentionState):
                        self.state = "attention"
                    else:
                        self.state = "triggered"
                        self.attentionTriggerState = 1
                    self.attentionState = not self.attentionState

            case "attention":
                if(self.moved):
                    self.state = "pickedUp"
                
                if(time.time() - self.idleTimer > self.attentionReturnCooldown):
                    self.idleTimer = time.time()
                    self.state = "static"
            
            case "pickedUp":
                if(time.time() - self.idleTimer > self.triggerRandomCooldown):
                    self.attentionTriggerState = 0
                    self.state = "triggered"
                    self.triggerRandomCooldown = random.random()*self.triggerRandom
                    self.idleTimer = time.time()

            case "setDown1":
                if(time.time() - self.idleTimer > self.setDownDuration1):
                    self.state = "setDown2"
                    self.idleTimer = time.time()

                if(self.moved):
                    self.state = "pickedUp"

            case "setDown2":
                if(time.time() - self.idleTimer > self.setDownDuration2):
                    self.state = "static"
                    self.idleTimer = time.time()

                if(self.moved):
                    self.state = "pickedUp"

            case "results":
                if(time.time() - self.idleTimer > self.resultsCooldown):
                    self.state = "setDown1"
                    self.idleTimer = time.time()


    
            





machineEye = MachineEye()
machineEye.init()

while(1):
    machineEye.loop()

#print(machineEye.listen())
