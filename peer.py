'''
A P2P messaging system does not rely on a central server to attend to its request. Instead each peer has its own client and server part.

We will proceed to implement this in steps. Starting from the basic functionality and eventually adding more complex functionalities at the end 

The goal is to create a pure p2p messaging app which is based on the gnutella routing algorithm.


Stage 1:
    Create a peer with server and client side with sockets. 
    When intializing a peer, we should also give it a name.

    Open 2 peer and connect them together
    Peer A should act as client and should Peer B should act as server.   

    Note, only 1 connection should happen at one time. If there are more than 2 clients trying to connect to the same peer server, the request should be denied. Server should print out a message.
    Client should also print out a message.

    Also add a debugging function to help print out shitzz. Maybe we can use the logging module

Stage 2:
    Ensure that each peer has an always listening server side. While the client side can connnect to a specific server

    We need to allow multi threading to occur here. There maybe multiple client peer trying to contact a server peer. The server peer should be able to allow connection from all client. Client messages are multiple in types. There is ping, connect, find. 


Stage 3:
    Initialize the peer by knowing at least 1 user


    Implement a find function. 
    - This has an input called TTL
    - checks if a username is in your peerlist
    - if username is not in your peerlist, ask your peers to check if they have the username in their peerlist
        - to check with peers, just send them a message
        in this format
        Key:value
        key = FIND
        value = username:TTL

    - this should happen recursively
    - this function will return ( True/False , identity/ None)
    
    identity = (username,peerHost, peerServerPort)
        
    
    
'''
import socket
from _thread import *
import threading
import sys
import util

class Peer:

    def __init__(self,peername, serverPort, clientPort, peerFriendName, peerFriendServerPort, peerFriendHost=None, serverHost=None, clientSocket=None):

        self.serverPort = int(serverPort)
        self.clientPort = int(clientPort)
        self.clientSocket = clientSocket
        self.peername = peername
        self.serverSocket = None
        self.lock = threading.Lock()



        
        #Determines whether the serverHost is given
        #If not, provide the localHost as the serverHost by connecting to google
        if serverHost: self.serverHost = serverHost
        else: self.serverHost =  self.__init_serverHost()

        # if no peerFriendHost,the peerFriendHost is localhost
        if peerFriendHost == None: peerFriendHost = self.serverHost



        # key = username
        # value = (ipAddress,Port)

        self.peerList = {}
        self.peerList[peerFriendName] = (peerFriendHost,peerFriendServerPort)

        # Should print out at the beginning what is our ports and stuff. It is good to declare
        print('Peername: {} \nServerHost: {} \nServerPort:{}'.format(self.peername,self.serverHost, self.serverPort))
        self.create_serverSocket()

###################### Threading #########################

    def threaded(self,clientConn):
        while True:

            # data received from client
            # This may need to be upgraded into a thread
            data = clientConn.recv(1024)
            data = str(data.decode())

            # This happens when client sent an empty message or sent a quit message
            if not data or data[0:4] == 'quit':
                print(' {} is disconnected'.format(data[4:]))
            
                # lock released on exit of client
                self.lock.release()
                break

            elif data[0:4] == util.TYPE_FIND:
                # We should call check peers
                data = data.split(':')
                peerToFind = data[1]
                TTL = int(data[2])
                if TTL > 0:
                    present,identity = self.find_peer(peerToFind)
                    if present:
                        message = util.create_message(util.TYPE_FOUND, identity)
                        clientConn.send(message)
                        # Lock released upon sending message
                        #self.lock.release()
                        # Close Client connection
                        #clientConn.close()
                        
                else:
                    message = util.create_message(util.TYPE_NOTFOUND,"")
                    clientConn.send(message)
                    # Lock released upon sending message
                    #self.lock.release()
                    # Close Client connection
                    #clientConn.close()
                
                    
            else:
                print('\nfrom client: {}'.format(data))
                # Allow peer to communicate 
                message = input('Type message to client:')
                message = util.create_message(util.TYPE_CHAT,message)
                clientConn.send(message)

        # Connection is closed
        clientConn.close()



##################### Server Methods ###########################

    '''
    Create a tcp client socket to connect to google
    Then retrieves our localhost
    '''
    def __init_serverHost(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('www.google.com', 80))
            serverHost = s.getsockname()[0]
            s.close()
        return serverHost

    '''
    Should the server socket always be running?
    Yes, it should always be running. The server should start once the peer has been called.
    Thus, we can include this method in the init function of peer.
    This method returns the socket
    '''
    def create_serverSocket(self):
        print('Creating server socket  for {}'.format(self.peername))
        # Creating a server socket
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Bind the socket to the server Host and the server port
        self.serverSocket.bind((self.serverHost, self.serverPort))
        # Become a server socketng outside ocnnections
        # Argument allows 5 incoming connect request before refusing
        self.serverSocket.listen(5)

    def main_loop_server(self):
        while True:
            # extrablish connection with client
            clientConn, clientAddr = self.serverSocket.accept() 

            # Lock acquired by client
            self.lock.acquire()
            print('Connected to {}:{}'.format(clientAddr[0],clientAddr[1]))

            # start a new thread and return its identifier
            start_new_thread(self.threaded, (clientConn,))
            break


