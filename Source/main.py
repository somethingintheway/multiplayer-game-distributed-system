from subprocess import Popen, CREATE_NEW_CONSOLE

def f(name):
    print('hello', name)
    input("Hello")

if __name__ == '__main__':
    # run node
    Popen("python node.py 1", creationflags=CREATE_NEW_CONSOLE)
    Popen("python node.py 2", creationflags=CREATE_NEW_CONSOLE)
    Popen("python node.py 3", creationflags=CREATE_NEW_CONSOLE)
    Popen("python node.py 4", creationflags=CREATE_NEW_CONSOLE)
    Popen("python node.py 5", creationflags=CREATE_NEW_CONSOLE)

    # Byzantine
    Popen("python node.py 6", creationflags=CREATE_NEW_CONSOLE)
    Popen("python node.py 7", creationflags=CREATE_NEW_CONSOLE)

    # run server
    Popen("python handler.py", creationflags=CREATE_NEW_CONSOLE)

    