from os import fdopen
import random
import threading
import time

NODE = 7
TIMESLOT = 60
TIMEGENERATE = 10

# Biến toàn cục, index cho transaction
index = 0   

# Đọc thông tin từ file config
def loadConfig():
    f = open('config', 'r')
    infos = f.readlines()

    f.close()
    return infos

# Chuyển IP Port --> IP, Port
def convertAddr(info:str):
    return info.strip().split('\t')

# Chọn node proposer
def chooseProposer(infos):
    while True:
        proposer = random.randint(1, NODE)
        
        # broadcast

        print(proposer)
        time.sleep(TIMESLOT)

# Phát sinh ngẫu nhiên transaction
def generateTransaction(infos):
    while True:
        accounts =  ["Alice", "Bob", "Cein", "Dio", "Eve"]
        random.shuffle(accounts)
        sender, receiver = accounts[0], accounts[1]
        amount = random.randint(1, 50)
        TxHash = ''
        id = index
        index = index + 1

        # broadcast


        print(sender, receiver, amount, TxHash, id)
        time.sleep(TIMEGENERATE)

if __name__ == '__main__':
    
    # Load config
    infos = loadConfig()
    print(convertAddr(infos[0]))


    x = threading.Thread(target = chooseProposer)
    x.start()

    x = threading.Thread(target = generateTransaction)
    x.start()