########################### CLIENT METHODS ####################
    '''
    Input: serverHost and server port
    This will create a client socket that will connet to the server socket
    Ouput: The client socket 
    '''
    def create_clientSocket(self,serverHost,serverPort):
        print('Creating Client Socket with port {}'.format(self.clientPort))
        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clientSocket.connect((serverHost, int(serverPort)))  
        

    def main_loop_client(self,serverHost, serverPort):
         # Create client socket
        self.create_clientSocket(serverHost, serverPort)

        # Message you send to server to initiate connection
        message = "Hi I am " + self.peername
        print('Waiting for server to allow connection.')

        while True:

            # Message sent to server
            self.clientSocket.send(message.encode())

            # message received from server
            data = self.clientSocket.recv(1024)


            # Print the received message from server
            print('\nFrom server: {}'.format(str(data.decode())))

            # Ask the client for message or command 'quit'
            message = input('Message to server:')
            if message != 'quit':
                continue
            else:
                message = message + self.peername
                message = util.create_message(util.TYPE_CHAT, message)
                self.clientSocket.send(message)
                break
        # close the client socket connection   
        print('Client socket is disconnected.') 
        self.clientSocket.close()



##################### Peer Methods ######################
# identity = 'username:ipaddress:port'
# purely strings

    def check_peerList(self, peerToFind):
        identity = None
        if peerToFind in self.peerList:
            identity = self.peerList.get(peerToFind)
            identity = '{}:{}:{}'.format(peerToFind,identity[0],identity[1])
        else:
            return False, identity
        return True, identity

    
    def add_peer(self,identity):
        self.peerList[identity[0]] = identity[1:]
    
    def remove_peer(self, username):
        self.peerList.pop(username)

    def find_peer(self,peerToFind, TTL=3):

        present, identity = self.check_peerList(peerToFind)
        
        # Only allow checks if TTL is > 0
        if TTL > 0:
            if present:
                return True,identity
            else:
                # We need to contact each of our peerlist and ask them to check their peer list

                for username, identity in self.peerList.items():
                    # Create a client socket  to contact peer
                    self.create_clientSocket(identity[0], identity[1])
                    
                    # Create message to send to peer
                    message = util.create_message(util.TYPE_FIND, peerToFind+":"+str(TTL -1))

                    # send peer the username and the TTL
                    print('Contacting {} to find {} with TTL {}.'.format(username,peerToFind, TTL-1 ))
                    self.clientSocket.send(message)

                    # we wait for the server reply
                    data = self.clientSocket.recv(1024)
                    data = str(data.decode())
                    data = data.split(':')

                    # parse data into present, identity
                    if data[0] == util.TYPE_FOUND:
                        identity = data[1:]
                        return True, identity
                    else:
                        print('Moving on to next peer')
                        continue
        else:
            print('TTL has reached zero.\nCannot find {}'.format(peerToFind))
            return False, None

                


     
##################### Main loop ############################
    ''' 
    The mainLoop is the loop that the peer keeps running
    Suggestion: Might wanna add a try excpet and finally here. this will make the code more robust

    We need to allow the server to run on a separate thread so that we can use the interface as a client

    We are facing some problems with how the client and server communicates
    What we can do is create a FSM to allow the peer to switch from 1 state to another. There are limited states so this should not be too 


    Keep the main loop short. Put all implementations outside.
    '''

    def mainLoop(self):
        while True:

            # CLIENT SIDE

            '''
            Waits for incoming messages.
            Messages are of different action:
                1. Connect or C 
                    Allow client to send messages to server
                    Allow client to quit connection with server with 'Q'

                    Not implemented: Receiving messages from server
                2. Listen
                    We allow the server listen in/ Appear online

            If message C is provided, Client wants to connect to a server
            User needs to provide 2 things
                1. serverHost
                2. serverPort

        
            '''

            action = input('What action do you want? \n1. Connect(C) \n2. Listen(L)\n3. Find(F)\nAction: ')
            
            # This will be our handler function
            # We can improve this by having a handler
            # For now we will use an if else to handle basic action 
            if action in util.ACTION_CONNECT:

                # # If none is given, give local host as the serverHost
                # serverHost = input('Please input the serverHost that you want to connect to.\nServerHost:')
                # if serverHost == '':serverHost = self.serverHost

                # serverPort = input('Please input the serverPort that you want to connect to.\nServerPort:')

                peerToFind = input('Type Username: ')
                present, identity = self.check_peerList(peerToFind)
                if present:
                    identity = identity.split(':')
                    serverHost = identity[1]
                    serverPort = identity[2]
                else:
                    print('User is not in your Contacts\nTry Finding the user in your network.')
                             
                # Here we insert the main loop client
                self.main_loop_client(serverHost,serverPort)
            
            # SERVER SIDE
            elif action in util.ACTION_LISTEN:
                print('Listening for other peers to connect.')
                self.main_loop_server()

            # FIND a peer
            elif action in util.ACTION_FIND:
                peerToFind = input('Username to find: ')
                present, identity = self.find_peer(peerToFind)
                if present:
                    print('User is found.')
                    print('{}\n'.format(identity))
                else:
                    print('User not within network.\n Try increasing your TTL.')
            
            else:
                print('Wrong command! Try again.')





def main():
    if len(sys.argv) < 2:
        print('Syntax: python3 peer.py peername serverPort clientPort peerFriendName peerFriendServerPort')
        sys.exit(-1)

    peername = sys.argv[1]
    serverPort = sys.argv[2]
    # Optimize this by allowing the system to find its own free port
    clientPort = sys.argv[3]
    peerFriendName = sys.argv[4]
    peerFriendServerPort = sys.argv[5]

    peer = Peer(peername,serverPort,clientPort,peerFriendName, peerFriendServerPort)
    peer.mainLoop()



if __name__== '__main__':
    main()