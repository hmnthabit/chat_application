import socket
from threading import Thread

import sys
import os

import abc
import argparse

from datetime import datetime
from pathlib import Path

class base_chat_server(metaclass=abc.ABCMeta):
    '''
    This class defines the abstract interface for any chat server sub-class
    All chat servers sub-classes must override the abstract methods of this class

    Abstract methods:
        - setup_server(): Setup the server binding
        - client_handling(): For Handling all connected chat clients
        - broadcast_msg(): Sending a message to all chat clients
        - remove_client(): Terminate and remove the connection of a specific client
    '''

    @abc.abstractmethod
    def setup_server(self):
        pass

    @abc.abstractmethod
    def client_handling(self):
        pass

    @abc.abstractmethod
    def broadcast_msg(self):
        pass

    @abc.abstractmethod
    def remove_client(self):
        pass


class chat_server(base_chat_server):
    def __init__(self, ip, port, log_file_name=""):

        self.ip = ip
        self.port = port
        self.all_chat_clients = {}

        self.log_file_name = log_file_name
        self.log_file_path = ""
        self.log_file_handle = ""

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Reuse the same local address (in bind()) instead of initiating a new connection
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        if self.log_file_name:
            self.setup_log_file()

    def setup_log_file(self):

        temp_path = Path("logs")
        temp_path.mkdir(parents=True, exist_ok=1)

        # Write the starting message and close it
        self.log_file_path = f"{temp_path}/{self.log_file_name}"
        self.log_file_handle = open(self.log_file_path, mode="w")

        self.log_file_handle.write("Logging Started\n")
        self.log_file_handle.close()

    def log_events(self, msg):
        '''
       Logging the events (msg parameter) by writing it external file
        '''

        t = datetime.now()
        new_msg = f"[{t}]: {msg}\n"
        self.log_file_handle = open(self.log_file_path, "a").write(new_msg)

    def setup_server(self):
        '''
        Setup the server connection
        '''

        try:
            self.s.bind((self.ip, self.port))

            self.s.listen(3)
            print(f"Listening {self.ip}:{self.port}")

        except Exception as e:
            print(f"({e}) exception raised")
            sys.exit()

        # Infinite loop for receiving any new connection
        while 1:
            try:

                client_socket, client_address = self.s.accept()

                log_msg = f"Received a connection from {client_address}"
                print(log_msg)

                # Log the event if the file handle exists
                if self.log_file_handle:
                    self.log_events(log_msg)

                # Add to the clients
                self.all_chat_clients[client_socket] = client_address

                # Get the client name first
                client_socket.send(b"Welcome to the chat room!\nPlease Enter your name: ")
                client_name = client_socket.recv(1024).decode()

                # Launch a new thread for each client
                t = Thread(target=self.client_handling, args=[client_socket, client_name, client_address])
                t.start()

            except Exception as e:
                print(f"({e}) exception raised")
                self.s.close()
                sys.exit()

    def client_handling(self, client_socket, client_name, client_address):
        '''
        Main function for handling the client messages
        '''
        while 1:

            try:
                msg = client_socket.recv(1024).decode()

                if msg.lower() != "quit":
                    msg = f"{client_name}> {msg}".encode()

                    # Send the msg to all clients
                    self.broadcast_msg(msg, client_socket)

                elif msg == "":
                    pass

                # If the message == "quit"
                else:
                    self.remove_client(client_socket, client_name, client_address)

                    # Exit the thread
                    sys.exit()

            except Exception as e:
                print(f"({e}) exception raised")
                sys.exit()

    def broadcast_msg(self, msg, client_socket):
        '''
        Sending a message to all the clients in the chat excpet the sender `client_socket`
        '''
        for cs in self.all_chat_clients:
            if cs != client_socket:
                cs.send(msg)

    def remove_client(self, client_socket, client_name, client_address):
        '''
        Remove client connection
        '''
        log_msg = f"{client_address} has closed the connection"
        print(log_msg)

        # Log the event if the file handle exists
        if self.log_file_handle:
            self.log_events(log_msg)

        msg = f"[{client_name}] has the left chat server".encode()
        self.broadcast_msg(msg, client_socket)

        del self.all_chat_clients[client_socket]

# =========================================================================================

def parse_args():
    arg_parser = argparse.ArgumentParser(usage='chat_server.py -p PORT --file LOG_FILE')

    # Arguments
    arg_parser.add_argument('-p', metavar='port', type=int, required=True)
    arg_parser.add_argument('--file', metavar='log file name', type=str,)

    args = arg_parser.parse_args()

    args.log_file_name = args.file

    return args

if __name__ == "__main__":

    args = parse_args()

    if args.log_file_name:
        a = chat_server("127.0.1.1", args.p, args.log_file_name)
        a.setup_server()

    else:
        a = chat_server("127.0.1.1", args.p)
        a.setup_server()