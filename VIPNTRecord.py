#!/usr/bin/env python
#VIPNT RECORD.py
#Written by Bruce Bromberek  (bruce.bromberek@gmail.com)
# Version 1.0
#
#Change Log:
#v1.0 1/31/06
#Released working base class and helper classes for working with VIPNT files
import re

class Record:
    # Class object to access and manipulate VIP-NT Production Records.
    # Based on information supplied in VIDEOJET VIP_NT Data Format Specifications Manual, P/N 365884-01 Rev AA 10/98
    #
    #Control Code Delimiters
    RS = ["\x1E","^RS"] #control characters by default but text strings are legal
    GS = ["\x1D","^GS"]
    US = ["\x1F","^US"]

    def __init__(self,line,a = 0,PROCESS_TEXTLINES = True):
        #Split an entire line into control and text portions.  See VIPNT Data format specifications.
        #First GS (either ^GS or \x1D) marks the start of the Text line. Variable a is used as a flag for ascii text or control codes
        #Valid line must have control segments and text segments
        (self.control, self.textarea) = ("","")
        self.PROCESS_TEXTLINES = PROCESS_TEXTLINES
        try:
            (self.control, self.textarea) = line.split(Record.GS[a],1) #this consumes the first GS
        except Exception:
            raise VIPNT_TextSegment("Missing Text Line")
            return
        self.control  = ControlSegment(self,self.control,a)
        self.textarea = "%s%s" % (Record.GS[a],self.textarea)# Consumed GS is restored
        if PROCESS_TEXTLINES:
            self.textarea = TextSegment(self,self.textarea,a)
        
    def processtextlines(self,a):
        self.textarea = TextSegment(self,self.textarea,a)
        self.PROCESS_TEXTLINES = True
        
    def getsacknum(self,start=0,stop=0,split=False,spliton="/",seg=0,skip=1):    
        num = self.textarea[start:stop]
        if split:
            s = self.textarea[start:stop].split(spliton)[seg].strip()[skip:]
            return s
        else:
            return num
        
    def output(self,a=0):
        controlline = self.control.output(a)
        if self.PROCESS_TEXTLINES:
            textline = self.textarea.output(a)
        else:
            textline = self.textarea
        return "%s%s%s" % (Record.RS[a],controlline,textline)

class TextSegment:
    def __init__(self,parent,line,a):
        self.parent        = parent
        self.text          = line.split(Record.US[a])
        self.NumTextSeg    = len(self.text)
        # Check for 20 max segments
        if self.NumTextSeg > 20:
            raise VIPNT_TextSegment("More than 20 text segments")
        # Check for 720 lines maximum
        if line.count(Record.GS[a]) > 720:
            raise VIPNT_TextSegment("More than 720 text lines combined")

        for i in range(self.NumTextSeg):
            # Check for 144 lines max per segment
            if self.text[i].count(Record.GS[a]) > 144:
                raise VIPNT_TextSegment("More than 144 text lines in one segment")
            self.text[i] = TextMessage(self.text[i],a)
            # Check for 500 characters text length
    def float(self,location):
        for i in range(self.NumTextSeg):
            self.text[i].float(location)
            
    def output(self,a):
        t = []
        for i in range(self.NumTextSeg):
            t.append(self.text[i].output(a))
        return Record.US[a].join(t)
    def outputTAB(self,a):
        t = []
        for i in range(self.NumTextSeg):
            t.append(self.text[i].outputTAB(a))
        return "\t".join(t)

class TextMessage:
    def __init__(self,line,a=0):    
        #Remove leading blank line
        self.lines = line.split(Record.GS[a])
        #Remove leading blank line caused by 1st GS.  Split assumes that delims are between sections only so causes first line to be blank
        self.lines.pop(0)
        #Check for eight lines and pad as necessary
    def output(self,a=0):
        lines = self.lines
        output = Record.GS[a].join(lines)
        return "%s%s" % (Record.GS[a],output)
    def outputTAB(self,a=0):
        lines = self.lines
        output = "\t".join(lines)
        return output
    def float(self, Location):
        blank = [""]
        size  = len(self.lines)
        if Location == "TOP":
            self.lines = self.lines + blank*size
        else:
            self.lines = blank*size+self.lines

    def parseline3(self):
        #split info line to pool, pallet, etc.  Customer issue date may contain spaces
        #hence the need to get at it by walking in from the ends
        dataline     = self.lines[2].split()
        self.pool    = dataline.pop(0)
        self.pubcode = dataline.pop(0)
        self.bundleID= dataline.pop()
        self.palletID= dataline.pop()
        #remove #
        self.bundleID= self.bundleID[1:]
        self.palletID= self.palletID[1:]
        self.makeup  = dataline.pop()
        self.issue   = " ".join(dataline)
        
