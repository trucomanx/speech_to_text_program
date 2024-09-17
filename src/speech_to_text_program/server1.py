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
    # Criar um arquivo temporário para o áudio
    temp_wav_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)

    # Obter os dados de áudio em formato WAV
    wav_data = audio_data.get_wav_data()

    # Abrir o arquivo WAV temporário para escrita
    with wave.open(temp_wav_file, "wb") as wf:
        # Obter a taxa de amostragem e a largura da amostra do objeto AudioData
        sample_rate = audio_data.sample_rate
        sample_width = audio_data.sample_width

        # Definir os parâmetros do áudio
        wf.setnchannels(1)  # Canal mono, pois speech_recognition trabalha com áudio mono
        wf.setsampwidth(sample_width)  # Tamanho de amostra dinâmico
        wf.setframerate(sample_rate)  # Usar a taxa de amostragem do áudio

        # Escrever os dados no arquivo
        wf.writeframes(wav_data)

    # Retornar o caminho para o arquivo temporário
    return temp_wav_file.name

################################################################################

app = Flask(__name__)

language_str = '';

# Pilha de dados
data_stack = deque();

# Função para converter voz em texto e adicionar à pilha
# https://github.com/Uberi/speech_recognition/blob/master/reference/library-reference.rst
def voice_to_text():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        # Ajustar para o ruído ambiente
        print("\nadjust_for_ambient_noise Please remain in silence for 5 second...\n")
        recognizer.adjust_for_ambient_noise(source,duration=5)
        recognizer.dynamic_energy_threshold = True;
        recognizer.dynamic_energy_adjustment_ratio = 1.5;
        
        print("Working now!")
        
        while True:
            try:
                print('waiting audio...')
                audio = recognizer.listen(source)
                text = recognizer.recognize_whisper(audio)
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                data_stack.append({'time': timestamp, 'text': text})
                print(f"Text recognized and added to stack: {text}")
                
            except sr.UnknownValueError:
                print("Não foi possível entender o áudio");
                pass
                
            except sr.RequestError as e:
                print(f"Error requesting results from speech recognition service; {e}")
                
            except Exception as e:
                print(f"Unexpected error: {e}")
                
            time.sleep(0.01)  

# Endpoint para retornar o tamanho atual da pilha
@app.route('/current_size', methods=['GET'])
def current_size():
    return jsonify({'current_size': len(data_stack)})

# Endpoint para retornar o tamanho máximo da pilha
@app.route('/maximum_size', methods=['GET'])
def maximum_size():
    return jsonify({'maximum_size': data_stack.maxlen})

# Endpoint para retornar o último dado da pilha
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
    """Carrega a configuração do arquivo JSON, criando-o com valores padrão se não existir."""
    home_directory = os.path.expanduser('~')
    config_directory = os.path.join(home_directory, '.config', 'speech_to_text_program')
    config_path = os.path.join(config_directory, 'config.json')
    
    # Cria o diretório de configuração se não existir
    os.makedirs(config_directory, exist_ok=True)
    
    if not os.path.exists(config_path):
        # Cria o arquivo com valores padrão se não existir
        with open(config_path, 'w') as file:
            json.dump(DEFAULT_CONFIG, file, indent=4);
            print("Created config file in:",config_path);
    
    # Carrega a configuração do arquivo
    with open(config_path, 'r') as file:
        config = json.load(file)
        print("Loaded config data from:",config_path);
    
    return config

def main():
    config = load_config()
    host = config.get('host', DEFAULT_CONFIG['host']) # Valor padrão se não especificado
    port = config.get('port', DEFAULT_CONFIG['port']) # Valor padrão se não especificado
    stack_size = config.get('stack_size', DEFAULT_CONFIG['stack_size']) # Valor padrão se não especificado
    language_str = config.get('language', DEFAULT_CONFIG['language']) # Valor padrão se não especificado
    
    
    print("      host:",host)
    print("      port:",port)
    print("stack_size:",stack_size)
    print("  language:",language_str)
    
    data_stack = deque(maxlen=stack_size);
    
    # Iniciar a função de voz em um thread separado
    voice_thread = threading.Thread(target=voice_to_text, daemon=True)
    voice_thread.start()
    
    app.run(host=host, port=port, debug=True)
    
    
if __name__ == '__main__':
    main();

