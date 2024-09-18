import numpy as np
import pyaudio
import wave
import os
from collections import deque
from flask import Flask, jsonify

app = Flask(__name__)

# Configurações
THRESHOLD_RATIO_START = 1.5  # Fator para iniciar a gravação com base no ruído
THRESHOLD_RATIO_STOP = 1.2   # Fator para parar a gravação com base no ruído
MAX_STACK_SIZE = 67          # Tamanho máximo da stack FIFO
SAMPLE_RATE = 44100          # Taxa de amostragem (Hz)
DURATION = 0.1               # Duração de cada gravação em segundos (100ms)
PRE_RECORDING_SECONDS = 3    # Tempo para gravação inicial (pré-determinação de ruído)
CHUNK_SIZE = int(SAMPLE_RATE * DURATION)  # Tamanho do chunk de áudio
FORMAT = pyaudio.paInt16     # Formato do áudio
CHANNELS = 1                 # Canal mono

# Stack de áudio
audio_stack = deque(maxlen=MAX_STACK_SIZE)

# Inicializar PyAudio
p = pyaudio.PyAudio()

# Função para calcular o valor RMS em float32
def calculate_rms(audio_data):
    """Calcula o valor RMS do áudio com valores em float32."""
    if len(audio_data) == 0:
        return 0
    audio_data = audio_data.astype(np.float32)
    return np.sqrt(np.mean(np.square(audio_data)))

# Grava o áudio e retorna os dados
def record_audio(duration):
    """Grava áudio por uma duração especificada e retorna como float32."""
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=SAMPLE_RATE,
                    input=True,
                    frames_per_buffer=CHUNK_SIZE)

    frames = []
    for _ in range(0, int(SAMPLE_RATE / CHUNK_SIZE * duration)):
        data = stream.read(CHUNK_SIZE)
        frames.append(np.frombuffer(data, dtype=np.int16).astype(np.float32))  # Convertendo para float32

    stream.stop_stream()
    stream.close()

    return np.concatenate(frames)

# Função para gravar o áudio em um arquivo .wav
def save_audio_to_wav(audio_data, filepath):
    """Salva o áudio em formato WAV (float32)."""
    with wave.open(filepath, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(4)  # 4 bytes para float32
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_data.astype(np.float32).tobytes())

@app.route('/current_size', methods=['GET'])
def get_current_size():
    """Retorna o tamanho atual da stack."""
    return jsonify({"current_size": len(audio_stack)})

@app.route('/maximum_size', methods=['GET'])
def get_maximum_size():
    """Retorna o tamanho máximo da stack."""
    return jsonify({"maximum_size": MAX_STACK_SIZE})

@app.route('/last_data', methods=['GET'])
def get_last_data():
    """Retorna o último dado da stack (tupla com tempo e caminho do arquivo)."""
    if len(audio_stack) > 0:
        last_item = audio_stack[-1]
        return jsonify({"init_time": last_item[0], "audio_filepath": last_item[1]})
    return jsonify({"error": "No audio data available"})

def measure_noise_level():
    """Mede o nível de ruído inicial para definir os thresholds de gravação."""
    print("Medindo nível de ruído inicial...")
    pre_noise_audio = record_audio(PRE_RECORDING_SECONDS)
    noise_rms = calculate_rms(pre_noise_audio)
    threshold_start = noise_rms * THRESHOLD_RATIO_START
    threshold_stop = noise_rms * THRESHOLD_RATIO_STOP
    print(f"Nível de ruído RMS: {noise_rms:.4f}")
    print(f"Threshold de início: {threshold_start:.4f}, Threshold de fim: {threshold_stop:.4f}")
    return threshold_start, threshold_stop

def run_audio_recording(threshold_start, threshold_stop):
    """Executa o loop de gravação contínua, armazenando o áudio na stack FIFO."""
    print("Iniciando a gravação de áudio...")
    recording = False
    temp_audio_data = []

    while True:
        audio_chunk = record_audio(DURATION)
        rms_value = calculate_rms(audio_chunk)
        
        if not recording and rms_value > threshold_start:
            print("Iniciando gravação, som detectado!")
            recording = True
            temp_audio_data = [audio_chunk]
        
        elif recording and rms_value > threshold_stop:
            temp_audio_data.append(audio_chunk)
        
        elif recording and rms_value <= threshold_stop:
            print("Finalizando gravação...")
            recording = False
            
            # Salvar o áudio em um arquivo temporário
            audio_filepath = f"temp_audio_{len(audio_stack)}.wav"
            audio_data = np.concatenate(temp_audio_data)
            save_audio_to_wav(audio_data, audio_filepath)
            
            # Adicionar o caminho do arquivo e o tempo na stack FIFO
            audio_stack.append((p.get_default_input_device_info()['defaultSampleRate'], audio_filepath))
            temp_audio_data = []

if __name__ == '__main__':
    # Medir o nível de ruído inicial
    threshold_start, threshold_stop = measure_noise_level()

    # Iniciar o loop de gravação em um thread separado
    from threading import Thread
    recording_thread = Thread(target=run_audio_recording, args=(threshold_start, threshold_stop))
    recording_thread.start()

    # Iniciar o servidor Flask
    app.run(host='0.0.0.0', port=5555)

