import hashlib  # MD5
import socket
from datetime import datetime
import sys
import threading
import timeit
import copy

NODE = 7
ETA_ACCEPT = 5
TIMESLOT = 60
NODESHOWBC = 1
MAX_TRANSACTION = 5
GENESIS_BLOCK_HASH = '18120168_18120xxx'

# Khai báo danh sách transaction
poolTransactions = []
NodeID = -1             # ID for current node
infos = []              # Add, Port: Handler + All nodes
ProposerID = -1         # ID for node proposer
log = True
isMined = False         # Is mining block
proposeBlock = None

stopEvent = None       
accounts =  {
        "Alice": 100,
        "Bob": 100,
        "Cein": 100,
        "Dio": 100,
        "Eve": 100
    }
BlockChainNode = None
voted = []
timeStartMining = None
isBroadcast = False
# use for NodeID=1 log New Block
isNewBlock = False
votedLog = ""

class BlockChain:
    def __init__(self):
        self.lastHash = GENESIS_BLOCK_HASH
        self.blk = []
        self.height = 0

    #def __hash__(self) -> str:
    #    return self.lastHash
    
    def update(self, block):
        self.lastHash = block.getHash()
        self.blk.append(block)
        self.height = block.getHeight()

    def getLastHash(self) -> str:
        return self.lastHash

    def getHeight(self) -> int:
        return self.height

    def lastBlock(self):
        return self.blk[-1]        

class Block:
    def __init__(self, txs, prevHash=None, ID=None, height=None):
        if type(txs) == list:
            self.prevHash = prevHash
            self.txs = txs
            self.ID = ID
            self.height = height
            
        elif type(txs) == str:
            self.txs = []
            temp = txs.split(",")
            self.prevHash = temp[0]
            self.ID = int(temp[1])
            self.height = int(temp[2])
            for t in temp[3:]:
                self.txs.append(Transaction("", "", 0, 0, "", t))
            
    # str(Block): prevHash,ID,height,Tx1,Tx2,...
    def __str__(self) -> str:
        result = self.prevHash + "," + str(self.ID) + "," + str(self.height) # {0}".format(len(self.txs))
        for tx in self.txs:
            result = result + "," + str(tx)
        return result

    def getHash(self) -> str:
        return hashlib.md5(str(self).encode()).hexdigest()

    def owner(self) -> int:
        return self.ID

    def getHeight(self) -> int:
        return self.height

    def getPrevHash(self) -> str:
        return self.prevHash

    def verifyBlock(self, poolTxs: list, Accs)->bool:
        global BlockChainNode
        if NodeID != NODESHOWBC and log:
            print("    [-] DEBUG: Verify 1...")
        if self.prevHash != BlockChainNode.getLastHash() or len(self.txs) > MAX_TRANSACTION or self.height != BlockChainNode.height + 1:
            return False

        # Verify Transaction (Exist, Valid)
        if NodeID != NODESHOWBC and log:
            print("    [-] DEBUG: Verify 2...")
        for tx in self.txs:
            if NodeID != NODESHOWBC and log:
                print("    [-] DEBUG: Verify 3...")
            if not tx in poolTxs:
                return False
                
            if tx.verifyTransaction(Accs):
                poolTxs.remove(tx)
                # Update acs
                tx.updateBalance(Accs)
            else:
                return False

        return True

class Transaction:
    def __init__(
        self,
        TxStr="",
        sender="", 
        receiver="", 
        amount=0, 
        id=0,
        TxHash="" ):
        if TxStr == "":
            self.sender = sender
            self.receiver = receiver
            self.amount = amount
            self.id = id
            self.TxHash = TxHash
        else:
            temp = TxStr.split(" ")
            self.sender = temp[0]
            self.receiver = temp[1]
            self.amount = int(temp[2])
            self.id = int(temp[3])
            self.TxHash = temp[4]

    def __str__(self) -> str:
        return "{0} {1} {2} {3} {4}".format(self.sender, self.receiver, self.amount, self.id, self.TxHash)

    def __eq__(self, __o: object) -> bool:
        return self.TxHash == __o.TxHash and self.id != __o.id 

    def getHash(self) -> str:
        message = self.sender + self.receiver + str(self.amount) + str(self.id)
        return hashlib.md5(message.encode()).hexdigest()

    def __copy__(self):
        return Transaction("", self.sender, self.receiver, self.amount, self.id, self.TxHash)

    def getID(self) -> int:
        return self.id

    # Kiểm tra tính toàn vẹn giao dịch và số dư hợp lệ
    def verifyTransaction(self, Accounts):
        # Check hash
        if self.TxHash != self.getHash() or Accounts[self.sender] < self.amount:
            return False
        
        return True

    # Cập nhạt số dư
    def updateBalance(self, Accounts):
        Accounts[self.sender] = Accounts[self.sender] - self.amount
        Accounts[self.receiver] = Accounts[self.receiver] + self.amount

