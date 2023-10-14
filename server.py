import socket
import threading
import pickle

HOST = '192.168.5.73'
PORT = 5018
HEADER = 255
DISCONNECT_MESSAGE = '@QUIT'
CHECK_ONLINE_MESSAGE = '@List'

server =  socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))

# a dictionary of online clients including their ids as keys and socket as value {id: (conn)}
connectedClients = {}
lock = threading.Lock()

def isDuplicate(conn, clientId):
    if clientId in connectedClients.keys():
        print(f"id {clientId} exists")
        conn.send("fail".encode())
        return True
    conn.send("success".encode())
    return False


def handleClient(conn, addr):

    connected = True
    while connected:

        """
        The client will follow this procedure:
            1. He will send the length of the message in bytes
            2. He will send the actual message
        """
        try:
            msg_length = conn.recv(HEADER).decode()
        except Exception as e:
            connected = quitMessage(clientId)
            break
        
        if msg_length:
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode()

            if ("Connect" not in msg):
                print(msg)

            if "Connect" in msg:
                clientId = msg[8:].rstrip('\x00')
                lock.acquire()
                if not isDuplicate(conn, clientId):
                    print(f'{msg}')
                    conn.send("30".encode())
                    connectedClients[clientId] = conn
                    #update the users about the change in the list
                    updateClientsList(clientId)
                lock.release()
               
            elif "List" == msg:
                listMessage(conn)

            elif '[MESSAGE]' in msg:
                forwardMessage(clientId, msg)

            elif "Quit" == msg:
                connected = quitMessage(clientId)

                
    conn.close()
    

def start():
    server.listen()
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handleClient, args=(conn, addr))
        thread.start()



def quitMessage(clientId):
    lock.acquire()
    connectedClients.pop(clientId)
    #update the users about the change in the list
    updateClientsList(clientId)
    lock.release()

    return False

    
def listMessage(conn): 
    conn.send(f'The number of online clients is: {len(connectedClients)}\n'.encode())
    for id in connectedClients:
        conn.send(f'----Client Id: {id}\n'.encode())
    

def forwardMessage(sourceId, msg):
    parts = msg.split(' ', 2)
    destinationId = parts[1][1:-1]

    writtenMessage = " ".join(parts[2:])
    writtenMessage = writtenMessage[0:]
    lock.acquire()
    if(destinationId in connectedClients):
        connectedClients[destinationId].send(f'Message from user {sourceId} : {writtenMessage}'.encode())
    else:
        connectedClients[sourceId].send(f'User {destinationId} is Offline'.encode())
    lock.release()



def updateClientsList(clientId):
    #send the updated list to everyone except the new user
    for id,conn in connectedClients.items():
        if(id != clientId):
            listMessage(conn)



print('[STARTING] Server is starting...')
start()