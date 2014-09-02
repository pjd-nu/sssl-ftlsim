import sys, re

class parse:
    def __init__(self, file):
        fp = open(file, 'r')
        for line in fp:
            if line[0] == '#' or line[0] == '\n':
                continue
            tmp = line.split()
            if len(tmp) != 3 or tmp[1] != '=':
                print 'error:', line
                sys.exit()
            name,_,val = tmp
            if val.isdigit():
                val = int(tmp[2])
            elif re.match('[0-9]+\.[0-9]*', val):
                val = float(tmp[2])
            setattr(self, tmp[0], val)
        fp.close()

    def has(self, name):
        return hasattr(self, name)