# Đọc thông tin từ file config
def loadConfig():
    f = open('config', 'r')
    infos = f.readlines()

    f.close()
    return infos

# Chuyển IP Port --> [IP, Port]
def convertAddr(info:str):
    return info.strip().split('\t')

# Dùng để nhận event (Proposer, Transaction, CreateBlock, AcceptBlock, UpdateBlock)
def listenEvent(infos: list):
    global isNewBlock, log, NodeID, ProposerID, poolTransactions, isMined, stopEvent, BlockChainNode, voted, timeStartMining, isBroadcast, proposeBlock

    host, port = convertAddr(infos[NodeID])
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, int(port)))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.listen(NODE * 3)
        while True:
            conn, addr = s.accept()
            with conn:
                while True:
                    data = conn.recv(1024).decode("utf-8")
                    if not data:
                        break
                    elif NodeID != NODESHOWBC and log:
                        print("    [-] Debug: " + data)
                        
                        # Receive notification about proposer
                        if "Proposer" in data:
                            # Log NewBlock in NodeID=1
                            if isNewBlock and NodeID == NODESHOWBC:
                                b = BlockChainNode.getLastBlock()

                                balanceStr = ""
                                for user in accounts:
                                    balanceStr += ", ({0}: {1})".format(user, accounts[user])
                                balanceStr = balanceStr[2:]

                                txsStr = ""
                                for txStr in str(b).split(",")[3:]:
                                    txsStr += "        ({0})".format(txStr)
                                
                                print("[>] Block {0} created".format(b.getHeight()))
                                print("    [+] PrevHash: {0}", b.getPrevHash())
                                print("    [+] Balance: {0}".format(balanceStr))
                                print("    [+] Miner: NodeID={}".format(b.owner()))
                                print("    [+] {0}".format(votedLog))
                                if txsStr != "":
                                    print("    [+] Transaction:")
                                    print("{0}".format(txsStr))
                                else:
                                    print("    [+] No trasaction")

                                isNewBlock = False
                                votedLog = ""

                            # Update info ProposerID
                            ProposerID = int(data.split(" ")[1])
                            timeObj = datetime.now().time()
                            if log and NodeID != NODESHOWBC:
                                print("    [+] Proposer: NodeID=" + str(ProposerID) + " at " + timeObj.strftime("[%H:%M:%S]"))

                            # stop mining
                            if isMined:
                                stopEvent.set()
                                stopEvent.clear()
                                proposeBlock = None
                                isMined = False
                                voted = []
                                isBroadcast = False

                            # Start mining
                            if NodeID == ProposerID:
                                isMined = True
                                timeStartMining = timeit.default_timer()
                                stopEvent = threading.Event()
                                p = threading.Thread(target = miningBlock, args=[infos], daemon= True)
                                p.start()

                        elif "Transaction" in data:
                            sender, receiver, amount, id, TxHash = data.split(" ")[1:]
                            temp = Transaction("", sender, receiver, int(amount), int(id), TxHash)
                            poolTransactions.append(temp)
                            if log and NodeID != NODESHOWBC:
                                print("    [+] Transaction: ID={0} received".format(id))

                        # Check and verify block: CreateBlock:str(block)
                        elif "CreateBlock" in data:
                            p = threading.Thread(target = verify, args=[data.split(":")[1]], daemon= True)
                            p.start()

                        elif "AcceptBlock" in data:
                            # Revoke mining
                            if timeit.default_timer() - timeStartMining > TIMESLOT:
                                stopEvent.set()
                                stopEvent.clear()
                                isMined = False
                                voted = []
                                continue

                            temp = int(data.split(":")[1])
                            if temp not in voted:
                                voted.append(temp)

                            if len(voted) >= ETA_ACCEPT:
                                # Send only to NodeID=1 to log new voted
                                #sendVotedList()
                                p = threading.Thread(target = sendVotedList, args=[], daemon= True)
                                p.start()

                                # Broadcast to other node
                                if not isBroadcast:
                                    #updateBlock()
                                    q = threading.Thread(target = updateBlock, args=[], daemon= True)
                                    q.start()
                                    isBroadcast = True

                        elif "UpdateBlock" in data:
                            p = threading.Thread(target = updateBlockChain, args=[data.split(":")[1]], daemon= True)
                            p.start()
                            #updateBlockChain(data.split(":")[1])

                        # Only for NodeID=1
                        elif "Voted" in data and NodeID == NODESHOWBC: 
                            isNewBlock = True
                            votedLog = data

# Send list voted to NODESHOWBC
def sendVotedList():
    global voted, log, infos, NodeID, isNewBlock, votedLog
    votedStr = ""
    for i in voted:
        votedStr += ", {0}".format(i)
    votedStr = votedStr[2:]

    msg = "Voted: {0}/{1} (NodeID: {2})".format(len(voted), NODE, votedStr)

    if NodeID == NODESHOWBC:
        isNewBlock = True
        votedLog = msg
        return

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        host, port = convertAddr(infos[NODESHOWBC])
        try:
            s.connect((host, int(port)))
            s.send(msg.encode("utf-8"))
        except Exception as e:
            if log:
                print("    [-] DEBUG: Send Voted to {0}:{1} failed: {2}".format(host, port, e))

