Cria um programa servidor "server.py" usando flask na porta 5555 (em python) que esteja em bucle infinito gravando áudios em blocos de 4096 amostras (usa pyaudio).
A frequencia de amostragem é de 44100 hz. 
Se o nível de som ultrapassar um umbral de início então o sistema grava o áudio até que o nível de som medio baixe outro umbral durante 1.618 segundos. 
O áudio obtido é guardado num arquivo temporal wav (o diretório de arquivos temporais deve ser obtido da biblioteca tempfile). 
O endereço do wav é salva numa stack FIFO de máximo 67 elementos, cada elemento da stack de dados (tupla (init_time,audio_filepath)) tem a hora em que o áudio iniciou. 
Quando a stack está cheia, o elemento mais antigo é apagado (por isso a stack tem tamanho máximo), mas também deve ser apagado o arquivo de áudio associado a esse elemento da stack para evitar arquivos de áudio órfãs.

Antes do bucle infinito de grvação de audio, o servidor tem uma função record_environment_noise(stream) que grava 3.7 segundos desde o stream de áudio, no momento dessa gravação ninguém estará falando e será útil para saber o nivel de ruido do ambiente. 
O limiar de início de gravação será 1.9 vezes o ruido ambiente.
O limiar de fim de gravação será 1.5 vezes o ruido ambiente. 
O nivel do ruido e' calculado sobre os blocos de amostras mediante uma funcao get_average_noise_level() mediante o valor absoluto médio, esa mesma funcao deve ser usado na funcao que calcula ruido de ambiente e a funcao que calcula o nivel de som no bucle infinito. 
Evita estar abrindo e fechando a comunicação com a "sound card" abre uma comunicação e recolhe os blocos de amostras de áudio e descarta as que não ultrapassem o limiar.
Existe um problema com o calculo do nivel de ruido e com o estado inicial do microfone ou do fluxo de áudio (stream) na primeira vez em que ele é aberto, pois o microfone pode estar ajustando o ganho ou a sensibilidade nos primeiros momentos, resultando em leituras incorretas. Por isso abre e fecha o fluxo de áudio uma vez antes de iniciar a gravação efetiva do nivel de ruido, permitindo que o hardware passe por um ciclo completo de inicialização. Alemd disso seria prudente descartar os primeiros blcoos de amostras de audios para garantir mais ainda a estabilidade inicial.

O programa servidor server.py aceita só os seguintes 3 comando pelo cliente client.py.
* Um comando current_size para retornar o tamanho atual da stack
* Um comando maximum_size para retornar o tamanho maximo da stack
* Um comando last_data para retornar o último dado da stack

Cria um exemplo de client.py


