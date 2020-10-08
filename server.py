import random
import socket
import time
from _thread import *
import threading
from datetime import datetime
import json

clients_lock = threading.Lock()
connected = 0

packetPerSecond = 1
colorChangeCountdown = 0

clients = {}

def connectionLoop(sock):
   while True:
      data, addr = sock.recvfrom(1024)
      data = str(data)
      #print (data)
      data = data[ 2 : len(data)-1]
      #print (data)
      data = json.loads(data)
      #print (data)
      if addr in clients:
         if 'heartbeat' in data['cmd']:
            clients[addr]['lastBeat'] = datetime.now()
         if 'updatePosition' in data['cmd']:
            #print (data)
            clients[addr]["position"]['X'] = data['x']
            clients[addr]["position"]['Y'] = data['y']
            clients[addr]["position"]['Z'] = data['z']
      else:
         if 'connect' in data['cmd']:
            print (data)
            clients[addr] = {}
            clients[addr]['lastBeat'] = datetime.now()
            clients[addr]['color'] = 0
            clients[addr]['position'] = {'X':0,'Y':0, 'Z': 0.0}
            message = {"cmd": 3,"id":str(addr)}
            m = json.dumps(message)
            sock.sendto(bytes(m,'utf8'), (addr[0],addr[1]))
            message2 = {"cmd": 0,"id":str(addr)}
            m2 = json.dumps(message2)
            for c in clients:
               sock.sendto(bytes(m2,'utf8'), (c[0],c[1]))
         if 'heartbeat' in data['cmd']:
            clients[addr] = {}
            clients[addr]['lastBeat'] = datetime.now()
            clients[addr]['color'] = 0
            clients[addr]['position'] = {'X':0,'Y':0, 'Z': 0.0}
            message = {"cmd": 0,"id":str(addr)}
            m = json.dumps(message)
            for c in clients:
               sock.sendto(bytes(m,'utf8'), (c[0],c[1]))

def cleanClients(sock):
   while True:
      for c in list(clients.keys()):
         if (datetime.now() - clients[c]['lastBeat']).total_seconds() > 5:
            print('Dropped Client: ', c)
            clients_lock.acquire()
            message = {"cmd": 2,"id":str(c)}
            m = json.dumps(message)
            for client in clients:
               print(m)
               sock.sendto(bytes(m,'utf8'), (client[0],client[1]))
            del clients[c]
            clients_lock.release()
      time.sleep(1)

def gameLoop(sock):
   while True:
      global colorChangeCountdown
      global packetPerSecond

      GameState = {"cmd": 1, "players": []}
      clients_lock.acquire()
      print (clients)
      for c in clients:
         player = {}
         if colorChangeCountdown == 0:
            clients[c]['color'] = {"R": random.random(), "G": random.random(), "B": random.random()}
         player['id'] = str(c)
         player['color'] = clients[c]['color']
         player['position'] = clients[c]['position']
         GameState['players'].append(player)
      s=json.dumps(GameState)
      #print(s)
      for c in clients:
         sock.sendto(bytes(s,'utf8'), (c[0],c[1]))
      clients_lock.release()
      colorChangeCountdown = (colorChangeCountdown + 1) % packetPerSecond
      time.sleep(1.0/packetPerSecond)

def main():
   port = 12345
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.bind(('', port))
   start_new_thread(gameLoop, (s,))
   start_new_thread(connectionLoop, (s,))
   start_new_thread(cleanClients,(s,))
   while True:
      time.sleep(1)

if __name__ == '__main__':
   main()
