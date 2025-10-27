import threading
import socket
import json
import os
import sys
from cryptog import encrypt_message, decrypt_message

from colorama import init, Fore, Style
init(autoreset=True) 


LOBBY_FILE = 'lobby.json'
lobby_lock = threading.RLock()

def read_lobby():
    with lobby_lock:
        if not os.path.exists(LOBBY_FILE):
            return []
        try:
            with open(LOBBY_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []



def print_help_menu():
    print(Fore.CYAN + "\n--- Central de Ajuda ---\n")
    print(Style.BRIGHT + "Este programa ('cliente.py') permite que você entre em chats.")

    print(Style.BRIGHT + "\nComandos disponíveis DENTRO de um chat:")
    print(Fore.GREEN + "  /help         " + Style.RESET_ALL + "- Mostra esta ajuda dentro do chat.")
    print(Fore.GREEN + "  /sair         " + Style.RESET_ALL + "- Desconecta você do chat atual e retorna ao menu principal.")
    print(Fore.GREEN + "  /users        " + Style.RESET_ALL + "- Lista todos os usuários atualmente online na mesma sala que você.")
    print(Fore.GREEN + "  /info         " + Style.RESET_ALL + "- Mostra o nome da sala, nº de membros e limite.")
    print(Fore.GREEN + "  /pm <user> <msg>" + Style.RESET_ALL + "- Envia uma mensagem privada para um usuário.")
    print(Fore.GREEN + "  /togglepm     " + Style.RESET_ALL + "- Bloqueia ou desbloqueia o recebimento de PMs.")
    print(Fore.GREEN + "  /votekick <user>" + Style.RESET_ALL + "- Inicia uma votação para expulsar um usuário.")
    print(Fore.GREEN + "  /votemute <user>" + Style.RESET_ALL + "- Inicia uma votação para silenciar um usuário (10 min).")
    print(Fore.GREEN + "  /vote <yes/no>" + Style.RESET_ALL + "- Vota numa eleição em progresso.")


    print(Style.BRIGHT + "\nPara Anfitriões (rodando 'servidor.py'):")
    print(" - Para criar um chat, você deve rodar o script 'servidor.py'.")
    print(" - No terminal do servidor, você pode usar os seguintes comandos:")
    print(Fore.YELLOW + "    users         " + Style.RESET_ALL + "- Lista os usuários conectados na sua sala.")
    print(Fore.YELLOW + "    kick <user>   " + Style.RESET_ALL + "- Expulsa um usuário da sua sala.")
    print(Fore.YELLOW + "    warn <user>   " + Style.RESET_ALL + "- Envia um aviso formal para um usuário (usado pelo anti-flood).")
    print(Fore.YELLOW + "    mute <user> [min]" + Style.RESET_ALL + "- Silencia um usuário (permanentemente ou por [min] minutos).")
    print(Fore.YELLOW + "    unmute <user> " + Style.RESET_ALL + "- Remove o silêncio de um usuário.")
    print(Fore.YELLOW + "    broadcast <msg>" + Style.RESET_ALL + "- Envia um anúncio global para todos na sala.")
    print(Fore.YELLOW + "    sair          " + Style.RESET_ALL + "- Desliga a sala atual e volta ao menu de criação.")

    print(Style.BRIGHT + "\nLimitações:")
    print(" - Chats públicos não precisam de senha, mas chats privados sim.")
    print(" - Um log de salas privadas (porta e senha) é salvo em 'private_rooms.log'.")
    print(" - O Anti-Flood automático bane após 3 infrações (Aviso -> Mute 5 min -> Expulsão).")
    print(Fore.CYAN + "------------------------")
    input(Style.DIM + "\nPressione <Enter> para voltar ao menu...\n")



def main():

    while True:
        print(Style.BRIGHT + Fore.GREEN + "\n--- Bem-vindo ao Chat (Terminal) ---\n")
        print("1: Entrar em um Chat Público")
        print("2: Entrar em um Chat Privado")
        print("3: Ajuda")
        print("4: Sair do Programa")
        choice = input("Escolha: ")

        porta_para_conectar = None
        SENHA = None

        if choice == '1':
            servers = read_lobby()
            if not servers:
                print(Fore.YELLOW + "\nNenhum chat público encontrado")
                continue

            print(Style.BRIGHT + "\n--- Chats Públicos Ativos ---")
            for i, server in enumerate(servers):

                members = server.get('members', 0)
                max_m_raw = server.get('max', 'N/A')
                max_m = str(max_m_raw) if max_m_raw is not None else 'N/A'
                print(f"{i+1}: {server.get('name', 'Sala Sem Nome')} ({members}/{max_m}) - Porta: {server.get('port', 'N/A')}")

            try:
                select_num = int(input("\nDigite o número do chat para entrar: "))
                if 1 <= select_num <= len(servers):
                    selected_server = servers[select_num - 1]
                    porta_para_conectar = int(selected_server['port'])
                    print(f"Conectando à sala '{selected_server['name']}'...")
                else:
                    print(Fore.RED + "Número inválido\n")
                    continue
            except (ValueError, KeyError, IndexError): 
                print(Fore.RED + "Entrada inválida ou erro ao ler lobby\n")
                continue

        elif choice == '2':
            try:
                porta_para_conectar = int(input("\nDigite a PORTA do chat privado: "))
                SENHA = input("Digite a SENHA do chat: \n")
            except ValueError:
                print(Fore.RED + "A porta deve ser um número\n")
                continue

        elif choice == '3':
            print_help_menu()
            continue

        elif choice == '4':
            print("\nSaindo do programa. Até logo!\n")
            sys.exit()

        else:
            print(Fore.RED + "Opção inválida\n")
            continue

        if not porta_para_conectar:
            continue

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        client.settimeout(10.0)

        try:
            client.connect(('localhost', porta_para_conectar))

            client.settimeout(None)

            if SENHA is not None:
                client.send(SENHA.encode('utf-8'))


            initial_response = client.recv(9)

            if initial_response == b"FAIL     ": 
                print(Fore.RED + "\n[Erro] Senha incorreta. Conexão recusada\n")
                client.close()
                continue
            elif initial_response == b"FAIL_FULL":
                 print(Fore.RED + "\n[Erro] A sala está cheia\n")
                 client.close()
                 continue


            remaining_bytes_needed = 44 - len(initial_response)

            if remaining_bytes_needed < 0:
                 print(Fore.RED + f"\n[Erro] Resposta inesperada do servidor ao receber chave: {initial_response}")
                 client.close()
                 continue
            elif remaining_bytes_needed > 0:
   
                 client.settimeout(2.0)
                 key_bytes_remaining = client.recv(remaining_bytes_needed)
                 client.settimeout(None) 
                 CHAVE_BYTES = initial_response + key_bytes_remaining
            else: 
                 CHAVE_BYTES = initial_response


            if len(CHAVE_BYTES) != 44:
                print(Fore.RED + f"\n[Erro] Falha ao receber a chave completa. Esperava 44 bytes, recebeu {len(CHAVE_BYTES)}\n")
                client.close()
                continue

            username = input('Usuário> ')
            client.send(encrypt_message(username, CHAVE_BYTES))
            client.settimeout(5.0) 
            auth_status = client.recv(9)
            client.settimeout(None)

            if auth_status == b"FAIL_NAME":
                print(Fore.RED + f"\n[Erro] O nome '{username}' já está em uso nesta sala\n")
                client.close()
                continue
            elif auth_status != b"OK_NAME  ":
                print(Fore.RED + f"\n[Erro] Resposta inesperada do servidor após enviar nome: {auth_status}\n")
                client.close()
                continue


        except ConnectionRefusedError:
            print(Fore.RED + f"\n[Erro] Ninguém está ouvindo na porta {porta_para_conectar}\n")
            continue
        except socket.timeout:
             print(Fore.RED + f"\n[Erro] Tempo limite de conexão/autenticação excedido para a porta {porta_para_conectar}\n")
             try: client.close()
             except: pass
             continue
        except Exception as e:
            print(Fore.RED + f"\nNão foi possivel estabelecer conexão: {e}\n")
            try: client.close() 
            except: pass
            continue

        print(Fore.GREEN + "\n--- Conectado ao Chat ---\n")
        print("Digite '/help' para ver os comandos")

        global stop_threads
        stop_threads = False

        thread = threading.Thread(target=receiveMessages, args=[client, CHAVE_BYTES])
        thread2 = threading.Thread(target=sendMessages, args=[client, CHAVE_BYTES])

        thread.start()
        thread2.start()

        thread.join()
        thread2.join()

        print(Style.BRIGHT + "\nDesconectado. Voltando ao menu principal...\n")



def receiveMessages(client, chave):
    global stop_threads
    while not stop_threads:
        try:
            msg_criptografada = client.recv(2048)
            if not msg_criptografada:
                if not stop_threads:
                     print(Fore.YELLOW + '\nO servidor fechou a sala\n')
                     stop_threads = True
                break
            msg = decrypt_message(msg_criptografada, chave)

            if msg.startswith('<'): 
                parts = msg.split('>', 1)
                if len(parts) == 2: print(Fore.WHITE + Style.BRIGHT + parts[0] + '>' + Style.NORMAL + parts[1] + '\n')
                else: print(Style.BRIGHT + msg + '\n')
            elif msg.startswith('[PM'): print(Fore.YELLOW + Style.BRIGHT + msg + '\n')
            elif msg.startswith('[Sistema]'): print(Fore.MAGENTA + Style.BRIGHT + msg + '\n')
            elif msg.startswith('[ANÚNCIO'): print(Fore.CYAN + Style.BRIGHT + msg + '\n')
            elif msg.startswith('[Votação]'): print(Fore.BLUE + Style.BRIGHT + msg + '\n')
            else: print(Fore.GREEN + msg + '\n')


        except ConnectionResetError:
             if not stop_threads: print(Fore.RED + '\nA conexão foi resetada pelo servidor\n')
             break
        except Exception as e:
            if not stop_threads: print(Fore.RED + f'\nErro ao receber/processar mensagem: {e}\n')
            break

    stop_threads = True



def sendMessages(client, chave):
    global stop_threads
    while not stop_threads:
        try:
            msg = input('\n')
            if stop_threads: break
            if msg.lower() == '/sair':
                print(Style.BRIGHT + "Saindo do chat...\n")
                stop_threads = True
                try: client.send(encrypt_message("/sair", chave))
                except: pass
                break

            if msg.strip():
                client.send(encrypt_message(msg, chave))
        except EOFError:
             print(Style.BRIGHT + "Input interrompido. Saindo...\n")
             stop_threads = True
             break
        except OSError as e:
            if not stop_threads: print(Fore.RED + f"\nErro de conexão ao enviar: {e}\n")
            stop_threads = True
            break
        except Exception as e:
             if not stop_threads: print(Fore.RED + f"\nErro inesperado ao enviar mensagem: {e}\n")
             stop_threads = True
             break

    try: client.close()
    except: pass

if __name__ == "__main__":
    main()