class ControlSegment:
    def __init__(self,parent,line,a=0):
        self.parent = parent
        #Start of control segment must be '2P'
        self.control       = line.split(Record.US[a])
        #Max of 8 control segments, min of 
        self.NumControlSeg = len(self.control)        
        if self.NumControlSeg <1 or self.NumControlSeg >8 :
            raise VIPNT_InvalidControlSegments("Incorrect Number of Segments")
            return            
        segments = ("Seg1","Seg2","Seg3","Seg4","Seg5","Seg6","Seg7","Seg8")
        for i,type in enumerate(segments):
            if i >= self.NumControlSeg:
                self.control.append(None)
            else:
                self.ControlSegment(self.control[i],type)
                
    def ControlSegment(self,segment,type):
        #get ID, sortcode,zipcode,quality,message, signature, version, makeup,aux device
        if   type == "Seg1":
            #length is 11
            #begins with 2p
            #ninedigit number with padded zeros
            self.RecordNum = int(segment[2:])
        elif type == "Seg2":
            #sort level 0,1,2,3,4
            #consolidated levl 0,3,5
            #zip code 12 car  numbers then space
            self.sortcode   = segment[0:1]
            self.consolidate = segment[1:2]
            self.zip         = segment[2:]
        elif type == "Seg3":
            #pallet it, 6 numbers 0 default
            self.palletID = segment 
        elif type == "Seg4":
            #Makeup Name, 12 cars ' ' default left justified
            self.versionID = segment.strip()
        elif type == "Seg5":
            #quality control Q or ' '
            self.QC = segment
        elif type == "Seg6":
            #signature map 100 charcaters 0 or 1
            self.sigmap = segment
        elif type == "Seg7":
            # Message indicators, 8 sets of 3 digits
            self.messages = []
            for i in range(8):
                self.message.append(segment[i*3:i*3+3])            
        elif type == "Seg8":
            self.aux_device_control = segment
            #max length 64
            #zeros or 1's only
            
    def output(self,a=0):
        return Record.US[a].join(self.control[:self.NumControlSeg])

    def updaterecordnum(self,id):
        self.RecordNum    = int(id)
        self.control[0]   = "2P%09d" % (int(id))
    def updatesortcode(self,code):
        if int(code) in [0,1,2,3,4]:
            self.sortcode     = code
            self.control[1]   = "%s%s" % (code,self.control[1][1:])
    def updateconsolidatecode(self,code):
        if int(code) in [0,3,5]:
            self.consolidate  = code
            self.control[1]   = "%s%s%s" % (self.control[1][0:1],code,self.control[1][2:])
    def updatepalletid(self,id):
        self.palletID = "%06d" % int(id)
        self.control[2] = self.palletID
    def updateversionid(self,id):
        self.versionID = id
        self.control[3] = "%-12s" % id
    def ensureseg5(self,status):
        if self.NumControlSeg==4:
            self.control[4] = status
            self.NumControlSeg+=1
    def updateQCstatus(self,id):
        if id=="Q":
            self.QC = "Q"
        else:
            self.QC = " "
        self.control[4] = self.QC

class VIPNTFileError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
class VIPNT_ProductionRecordError(VIPNTFileError):
    pass
class VIPNT_InvalidControlSegments(VIPNTFileError):
    pass
class VIPNT_TextSegment(VIPNTFileError):
    pass

#Simple routine to read DAT files in chunks with nonstandard delimiters
def ReadDelim(f, delim, blocksize=2048):
    end = ''
    while 1:
        block = f.read(blocksize)
        if not block:
            yield "^EOF"
            break
        parts = block.split(delim)
        if len(parts) == 1:
            end += parts[0]
        else:
            yield end + parts[0]
            for p in parts[1:-1]:
                yield p
            end = parts[-1]
    yield end
    
