import sys

def parse(file):
    d = dict()
    fp = open(file, 'r')
    for line in fp:
        if line[0] == '#':
            continue
        tmp = line.split()
        if len(tmp) != 3 or tmp[1] != '=':
            print 'error:', line
            sys.exit()
        d[tmp[0]] = tmp[2]
    fp.close()
    return d
