class Node:
    def __int__(self):
        pass

    def createBlock():
        pass
    pass

class Block:
    def __init__(self, txs):
        pass

class Transaction:
    def __init__(
        self,
        sender: int, 
        receiver: int, 
        amount: int, 
        TxHash
    ):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.TxHash = TxHash

    def verifyTransaction(self):
        # Check hash
        if self.TxHash != '':
            return False

        return True



if __name__ == '__main__':
    accounts =  {
        "Alice": 100,
        "Bob": 100,
        "Cein": 100,
        "Dio": 100,
        "Eve": 100
    }

    # Khai báo danh sách transaction

    # Thread nhận Transaction

    # Thread để nhận sự kiện proposer

    # Thread xác nhận các block