# Tạo block và broadcast
def miningBlock(infos: list):
    global NodeID, stopEvent, accounts, poolTransactions, BlockChainNode, proposeBlock, log
    if NodeID != NODESHOWBC and log:
        print("    [>] NodeID={0} start mining".format(NodeID))

    txs = []
    if stopEvent.is_set():
        if NodeID != NODESHOWBC and log:
            print("    [>] NodeID={0} stop mining".format(NodeID))
        return

    accs = accounts.copy()
    poolTxs = poolTransactions.copy()
    for tx in poolTxs:
        if tx.verifyTransaction(accs):
            txs.append(tx)
            # Update acs
            tx.updateBalance(accs)

            if len(txs) == MAX_TRANSACTION:
                break
    
    # Create Block
    if NodeID != NODESHOWBC and log:
        print("    [-] Num transactions Accepted: " + str(len(txs)))
    if stopEvent.is_set():
        if NodeID != NODESHOWBC and log:
            print("    [>] NodeID={0} stop mining".format(NodeID))
        return
    proposeBlock = Block(txs, BlockChainNode.getLastHash(), NodeID, BlockChainNode.getHeight() + 1)
    mess = "CreateBlock:{0}".format(str(proposeBlock))

    # Broadcast block
    if stopEvent.is_set():
        if NodeID != NODESHOWBC and log:
            print("    [>] NodeID={0} stop mining".format(NodeID))
        return
    for info in infos[1:NodeID] + infos[NodeID + 1:]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            host, port = convertAddr(info)
            try:
                s.connect((host, int(port)))
                s.send(mess.encode("utf-8"))
            except Exception as e:
                if NodeID != NODESHOWBC and log:
                    print("    [-] DEBUG: Send CreateBlock to {0}:{1} failed: {2}".format(host, port, e))

    if NodeID != NODESHOWBC and log:
        print("    [>] NodeID={0} stop mining".format(NodeID))

# Verify block
def verify(block: str):
    global poolTransactions, accounts

    b = Block(block)
    
    if b.verifyBlock(poolTransactions.copy(), accounts.copy()):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            host, port = convertAddr(infos[b.owner()])
            try:
                s.connect((host, int(port)))
                msg = "AcceptBlock:{0}".format(NodeID)
                s.send(msg.encode("utf-8"))
            except Exception as e:
                if log:
                    print("    [-] DEBUG: Response AcceptBlock to {0}:{1} failed: {2}".format(host, port, e))

# Send Event updateBlock and update BlockChain
def updateBlock():
    global BlockChainNode, proposeBlock

    message = "UpdateBlock:{0}".format(str(proposeBlock))
    updateBlockChain(str(proposeBlock))

    # Broadcast block
    for info in infos[1:NodeID] + infos[NodeID + 1:]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            host, port = convertAddr(info)
            try:
                s.connect((host, int(port)))
                s.send(message.encode("utf-8"))
            except Exception as e:
                if log and NodeID != NODESHOWBC:
                    print("    [-] DEBUG: Send UpdateBlock to {0}:{1} failed: {2}".format(host, port, e))

# Add block, update Balance 
def updateBlockChain(blkStr: str):
    global BlockChainNode, accounts, poolTransactions, log, NodeID
    
    b = Block(blkStr)
    BlockChainNode.update(b)

    for txStr in blkStr.split(",")[3:]:
        tx = Transaction(TxStr= txStr)
        tx.updateBalance(accounts)

        try: 
            poolTransactions.remove(tx)
        except:
            pass

    # only NodeId=1 show BlockChain, others show log
    if log and NodeID != NODESHOWBC:
        print("[>] Block {0} was added".format(b.height))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python node.py <id>")
        sys.exit()
    
    NodeID = int(sys.argv[1])
    print("[>] NodeId={0} running".format(NodeID))

    # Load config
    infos = loadConfig()
    BlockChainNode = BlockChain()
    # Print genesis block
    if NodeID == NODESHOWBC:
        balanceStr = ""
        for user in accounts:
            balanceStr += ", ({0}: {1})".format(user, accounts[user])
        balanceStr = balanceStr[2:]

        print("[>] Block GENESIS 0: " + GENESIS_BLOCK_HASH)
        print("    [+] Balance: {0}".format(balanceStr))

    # Thread nhận event
    x = threading.Thread(target = listenEvent, args=[infos], daemon= True)
    x.start()

    # Stop node: Ctrl C and verify
    while True:
        try:
            input('')
        except KeyboardInterrupt:
            log = False
            res = input("[>] Do you really want to exit (Y/N)? ")
            if res == 'y' or res == "Y":
                print('[>] NodeID={0} stopped'.format(NodeID))
                input('')
                sys.exit()
                
            else:
                print('[>] NodeID={0} continue ...'.format(NodeID))
                log = True