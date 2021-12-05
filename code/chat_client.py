import socket
import sys
import tkinter as tk 

import argparse

from threading import Thread

import abc

# --- Varabiles ---
ip = "127.0.1.1"
port = 5555

# --- Colors ---
back_color = "#505455"
message_frame_color = "#4B5A5F"
text_color = "#FFFFFF"


class base_chat_client(metaclass=abc.ABCMeta):
    '''
    This class defines the abstract interface for any chat client sub-class
    All chat client (e.g. CLI, GUI) sub-classes must override the abstract methods of this class

  Abstract Methods:
        - send_message(): Send a message to the chat server 
        - receive_message(): Recives a messsage from the chat server and display it
        - run(): Run the chat client threads/functions
        - client_exit(): Terminate the connection 
    '''

    def __init__(self, chat_server_ip, chat_server_port):
        # init
        self.s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.ip = chat_server_ip
        self.port = chat_server_port

        self.client_name = ""

    def connect_to_server(self):
        try:
            self.s.connect((self.ip, self.port))
            wlc_msg = self.s.recv(1024)

            print(wlc_msg.decode())

            self.client_name = input()
            self.s.send(self.client_name.encode())

        except Exception as e:
            print(f"({e}) exception raised")
            sys.exit()

    @abc.abstractmethod      
    def receive_message(self):
        pass

    @abc.abstractmethod
    def send_message(self):
        pass

    @abc.abstractmethod
    def run(self):
        pass

    def client_exit(self):

        try:
            self.s.send(b"quit")
            self.s.close()
            sys.exit()

        except Exception as e:
            sys.exit()

class chat_client_cli(base_chat_client):

    '''
    This class handle the CLI functionality. It's not related to the GUI class 
    '''

    def __init__(self, chat_server_ip, chat_server_port):
        # init
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip = chat_server_ip
        self.port = chat_server_port

        self.client_name = ""
        self.connect_to_server()

    def receive_message(self):
        while 1:
            try:
                msg = self.s.recv(1024).decode()
                print(f"\r{msg}\n{self.client_name}>",end="")

            except Exception as e:
                print(f"[{e}] exception was raised ")
                sys.exit()

    def send_message(self):
        while 1:
            msg = input(f"{self.client_name}>")

            if msg != "" and msg.lower() != "quit":
                self.s.send(msg.encode())

            elif msg == "":
                pass
            else:
                self.client_exit()

    def run(self):
        '''
        Run the client by starting `receive_message()` and `send_message()` threads
        '''
        # This thread will be stopped whenever t2 is stopped or the `run()` exited --> (`daemon=1`)
        t = Thread(target=self.receive_message,daemon=1)
        t.start()

        t2 = Thread(target=self.send_message,)
        t2.start()

# ================================================================================
class chat_gui:

    '''
    This class setup the GUI (e.g.windows and frames) for the GUI chat clients only
    '''

    def __init__(self):
        # GUI varabiles
        self.main_chat_window =  tk.Tk()

        # Frames
        self.main_chat_frame = 0
        self.msg_list_frame = 0

        self.msg_list_box = 0
        self.message_entry_box = 0

    def init_main_window(self):
        self.main_chat_window.title("Chat Application")

        self.main_chat_window.geometry("800x400")

        # Set bg color
        self.main_chat_window.configure(bg=back_color)

        # Configure the rows in the main interface
        self.main_chat_window.rowconfigure(0, weight=1)
        self.main_chat_window.rowconfigure(1, weight=0)

        # Configure the columns
        self.main_chat_window.columnconfigure(0, weight=1)

    def init_frames(self):
        #  Frames
        self.main_chat_frame =  tk.Frame(master=self.main_chat_window)
        self.main_chat_frame.grid(row=1, column=0, sticky="we", padx=20)

        # Message_list frame
        self.msg_list_frame =  tk.Frame(master=self.main_chat_window)
        self.msg_list_frame.grid(row=0, column=0, sticky="nsew", columnspan=4)

        # Scrollbar
        self.scrollbar_widget =  tk.Scrollbar(master=self.msg_list_frame)
        self.scrollbar_widget.pack(side= tk.RIGHT, fill= tk.Y,)

    def init_msg_interface(self):
        # --- Buttons ---
        self.msg_list_box =  tk.Listbox(master=self.msg_list_frame, bg=message_frame_color, fg=text_color)
        self.msg_list_box.pack(side= tk.LEFT, fill= tk.BOTH, expand=True)

        # --- Message entry box ---
        self.message_entry_box =  tk.Entry(master=self.main_chat_frame)
        self.message_entry_box.pack(fill= tk.BOTH,)

    # Should be overridden by `chat_client_gui()`
    def bind_send_event(self):
        pass

    def init_gui(self):
        '''
        Running the gui functions in the correct order to initialize the gui interface
        '''
        self.init_main_window()
        self.init_frames()
        self.init_msg_interface()
        self.bind_send_event()


