from os import fdopen
import random
import threading
import time
import hashlib  # MD5
import socket
from datetime import datetime
import sys

NODE = 7
TIMESLOT = 60
TIMEGENERATE = 10

log = True  # Check to print log on screen
index = 0   # index for next generate Transaction
infos = []  # Add, Port: Handler + All nodes

# Đọc thông tin từ file config
def loadConfig():
    f = open('config', 'r')
    infos = f.readlines()

    f.close()
    return infos

# Chuyển IP Port --> [IP, Port]
def convertAddr(info:str):
    return info.strip().split('\t')

# Chọn node proposer
def chooseProposer(infos: list):
    while True:
        proposer = random.randint(1, NODE)
        
        # broadcast
        for info in infos[1:]:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                host, port = convertAddr(info)
                try:
                    s.connect((host, int(port)))
                    s.send("Proposer: {0}".format(proposer).encode("utf-8"))
                except Exception as e:
                    if log:
                        print("    [-] DEBUG: Send proposer to {0}:{1} failed: {2}".format(host, port, e))

        timeObj = datetime.now().time()
        if log:
            print("    [+] Proposer: NodeID=" + str(proposer) + " at " + timeObj.strftime("[%H:%M:%S]"))
        time.sleep(TIMESLOT)

# Phát sinh ngẫu nhiên transaction
def generateTransaction(infos: list):
    global index
    #index = 0 # index for transaction
    while True:
        accounts = ["Alice", "Bob", "Cein", "Dio", "Eve"]
        random.shuffle(accounts)
        sender, receiver = accounts[0], accounts[1]
        amount = random.randint(1, 50)
        id = index
        index = index + 1

        # Create hash transaction
        message = sender + receiver + str(amount) + str(id)
        TxHash = hashlib.md5(message.encode()).hexdigest()

        # broadcast
        for info in infos[1:]:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                host, port = convertAddr(info)
                try:
                    s.connect((host, int(port)))
                    s.send(("Transaction: {0} {1} {2} {3} {4}".format(sender, receiver, amount, id, TxHash)).encode("utf-8"))
                except:
                    if log:
                        print("    [-] DEBUG: Send transaction to {0}:{1} failed".format(host, port))

        if log:
            print("    [+] Transaction: ID=" + str(id) + " generated with hash " + TxHash)
        time.sleep(TIMEGENERATE)

if __name__ == '__main__':
    print("[>] Starting server .....")
    # Load config
    infos = loadConfig()

    x = threading.Thread(target = chooseProposer, args=[infos], daemon= True)
    x.start()

    x = threading.Thread(target = generateTransaction, args=[infos], daemon= True)
    x.start()

    # Stop server: Ctrl C and verify
    while True:
        try:
            input('')
        except KeyboardInterrupt:
            log = False
            res = input("[>] Do you really want to exit (Y/N)? ")
            if res == 'y' or res == "Y":
                print('[>] Server stopped!!!')
                input('')
                sys.exit()
                
            else:
                print('[>] Server continue...')
                log = True