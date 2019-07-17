import sys

# Call with sys.argv[1:]
def parse(args):
    VERBOSITY = 0
    HOST, PORT = "localhost", 9999
    while args:
        arg = args[0]
        args = args[1:]
        if arg in ['-v', '-vv', '-vvv', '-vvvv']:
            VERBOSITY = len(arg) - 1
        elif ':' in arg:  # 'localhost:8192'
            host, port = arg.split(':')
            if host:
                HOST = host
            if port:
                PORT = int(port)
        else:
            print("Unknown argument or option: '%s'" % arg)
            sys.exit(1)
    return VERBOSITY, HOST, PORT
