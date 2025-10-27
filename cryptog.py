from cryptography.fernet import Fernet
import threading
import socket 



def generate_key():
    return Fernet.generate_key()



def encrypt_message(message, key):
    fernet = Fernet(key)
    encrypted_message = fernet.encrypt(message.encode())
    return encrypted_message



def decrypt_message(encrypted_message, key):
    fernet = Fernet(key)
    decrypted_message = fernet.decrypt(encrypted_message).decode()
    return decrypted_message



def receive_messages(conn, key):
    while True: 
        encrypted_message = conn.recv(2048)
        if not encrypted_message:
            break
        message = decrypt_message(encrypted_message, key)
        print('Amigo:', message)