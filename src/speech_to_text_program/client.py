#!/usr/bin/python3

import requests



def send_request(base_url,endpoint):
    try:
        response = requests.get(f'{base_url}/{endpoint}')
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def main():
    # URL base do servidor
    BASE_URL = 'http://localhost:5555'
    
    while True:
        print("\nComandos disponíveis:")
        print("1. Ver tamanho atual da pilha")
        print("2. Ver tamanho máximo da pilha")
        print("3. Ver último dado da pilha")
        print("4. Sair")
        choice = input("Escolha uma opção (1-4): ")

        if choice == '1':
            print(send_request(BASE_URL,'current_size'))
        elif choice == '2':
            print(send_request(BASE_URL,'maximum_size'))
        elif choice == '3':
            print(send_request(BASE_URL,'last_data'))
        elif choice == '4':
            break
        else:
            print("Opção inválida. Tente novamente.")

if __name__ == '__main__':
    main()

