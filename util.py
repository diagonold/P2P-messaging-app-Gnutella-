# MESSAGE types
TYPE_FIND = 'FIND'
TYPE_CHAT = 'CHAT'
TYPE_QUIT = 'QUIT'
TYPE_FOUND = '1111'
TYPE_NOTFOUND = '0000'

# ACTION types
ACTION_CONNECT = ['Connect','connect','C','c']
ACTION_LISTEN = ['Listen', 'listen','L','l']
ACTION_QUIT = ['Quit','quit,','Q','q']
ACTION_FIND = ['Find','find','f','F']

def create_message(type,value):
    message = '{}:{}'.format(type,value)
    return message.encode()