class chat_client_gui(base_chat_client, chat_gui):

    '''
    - Main chat client GUI class.
    - It inherits `chat_gui()` for initlizing the GUI instead of including all the methods in one class

    Added methods:
        - bind_send_event(): Bind `Send` button to `send_message()` function

    '''

    def __init__(self, chat_server_ip, chat_server_port):

        self.s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.ip = chat_server_ip
        self.port = chat_server_port

        chat_gui.__init__(self)
        self.init_gui()

        self.client_name = ""
        self.connect_to_server()

    def bind_send_event(self):
        '''
        Bind send button to self.send_message_gui() method
        '''
        # Bind send button to `send_message_gui_callback()`
        # No need for event for binding with `button` widget
        self.send_button =  tk.Button(master=self.main_chat_window, text="Send", command=lambda: self.send_message())
        self.send_button.grid(row=1,column=1,sticky="ew",pady=10)

        # Bind return key to `send_message_gui_callback()`
        send_message_gui_callback = lambda event: self.send_message()
        self.message_entry_box.bind("<Return>", send_message_gui_callback)
        self.message_entry_box.insert(0, "Type message")

    def receive_message(self):
        # Infinite loop for receiving the messages from the server
        while 1:
            try:
                msg = self.s.recv(1024).decode()
                self.msg_list_box.insert( tk.END,msg,)

            except Exception as e:
                print(f"[{e}] exception was raised ")
                sys.exit()

    def send_message(self):
        # Get the message from the msg entery box
        msg = self.message_entry_box.get()

        # Clean the msg box
        self.message_entry_box.delete(0, tk.END)

        if msg.lower() != "quit":
            self.s.send(msg.encode())

            msg = f"{self.client_name}>{msg}"
            self.msg_list_box.insert( tk.END, msg)

        elif msg == "":
            pass

        # If the user type "quit", then exit
        else:
            self.client_exit()

    def run(self):
        '''
        Run the client by starting receive_message() thread and the GUI
        '''
        # Start `receive()` thread first before executing the GUI loop
        t = Thread(target=self.receive_message)
        t.start()

        self.main_chat_window.mainloop()

# ================================================================================

def parse_args():

    arg_parser = argparse.ArgumentParser(
        usage='chat_client.py -i SERVER_ADDRESS -p PORT --mode GUI/CLI')

    # Arguments
    arg_parser.add_argument('-i',  type=str, metavar='ip',required=True, help='Chat server IP')

    arg_parser.add_argument('-p',metavar='port',type=int,required=True)

    # Default to GUI
    arg_parser.add_argument('--mode', action="store", type=str,default="GUI", help='Client interface (e.g. CLI, GUI)')

    args = arg_parser.parse_args()

    # Rename
    args.ip = args.i
    args.port = args.p

    return args


if __name__ == "__main__":

    args = parse_args()

    if args.mode == "GUI":
        b = chat_client_gui(args.ip,args.port)
        b.run()

    else:
        a = chat_client_cli(args.ip,args.port)
        a.run()
