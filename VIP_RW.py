import os
import sys
import glob
from VIPNTRecord import *

#   Read files as specified by glob in sys.argv[1]
#   Write to directory as specified by path in sys.argv[2]
#
#   For each file, start records at 1
#
FLAGMASK_FIRST = 1
FLAGMASK_LAST = 2
def flag_lastfirst(collection):
    flag = FLAGMASK_FIRST
    first = True
    index = 1
    for element in collection:
        if not first:
            yield index, flag, current
            index += 1
            flag = 0
        current = element
        first = False
    
    flag = FLAGMASK_LAST
    yield index-1,flag, current


def ReadDelim(f, delim, blocksize=2048):
    end = ''
    FIRST = True
    while 1:
        block = f.read(blocksize)
        if not block:
            if len(end)<>0 :
                yield end
            #EOF Reached
            break
        parts = block.split(delim)
        if FIRST:
            FIRST = False
            if parts[0] == "" and len(parts)>1:
                parts = parts[1:]
        if len(parts) == 1:
            end += parts[0]
        else:
            yield end + parts[0]
            for p in parts[1:-1]:
                yield p
            end = parts[-1]
    #yield end

def ReadVIPNT (name):
    file_RAW = name
    raw = open(file_RAW)
    idx = 0
    print "Processing:",
    for idx,status,line in flag_lastfirst(ReadDelim(raw,Record.RS[0])):
        try:
            book = Record(line,0,False)
        except:
            print idx,status,line
            sys.exit()
        if  idx%1000 == 0:
            print ".",
        yield book,status
    print "Record %s processed"  % str(idx+1)
    raw.close()



    
def WriteVIP(data,filename):
    rec=0
    qcout = open(filename,'w')
    for book,status in ReadVIPNT(data):
        rec +=1
        book.control.updaterecordnum(rec)
        book.control.ensureseg5(" ")
        newbook = book.output()
        qcout.write(newbook)
        
    qcout.close()


            
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "Read and write  VIPNT files.  Record number is updated to start at 1 for each file"
        print "Usage: VIP_RW.py sourceglob destpath "
        print "    VIP_RW.py *.DAT .\Fred "
        sys.exit()
        
    allfiles = glob.glob(sys.argv[1])


    for f in allfiles:
        print f
        path,base = os.path.split(f)
        outf = sys.argv[2] + "\\" + base
        WriteVIP(f,outf)