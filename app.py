from flask import Flask, render_template, request, session, redirect, url_for, Response, jsonify
from openpyxl import Workbook, load_workbook
import numpy as np
import speech_recognition as sr
import wave
import pyaudio
import os
from deepgram import Deepgram
import asyncio, json
from translate import Translator
import sys
import pyaudio


 
r=sr.Recognizer()

# x = random.randint(100000,999999)
app = Flask(__name__)
app.secret_key = '1234qwerasdfzxcv,./098poilkjmnb\][]'  # Change this to a secure secret key
app.config['SESSION_TYPE'] = 'filesystem'

languages_available = ['English', 'Japanese', 'Chinese', 'German', 'Hindi', 'French', 'Korean', 'Portuguese', 'Italian', 'Spanish', 'Indonesian', 'Dutch', 'Turkish', 'Filipino', 'Polish', 'Swedish', 'Bulgarian', 'Romanian', 'Arabic', 'Czech', 'Greek', 'Finnish', 'Croatian', 'Malay', 'Slovak', 'Danish', 'Tamil', 'Ukrainian', 'Russian']
languages_code = {'English':'en', 'Japanese':'ja', 'Chinese':'zh', 'German':'de', 'Hindi':'hi', 'French':'fr', 'Korean':'ko', 'Portuguese':'pt', 'Italian':'it', 'Spanish':'es', 'Indonesian':'id', 'Dutch':'nl', 'Turkish':'tr', 'Filipino':'tl', 'Polish':'pl', 'Swedish':'sv', 'Bulgarian':'bg', 'Romanian':'ro', 'Arabic':'ar', 'Czech':'cs', 'Greek':'el', 'Finnish':'fi', 'Croatian':'hr', 'Malay':'ms', 'Slovak':'sk', 'Danish':'da', 'Tamil':'ta', 'Ukrainian':'uk', 'Russian':'ru'}






@app.route('/')
def index():
    print('Request for index page received')
    return render_template('index.html', languages = languages_available)




@app.route('/start_recording', methods=['POST'])
def start_recording():

    data = request.get_json()
    # Access individual parameters
    pname = data.get('pname')

    print(f"Received parameters - Name: {pname}")

    if not os.path.exists('./audio'):
        os.mkdir('./audio/')
    try:
        if not os.path.exists('./audio/'+pname):
            os.mkdir('./audio/'+pname)
        lis = os.listdir('./audio/'+pname)
        file_path = "./audio/"+pname+"/recorded_audio_"+str(len(lis))+".wav"  # Adjust as needed
        print(len(lis))
        print("hi")
        # file_path = "./audio/recorded_audio_"+str(len(lis))+".wav"
        print(file_path)
        recorded_wordsss = record_audio(file_path)  # Call the recording function
        print(recorded_wordsss)
        translated_word = translate_english_to_hindi(recorded_wordsss)
        return jsonify({"status": "recording_started", 'words': translated_word})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

# def translate_english_to_hindi(from_language,to_language):
def translate_english_to_hindi(text):
    # translator= Translator(to_lang="hi")
    translator= Translator(to_lang="hi")
    translation = translator.translate(text)
    print("Translated Word: "+translation)
    return translation


def record_audio(file_path, silence_threshold=2.0):
    chunk = 1024
    sample_format = pyaudio.paInt16
    channels = 1
    fs = 44100
    print("hello")
    p = pyaudio.PyAudio()

    stream = p.open(format=sample_format,
                    channels=channels,
                    rate=fs,
                    frames_per_buffer=chunk,
                    input=True)

    recognizer = sr.Recognizer()

    # Adjust for ambient noise before recording
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        print(recognizer.energy_threshold)
        frames = []

        print("Recording...")

        # Adjust the timeout to control the duration of silence needed to stop recording
        try:
            audio = recognizer.listen(source, timeout=silence_threshold)
            frames.append(audio.frame_data)
            print("Finished recording.")
            
        except sr.WaitTimeoutError:
            print("No speech detected. Stopping recording.")

    stream.stop_stream()
    stream.close()
    p.terminate()
    print("hello1")

    with wave.open(file_path, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(sample_format))
        wf.setframerate(fs)
        wf.writeframes(b''.join(frames))

    recog_words = test_accuracy(file_path, "Hello")
    print("\n\n")
    print(recog_words)
    return recog_words


async def deepg(FILE):
    MIMETYPE = 'audio/wav'
    DEEPGRAM_API_KEY = '1f94104b6180b7f5370de816800a6f8efae9005f'

    # Initialize the Deepgram SDK
    deepgram = Deepgram(DEEPGRAM_API_KEY)

    # Check whether requested file is local or remote, and prepare source
    if FILE.startswith('http'):
        # file is remote
        # Set the source
        source = {
            'url': FILE
        }
    else:
        # file is local
        # Open the audio file
        audio = open(FILE, 'rb')

        # Set the source
        source = {
            'buffer': audio,
            'mimetype': MIMETYPE
        }

    # Send the audio to Deepgram and get the response
    response = await asyncio.create_task(
    deepgram.transcription.prerecorded(
        source,
        {
        'smart_format': True,
        'model': 'nova-2',
        }
    )
    )

    

    # Write only the transcript to the console
    
    print(response["results"]["channels"][0]["alternatives"][0]["transcript"])
    return response["results"]["channels"][0]["alternatives"][0]["transcript"]




def test_accuracy(audio_path, expected_text):
    recognizer = sr.Recognizer()
    print(audio_path)

    with sr.AudioFile(audio_path) as source:
        audio = recognizer.record(source)

    try:
        # recognized_text = recognizer.recognize_google(audio)
        # recognized_text = deepg(audio_path)
        try:
            # If running in a Jupyter notebook, Jupyter is already running an event loop, so run main with this line instead:
            #await main()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            words = loop.run_until_complete(deepg(audio_path))
            recognized_text =  words
        except Exception as e:
            exception_type, exception_object, exception_traceback = sys.exc_info()
            line_number = exception_traceback.tb_lineno
            print(f'line {line_number}: {exception_type} - {e}')
        print("Expected Text: {}".format(expected_text))
        print("Recognized Text: {}".format(recognized_text))
        accuracy = calculate_accuracy(expected_text, recognized_text)
        print("Accuracy: {:.2%}".format(accuracy))
        return recognized_text
    except sr.UnknownValueError:
        print("Could not understand audio")
    except sr.RequestError as e:
        print("Error with the speech recognition service; {0}".format(e))


def calculate_accuracy(expected, recognized):
    expected_words = set(expected.lower().split())
    recognized_words = set(recognized.lower().split())

    common_words = expected_words.intersection(recognized_words)
    accuracy = len(common_words) / len(expected_words)

    return accuracy


if __name__ == '__main__':
    app.run(debug=True)