import requests

def get_current_size():
    response = requests.get('http://localhost:5555/current_size')
    if response.status_code == 200:
        print("Tamanho atual da stack:", response.json()['current_size'])
    else:
        print("Erro ao obter o tamanho atual da stack.")

def get_maximum_size():
    response = requests.get('http://localhost:5555/maximum_size')
    if response.status_code == 200:
        print("Tamanho máximo da stack:", response.json()['maximum_size'])
    else:
        print("Erro ao obter o tamanho máximo da stack.")

def get_last_data():
    response = requests.get('http://localhost:5555/last_data')
    if response.status_code == 200:
        data = response.json()
        if 'error' in data:
            print("Erro:", data['error'])
        else:
            print(f"Último dado - Início: {data['init_time']}, Arquivo de áudio: {data['audio_filepath']}")
    else:
        print("Erro ao obter o último dado da stack.")

if __name__ == "__main__":
    print("Comandos disponíveis: current_size, maximum_size, last_data")
    command = input("Digite o comando: ").strip()

    if command == "current_size":
        get_current_size()
    elif command == "maximum_size":
        get_maximum_size()
    elif command == "last_data":
        get_last_data()
    else:
        print("Comando inválido.")

