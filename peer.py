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

        self.peerList = {}
        self.peerList[peerFriendName] = (peerFriendHost,peerFriendServerPort)

        # Should print out at the beginning what is our ports and stuff. It is good to show the info to user.
        print('Peername: {} \nServerHost: {} \nServerPort:{}'.format(self.peername,self.serverHost, self.serverPort))
        print('PeerList: {}\n'.format(self.peerList))
        self.create_serverSocket()

###################### Threading #########################

    def threaded(self,clientConn):
        while True:

            # data received from client
            data = clientConn.recv(1024)
            data = str(data.decode())

            # This happens when client sent an empty message or sent a quit message
            if not data or data[0:4] == util.TYPE_QUIT:
                # lock released on exit of client
                self.lock.release()
                break

            elif data[0:4] == util.TYPE_FIND:
                # We should call check peers
                data = data.split(':')
                peerToFind = data[1]
                TTL = int(data[2])
                #print('peer {} has TTL {}'.format(self.peername,TTL))

                if TTL > 0 and peerToFind:
                    present,identity = self.find_peer(peerToFind)
                    if present:
                        message = util.create_message(util.TYPE_FOUND, identity)
                        clientConn.send(message)

                        
                else:
                    message = util.create_message(util.TYPE_NOTFOUND,"")
                    clientConn.send(message)
                   
            else:
                print('From client: {}'.format(data))
                # Allow peer to communicate 
                message = input('To client: ')
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
            print('Connected to {}:{}\n'.format(clientAddr[0],clientAddr[1]))

            # start a new thread and return its identifier
            start_new_thread(self.threaded, (clientConn,))
            
            
            


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
            message = str(data.decode())
            print('From server: {}'.format(message[5:]))

            # Ask the client for message or command 'quit'
            message = input('To server:')
            if message != 'quit':
                continue
            else:
                message = message + self.peername
                message = util.create_message(util.TYPE_QUIT, message)
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
                    # Decrement TTL by 1
                    TTL = TTL -1
                    
                    # Create a client socket  to contact peer
                    self.create_clientSocket(identity[0], identity[1])
                    
                    
                    # Create message to send to peer
                    message = util.create_message(util.TYPE_FIND, peerToFind+":"+str(TTL))

                    # send peer the username and the TTL
                    print('Contacting {} to find {}.'.format(username,peerToFind, TTL))
                    self.clientSocket.send(message)

                    # we wait for the server reply
                    data = self.clientSocket.recv(1024)
                    data = str(data.decode())
                    data = data.split(':')

                    # tell the server to end connection
                    message = util.create_message(util.TYPE_QUIT,self.peername)
                    self.clientSocket.send(message)

                    # parse data into present, identity
                    if data[0] == util.TYPE_FOUND:
                        identity = data[1:]
                        #self.add_peer(identity)
                        return True, identity
                    else:
                        print('Moving on to next peer')
                        continue
        else:
            print('TTL has reached zero.\nCannot find {}'.format(peerToFind))
            return False, None

                     
##################### Main loop ############################
    def mainLoop(self):
        while True:

           # CLIENT SIDE
            action = input('What action do you want? \n1. Connect(C) \n2. Listen(L)\n3. Find(F)\nAction: ')
            
            # This will be our handler function
            if action in util.ACTION_CONNECT:

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
        print('Syntax: python3 peer.py peername serverPort clientPort neighbourName neighbourServerPort')
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