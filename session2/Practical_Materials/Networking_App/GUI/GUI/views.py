import re
import os
import socket
import threading
import socketserver

from .forms import *

from django.http import HttpResponse
from django.shortcuts import redirect,render
from django.contrib.auth import login,logout,authenticate

rules_dict = dict()

listener_running = False

tcp_server = ("0.0.0.0", 9876)

udp_server = ("0.0.0.0", 6789)

packet_inspection = dict()

message_board = {
    "TCP": dict(),
    "UDP": dict()
}

class TCPHandler(socketserver.StreamRequestHandler):

    def handle(self):

        # Receive and print the data received from client

        print(self.__dict__)

        print("Recieved one request from {}".format(self.client_address[0]))

        msg = self.rfile.readline().strip()

        print("Data Recieved from client is:".format(msg))

        print(msg)  

        print("Thread Name:{}".format(threading.current_thread().name))

        packet_inspection.clear()

        packet_inspection["protocol"] = "TCP"
        packet_inspection["sent_from"] = self.client_address
        packet_inspection["data"] = msg

        tcp_idx = "{}:{}".format((len(message_board["TCP"]) +1), msg)

        message_board["TCP"][tcp_idx]=(self.__dict__)


def home(request):
    global listener_running

    if not listener_running:
        # Create a Server Instance
        tcp_server_instance = socketserver.ThreadingTCPServer(tcp_server, TCPHandler)

        # Make the server wait forever serving connections
        tcp_server_thread = threading.Thread(target=tcp_server_instance.serve_forever, daemon=True)
        tcp_server_thread.start()

        udp_server_thread = threading.Thread(target=udpSocketListener, daemon=True)
        udp_server_thread.start()

        listener_running = True

    response = ""

    if request.method == "POST":

        dest_ip = request.POST["dest_addr"]
        dest_port = request.POST["dest_port"]
        msg_data = request.POST["msg_data"]
        network_protocol = request.POST["protocol"]

        if "block" in request.POST:
            # https://gist.github.com/davydany/0ad377f6de3c70056d2bd0f1549e1017
            if dest_ip == "":
                response = "You need to set an IP address to block"
            else:
                if dest_port == "":
                    block_cmd = "iptables -A INPUT -p {} -s {} -j DROP".format(network_protocol,dest_ip)

                    response = "No port provided - All {} traffic from {} blocked".format(network_protocol.upper(), dest_ip)

                else:
                    block_cmd = "iptables -A INPUT -p {} -s {} --dport {} -j DROP".format(network_protocol, dest_ip, dest_port)

                    response = "{} Traffic from {} to {} blocked".format(network_protocol.upper(), dest_ip, dest_port)

                os.system(block_cmd)

                stream = os.popen("iptables -L INPUT")
                output = stream.read().strip().split("\n")

                last_rule_added_str = re.sub('\s+',' ',output[-1])
                
                response +="\n{}\n".format(last_rule_added_str)

        if "send" in request.POST:
            if dest_ip == "":
                response = "You need to set an IP address to send a message to"

            else: 

                if msg_data == "":
                    msg_data = "Hello There"

                if network_protocol == "tcp":
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                    sock.connect((dest_ip, int(dest_port)))

                    sock.send(msg_data.encode())

                    sock.close()

                if network_protocol == "udp":
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.sendto(msg_data.encode(), (dest_ip, int(dest_port)))
                
    context = {
        'response':response,
        'packet_data': packet_inspection
    }

    return render(request,'GUI/home.html', context)


def iptablesRulesView(request):

    if request.method == "POST":

        rule_to_remove = int(request.POST["iptables_rules"])

        print(rules_dict[rule_to_remove])

        remove_rule_cmd = "iptables -D INPUT {}".format(rule_to_remove)

        os.system(remove_rule_cmd)

        rules_dict.clear()

    idx = 1

    stream = os.popen("iptables -L INPUT")

    rules = stream.read().strip().split("\n")[2:]

    for rule in rules:
        rules_dict[idx] = rule
        idx += 1

    context = {
        'rules':rules_dict
    }

    return render(request,'GUI/iptablesRules.html', context)


def messageBoardView(request):
    global message_board

    tcp_message_to_inspect = ""

    udp_message_to_inspect = ""

    if request.method == "POST":

        if "tcp_message_to_inspect" in request.POST:

            tcp_message_to_inspect = message_board["TCP"][request.POST["tcp_message_to_inspect"]]

        if "udp_message_to_inspect" in request.POST:

            udp_message_to_inspect = message_board["UDP"][request.POST["udp_message_to_inspect"]]

    context = {
        "TCP_messages":message_board["TCP"],
        "UDP_messages":message_board["UDP"],
        "chosen_tcp_message":tcp_message_to_inspect,
        "chosen_udp_message":udp_message_to_inspect
    }

    return render(request,'GUI/messageBoard.html', context)


def udpSocketListener():

    # create udp socket
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind(udp_server)

    while True:
        data, client_addr  = udp_sock.recvfrom(2048)

        temp_dict = dict()

        temp_dict["Data"] = data
        temp_dict["Client Address"] = client_addr

        udp_idx = "{}:{}".format((len(message_board["UDP"]) +1), data)

        message_board["UDP"][udp_idx]=temp_dict

        packet_inspection.clear()

        packet_inspection["protocol"] = "UDP"
        packet_inspection["sent_from"] = client_addr
        packet_inspection["data"] = data
        
        print(data)
        print(client_addr)
        