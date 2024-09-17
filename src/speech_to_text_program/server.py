import os
import time
import wave
import pyaudio
import threading
from flask import Flask, jsonify
from collections import deque
import tempfile
from datetime import datetime

app = Flask(__name__)

# Configurações de áudio
SAMPLE_RATE = 44100
CHUNK_SIZE = 4096
FORMAT = pyaudio.paInt16
CHANNELS = 1

# Stack FIFO para armazenar os áudios
MAX_STACK_SIZE = 67
audio_stack = deque(maxlen=MAX_STACK_SIZE)

# Variáveis globais para os limites de gravação
start_threshold = 0
stop_threshold = 0

# Mutex para controlar o acesso à stack de áudio
stack_mutex = threading.Lock()

def get_average_noise_level(audio_data):
    """Calcula o nível médio de som (valor absoluto médio)."""
    return sum(abs(x) for x in audio_data) / len(audio_data)

def record_environment_noise(stream):
    """Grava 3.7 segundos de áudio ambiente para medir o nível de ruído."""
    
    # Inicializa e descarta alguns blocos para estabilizar o microfone

    last1_noise_level=1;
    current_noise_level=1;
    for k in range(20): 
        last2_noise_level=last1_noise_level;
        last1_noise_level=current_noise_level;
        
        noise_data = 0.0;
        L=int(SAMPLE_RATE / CHUNK_SIZE * 1.5);
        for _ in range(L):
            block = stream.read(CHUNK_SIZE)
            audio_data = wave.struct.unpack("%dh" % CHUNK_SIZE, block)
            val=get_average_noise_level(audio_data);
            noise_data+=val;
        
        current_noise_level=noise_data/L;
        
        mean_noise_level=(current_noise_level+last1_noise_level+last2_noise_level)/3.0;
        mean_diff_noise_level=0.5*abs(current_noise_level-last1_noise_level)+0.5*abs(last1_noise_level-last2_noise_level);
        factor=mean_diff_noise_level/mean_noise_level;
        
        print('Noise level in test',k,':',current_noise_level,'factor:',factor)
        if  factor<0.05:
            break;
    
    return current_noise_level;

def record_audio():
    """Função principal de gravação de áudio em loop."""
    global start_threshold, stop_threshold

    p = pyaudio.PyAudio()
    
    # Gravação inicial para medir o ruído ambiente
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=SAMPLE_RATE, input=True, frames_per_buffer=CHUNK_SIZE)
    stream.stop_stream()
    stream.close()



    # Inicializa o fluxo de áudio principal
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=SAMPLE_RATE, input=True, frames_per_buffer=CHUNK_SIZE)

    noise_level = record_environment_noise(stream)
    start_threshold = 1.5 * noise_level
    stop_threshold = 1.5 * noise_level
    
    print(f"Ruído ambiente: {noise_level}, Limiar início: {start_threshold}, Limiar fim: {stop_threshold}")


    while True:
        # Lê blocos de áudio em chunks
        block = stream.read(CHUNK_SIZE)
        audio_data = wave.struct.unpack("%dh" % CHUNK_SIZE, block)
        sound_level = get_average_noise_level(audio_data)
        
        if sound_level >= start_threshold:
            print("Gravação iniciada...")
            audio_frames = []
            init_time = datetime.now()

            while True:
                audio_frames.append(block)
                block = stream.read(CHUNK_SIZE)
                audio_data = wave.struct.unpack("%dh" % CHUNK_SIZE, block)
                sound_level = get_average_noise_level(audio_data)

                if sound_level < stop_threshold:
                    silent_time = 0
                    while silent_time < 1.618:
                        silent_time += CHUNK_SIZE / SAMPLE_RATE
                        block = stream.read(CHUNK_SIZE)
                        audio_frames.append(block)
                        audio_data = wave.struct.unpack("%dh" % CHUNK_SIZE, block)
                        sound_level = get_average_noise_level(audio_data)
                        if sound_level >= stop_threshold:
                            silent_time = 0
                    break

            # Cria o arquivo temporário .wav
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            wave_file = wave.open(temp_file.name, 'wb')
            wave_file.setnchannels(CHANNELS)
            wave_file.setsampwidth(p.get_sample_size(FORMAT))
            wave_file.setframerate(SAMPLE_RATE)
            wave_file.writeframes(b''.join(audio_frames))
            wave_file.close()

            with stack_mutex:
                # Adiciona o caminho do arquivo e a hora de início à stack
                if len(audio_stack) == MAX_STACK_SIZE:
                    # Remove o arquivo mais antigo da stack
                    oldest = audio_stack.popleft()
                    if os.path.exists(oldest[1]):
                        os.remove(oldest[1])
                audio_stack.append((init_time, temp_file.name))
                print(f"Áudio salvo: {temp_file.name}")

@app.route('/current_size', methods=['GET'])
def current_size():
    with stack_mutex:
        return jsonify({'current_size': len(audio_stack)})

@app.route('/maximum_size', methods=['GET'])
def maximum_size():
    return jsonify({'maximum_size': MAX_STACK_SIZE})

@app.route('/last_data', methods=['GET'])
def last_data():
    with stack_mutex:
        if len(audio_stack) > 0:
            last_item = audio_stack[-1]
            return jsonify({'init_time': last_item[0].strftime('%Y-%m-%d %H:%M:%S'), 'audio_filepath': last_item[1]})
        else:
            return jsonify({'error': 'Stack is empty'})

if __name__ == "__main__":
    threading.Thread(target=record_audio).start()
    app.run(host='0.0.0.0', port=5555)