if __name__ == "__main__":
    #Run Test Cases
    print "Running Test Cases......."
    #Test input Parse and output
    testline  = "\x1E2P000000001\x1F00986642836   \x1F000000\x1F0002        \x1F \x1D#BXNGMLS *********CAR-RT LOT**C-026\x1D#0894000064221822# FEB07\x1DDE2 BLIF1SZ JAN06 0002        #1 #1\x1DBRUCE BROMBEREK              ^ISC^X\x1D8900 SE HILLCREST DR\x1DVANCOUVER WA  98664-2836\x1D\x1DBECDECBCEDCDECDBCDCBCBCDEE\x1F\x1D@nd Message\x1D\x1D\x1D\x1D\x1D\x1D\x1DLine 8"
    testlineA = "^RS2P000000001^US00986642836   ^US000000^US0002        ^US ^GS#BXNGMLS *********CAR-RT LOT**C-026^GS#0894000064221822# FEB07^GSDE2 BLIF1SZ JAN06 0002        #1 #1^GSBRUCE BROMBEREK              ^ISC^X^GS8900 SE HILLCREST DR^GSVANCOUVER WA  98664-2836^GS^GSBECDECBCEDCDECDBCDCBCBCDEE^US^GS@nd Message^GS^GS^GS^GS^GS^GS^GSLine 8"
    Test = Record(testline[1:])
    print "%s%s%s" % ("Version:",Test.control.versionID,"##")
    if testline == Test.output():
        print "Round Trip     - OK"
    else:
        print "Round Trip Test Failed"
        print Test.output()
        print testline
    #Same test but with ASCII input
    Test = Record(testlineA[3:],1)
    if testlineA == Test.output(1):
        print "ASCII input    - OK"
    else:
        print Test.output(1)
        print testlineA
    #Same test but with ASCII output
    if testlineA == Test.output(1):
        print "ASCII out      - OK"
    else:
        print Test.output(1)
        print testlineA
    #Check pallet id, version id, QC bit updates
    Test.control.updatepalletid(42)
    Test.control.updateversionid("0202")
    Test.control.updateQCstatus("Q")
    testline1  = "\x1E2P000000001\x1F00986642836   \x1F000042\x1F0202        \x1FQ\x1D#BXNGMLS *********CAR-RT LOT**C-026\x1D#0894000064221822# FEB07\x1DDE2 BLIF1SZ JAN06 0002        #1 #1\x1DBRUCE BROMBEREK              ^ISC^X\x1D8900 SE HILLCREST DR\x1DVANCOUVER WA  98664-2836\x1D\x1DBECDECBCEDCDECDBCDCBCBCDEE\x1F\x1D@nd Message\x1D\x1D\x1D\x1D\x1D\x1D\x1DLine 8"
    if testline1 == Test.output():
        print "Pallet Update  - OK"
        print "Version Update - OK"
        print "QC Status bit  - OK"
    else:
        print "Pallet Version or QC update test failed"
    #Check sortcode, consolidate, and record number updates
    Test.control.updatesortcode(4)
    Test.control.updateconsolidatecode("3")
    Test.control.updaterecordnum(1492)
    testline1  = "\x1E2P000001492\x1F43986642836   \x1F000042\x1F0202        \x1FQ\x1D#BXNGMLS *********CAR-RT LOT**C-026\x1D#0894000064221822# FEB07\x1DDE2 BLIF1SZ JAN06 0002        #1 #1\x1DBRUCE BROMBEREK              ^ISC^X\x1D8900 SE HILLCREST DR\x1DVANCOUVER WA  98664-2836\x1D\x1DBECDECBCEDCDECDBCDCBCBCDEE\x1F\x1D@nd Message\x1D\x1D\x1D\x1D\x1D\x1D\x1DLine 8"
    if testline1 == Test.output():
        print "Sort Update    - OK"
        print "Cons Update    - OK"
        print "Record Number  - OK"
    else:
        print "Sort, Cons or Record Num update test failed"
        print Test.output()
        print testline1
    #Test Text Float
    Test.textarea.float("TOP")
    testline1  = "\x1E2P000001492\x1F43986642836   \x1F000042\x1F0202        \x1FQ\x1D#BXNGMLS *********CAR-RT LOT**C-026\x1D#0894000064221822# FEB07\x1DDE2 BLIF1SZ JAN06 0002        #1 #1\x1DBRUCE BROMBEREK              ^ISC^X\x1D8900 SE HILLCREST DR\x1DVANCOUVER WA  98664-2836\x1D\x1DBECDECBCEDCDECDBCDCBCBCDEE\x1D\x1D\x1D\x1D\x1D\x1D\x1D\x1D\x1F\x1D@nd Message\x1D\x1D\x1D\x1D\x1D\x1D\x1DLine 8\x1D\x1D\x1D\x1D\x1D\x1D\x1D\x1D"
    if testline1 == Test.output():
        print "Float Text     - OK"
    else:
        print "Float Text test failed"
        print Test.output()
        print testline1
    #Testing access of version and address elements
    print "%s%s%s" % ("Version:",Test.control.versionID,"##")