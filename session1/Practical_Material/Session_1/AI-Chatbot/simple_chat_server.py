import sys
import time
import socket

import random
import json
import torch
import nltk

from model import NeuralNet
from nltk_utils import bag_of_words, tokenize

if len(sys.argv) != 2:
    print("Correct usage: script, port number")
    exit()

nltk.download('punkt')
    
port = int(sys.argv[1])

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


with open('intents.json', 'r') as json_data:
    intents = json.load(json_data)

FILE = "data.pth"
data = torch.load(FILE)

input_size = data["input_size"]
hidden_size = data["hidden_size"]
output_size = data["output_size"]
all_words = data["all_words"]
tags = data["tags"]
model_state = data["model_state"]


model = NeuralNet(input_size, hidden_size, output_size).to(device)
model.load_state_dict(model_state)
model.eval()

bot_name = "H-UWE"

print('Setup Server...')
time.sleep(1)
#Get the hostname, IP Address from socket and set Port
soc = socket.socket()
ip = "0.0.0.0"

soc.bind((ip, port))

print(ip, '({})'.format(ip))

soc.listen(1) #Try to locate using socket
print('Waiting for incoming connections...')

connection, addr = soc.accept()

print("Received connection from ", addr[0], "(", addr[1], ")\n")
print('Connection Established. Connected From: {}, ({})'.format(addr[0], addr[0]))

#get a connection from client side
client_name = connection.recv(1024)
client_name = client_name.decode()

connection.send(bot_name.encode())

time.sleep(10)

print(client_name + ' has connected.')
print('Press [bye] to leave the chat room')

connection.send(str("Welcome to the H-UWE chat bot server").encode())

while True:

	recv_message = connection.recv(1024)
	recv_message = recv_message.decode()
	
	print("{} > {}".format(client_name, recv_message))

	send_message = "I do not understand..."
	
	tokenized_recv_message = tokenize(recv_message)
	X = bag_of_words(tokenized_recv_message, all_words)
	X = X.reshape(1, X.shape[0])
	X = torch.from_numpy(X).to(device)

	output = model(X)
	_, predicted = torch.max(output, dim=1)
	tag = tags[predicted.item()]

	probs = torch.softmax(output, dim=1)
	prob = probs[0][predicted.item()]
	if prob.item() > 0.75:
		for intent in intents['intents']:
			if tag == intent["tag"]:
				send_message = "{}".format(random.choice(intent['responses']))
				print("{} > {}".format(bot_name, send_message))
	
	connection.send(send_message.encode())
	
	if recv_message.__contains__('bye'):
		break
		
connection.close()
soc.close()
