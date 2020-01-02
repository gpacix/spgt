import sys

# Call with sys.argv[1:]
def parse(args, values):
    while args:
        arg = args[0]
        args = args[1:]
        if arg in ['-v', '-vv', '-vvv', '-vvvv']:
            values['VERBOSITY'] = len(arg) - 1
        elif ':' in arg:  # 'localhost:8192'
            host, port = arg.split(':')
            if host:
                values['HOST'] = host
            if port:
                values['PORT'] = int(port)
        elif arg == '--scale':
            values['SCALE'] = int(args[0])
            args = args[1:]
        elif arg == '--size':
            values['SIZE'] = int(args[0])
            args = args[1:]
        else:
            print("Unknown argument or option: '%s'" % arg)
            sys.exit(1)
    return values
