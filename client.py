from threading import *
import socket
import time
import pickle
import re
import os

HOST = '192.168.5.73'
PORT = 5018
HEADER = 255
CLIENT_ID_LENGTH = 8
DISCONNECT_MESSAGE = '@QUIT'
CHECK_ONLINE_MESSAGE = '@LIST'




client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))
connected = True


"""
    Adds padding to the byte representation of the message length. 
    to ensure that the length of the message is exactly HEADER bytes long. 
    If the length is less than HEADER, spaces are added to fill the remaining space.
"""
def send(msg, client):
    msg = msg.encode()
    msgLength = len(msg)
    msgLength = str(msgLength).encode()
    msgLength += b' ' * (HEADER - len(msgLength))

    client.send(msgLength)
    client.send(msg)


def receiveClientMsg(client):
        global connected
        while connected: 
            try:
                msg = client.recv(1024).decode()
                if msg:
                    print(f'\n{msg}') 
                
            except Exception as e:
                break
            


def sendMsgToServer(client):
    global connected

    #This is the pattern in regex for this Syntax: (otherclientid) message-statement
    pattern = r'\(([^)]+)\)'

    while connected:

        command = input("Write the command: ")
        
        if (command.upper() == DISCONNECT_MESSAGE):
            send('Quit' ,client)
            connected = False
            client.close()
            os._exit(0)

        elif (command.upper() == CHECK_ONLINE_MESSAGE):
           send('List' ,client)
           time.sleep(2)
           
        elif (re.match(pattern, command)):
            clientToClientMessage(client, command)
            time.sleep(2)

        else:
            print("Unknown command")
            



def connectMessage(client):

    #In case the user wrote a string as his id, ask him to write his id again as an 8 bytes integer

    
    while True:  
        clientId = input("Enter your ID: ")
        if(not clientId.isnumeric()):
            continue

        else:    
            #convert it to string in order to performe the padding 
            clientId = str(clientId)

            #if some client has name less than 8 bytes then
            #perform padding to keep it of 8 Bytes
            if len(clientId.encode()) <= 8:
                clientId = clientId.ljust(CLIENT_ID_LENGTH, '\0')
            elif len(clientId.encode()) > 8:
                clientId = str(input("Enter your ID: "))
                

            #connect message
            send(f'Connect {clientId}', client)
            msg = client.recv(7).decode()
            print(msg)
            if msg == "success":
                return clientId
            else:
                print("duplicate id, try again")


def clientToClientMessage(client, command):

        parts = command.split(' ')
        destinationId = parts[0][1:-1]
        msg = " ".join(parts[1:])
        msg = msg[0:]
        if (len(msg.encode())>239):
            print(f"\nmessage is too long to be sent, remove {len(msg.encode()) - 239} character(s) and try again.")
        else:
            send(f'[MESSAGE] ({destinationId}) {msg}', client)



def aliveMessage(clientId, client, intervalTime):
    global connected
    while connected:
        try:
            time.sleep(int(intervalTime))
            send(f'alive {clientId}', client)
        except Exception as e:
            print(e)


#send the client id to the server
clientId = connectMessage(client)
#receive alive message
intervalTime = client.recv(HEADER).decode()


# Create a separate thread for the sleep operation
sleepThread = Thread(target=aliveMessage, args=(clientId, client, intervalTime))

# Create a separate thread for the receiving messages
receiveThread = Thread(target=receiveClientMsg, args=(client,))

# Create a separate thread for the sending messages
sendThread = Thread(target=sendMsgToServer, args=(client,))
 

sleepThread.start()
receiveThread.start()
sendThread.start()

sleepThread.join()
receiveThread.join()
sendThread.join()