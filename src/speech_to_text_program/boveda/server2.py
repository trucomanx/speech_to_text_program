#!/usr/bin/python3

from flask import Flask, request, jsonify
from collections import deque
from datetime import datetime
import speech_recognition as sr
import threading
import time
import os
import json

################################################################################
import wave
import tempfile

def save_audio_data_to_temp_wav(audio_data):
    temp_wav_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    wav_data = audio_data.get_wav_data()

    with wave.open(temp_wav_file, "wb") as wf:
        sample_rate = audio_data.sample_rate
        sample_width = audio_data.sample_width

        wf.setnchannels(1)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(wav_data)

    return temp_wav_file.name

################################################################################

app = Flask(__name__)

language_str = ''

data_stack = deque()

def voice_to_text():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\nadjust_for_ambient_noise Please remain in silence for 5 second...\n")
        recognizer.adjust_for_ambient_noise(source, duration=5)
        recognizer.dynamic_energy_threshold = True
        recognizer.dynamic_energy_adjustment_ratio = 1.5
        
        print("Working now!")
        
        while True:
            try:
                print('waiting audio...')
                audio = recognizer.listen(source)
                text = recognizer.recognize_whisper(audio,language='portuguese')
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                data_stack.append({'time': timestamp, 'text': text})
                print(f"Text recognized and added to stack: {text}")
                
            except sr.UnknownValueError:
                print("Não foi possível entender o áudio")
                
            except sr.RequestError as e:
                print(f"Error requesting results from speech recognition service; {e}")
                
            except Exception as e:
                print(f"Unexpected error: {e}")
                
            time.sleep(0.01)

@app.route('/current_size', methods=['GET'])
def current_size():
    return jsonify({'current_size': len(data_stack)})

@app.route('/maximum_size', methods=['GET'])
def maximum_size():
    return jsonify({'maximum_size': data_stack.maxlen})

@app.route('/last_data', methods=['GET'])
def last_data():
    if data_stack:
        return jsonify(data_stack[-1])
    else:
        return jsonify({'message': 'Empty stack'})

################################################################################

DEFAULT_CONFIG = {
    "host": "0.0.0.0",
    "port": 5555,
    "stack_size": 128,
    "language":"pt"
}

def load_config():
    home_directory = os.path.expanduser('~')
    config_directory = os.path.join(home_directory, '.config', 'speech_to_text_program')
    config_path = os.path.join(config_directory, 'config.json')
    
    os.makedirs(config_directory, exist_ok=True)
    
    if not os.path.exists(config_path):
        with open(config_path, 'w') as file:
            json.dump(DEFAULT_CONFIG, file, indent=4)
            print("Created config file in:", config_path)
    
    with open(config_path, 'r') as file:
        config = json.load(file)
        print("Loaded config data from:", config_path)
    
    return config

def run_flask_app():
    config = load_config()
    host = config.get('host', DEFAULT_CONFIG['host'])
    port = config.get('port', DEFAULT_CONFIG['port'])
    
    print("      host:", host)
    print("      port:", port)
    
    app.run(host=host, port=port, debug=True)

def main():
    global data_stack
    
    config = load_config()
    stack_size = config.get('stack_size', DEFAULT_CONFIG['stack_size'])
    language_str = config.get('language', DEFAULT_CONFIG['language'])
    
    print("stack_size:", stack_size)
    print("  language:", language_str)
    
    data_stack = deque(maxlen=stack_size)
    
    # Iniciar o servidor Flask em um thread separado
    flask_thread = threading.Thread(target=run_flask_app, daemon=True)
    flask_thread.start()
    
    # Executar a função de voz na thread principal
    voice_to_text()

if __name__ == '__main__':
    main()

