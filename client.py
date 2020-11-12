# Import socket module 
import socket 
import sys


def Main(username): 
	# local host IP '127.0.0.1' 
	host = '127.0.0.1'

	# Define the port on which you want to connect 
	port = 12346

	s = socket.socket(socket.AF_INET,socket.SOCK_STREAM) 

	# connect to server on local computer 
	s.connect((host,port)) 

	# message you send to server 
	message = "Hi i am " + username
	print('Waiting for server to allow connection')
	while True: 

		# message sent to server 
		s.send(message.encode('ascii')) 

		# messaga received from server 
		data = s.recv(1024) 

		# print the received message 
		# here it would be a reverse of sent message 
		print('\nReceived from the server : ',str(data.decode('ascii'))) 

      
		# ask the client whether he wants to continue 
		message = input('\nMessage to server: ') 
		if message != 'quit': 
			continue
		else:
			message = message + username
			s.send(message.encode())
			break

	# close the connection 
	s.close() 

if __name__ == '__main__': 
    if len(sys.argv) != 2:
        print('Proper usage: python3 client.py username')

    username = str(sys.argv[1])
    Main(username)
