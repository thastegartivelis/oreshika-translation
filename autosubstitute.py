import os
import math
import zlib
import sys
import struct
import time
import csv
import codecs

last = ''
substitutions = {}
usedSubstitutions = {}
availableSubstitutions = set()
translateFiles = set()
translateFolders = set()
with codecs.open('translations.csv', 'r') as file:
    reader = csv.reader(file)
    for index, row in enumerate(reader):
        if index == 0:
            continue
        folder = row[0]
        file = row[1]
        original = row[5]
        translation = row[6]
        translateFolders.add(folder)
        translateFiles.add(file)
        availableSubstitutions.add(original)
        #print(row[0])
        #text = row[0].replace('NULL', '\x00')
        if not folder in substitutions:
            substitutions[folder] = {}
        if not file in substitutions.get(folder):
            substitutions.get(folder)[file] = {}
        if original in substitutions.get(folder).get(file):
            #print('duplicate: {0}'.format(text.encode('utf8')))
            #print((text.encode('utf8')))
            pass
        # substitutions[text] = 't'.decode('utf8')
        substitutions.get(folder).get(file)[original] = translation
        last = original

class Parser():

    def __init__(self):

        # Variables to store things
        self.statusText = ''
        self.fHeader1 = []
        self.fHeader2 = []
        self.fData = []
        self.fHeaderTableLength = []
        self.fFFList = []
        self.fHeader = []
        self.indexSelection = 0

################################################################################
    def OnOpen(self,filename, fileSubstitutions):
        self.statusText = 'Filename: ' + filename + '   Status: Open File'
        print((self.statusText))

        datfile = open(filename, 'rb')

        tempData = datfile.read(3)
        fHeaderListNum = ord(datfile.read(1))

        # Read the main header and compile list of headers in file
        for i in range(fHeaderListNum):
            header1 = struct.unpack('<I', datfile.read(4))[0]
            location = datfile.tell()-4 
            self.fHeader1.append([i, location, header1])

        # Iterate through all headers and find if they end in 0xFF
        fileSize = os.path.getsize(filename)
        for entry in self.fHeader1:
            hNum, hOffset, fOffset = entry
            datfile.seek(fOffset-1)

            byte = datfile.read(1)

            if byte == '\xFF':
                self.fFFList.append('1')
            else:
                self.fFFList.append('0')

        datfile.seek(fileSize-1)
        byte = datfile.read(1)

        if byte == '\xFF':
            self.fFFList.append('1')
        else:
            self.fFFList.append('0')
            
        self.fFFList = self.fFFList[1:len(self.fFFList)]
        
        # Iterate through all the headers and save header data
        tempCounter = 0
        for entry in self.fHeader1:
            hNum, hOffset, fOffset = entry
            tempList = []
            datfile.seek(fOffset)

            headerListNum = struct.unpack('<I', datfile.read(4))[0]
            for i in range(headerListNum):
                header2 = struct.unpack('<I', datfile.read(4))[0]
                location = datfile.tell()-4
                self.fHeader2.append([hNum, hOffset, i, location, header2])

            self.fHeaderTableLength.append([tempCounter, headerListNum])
            tempCounter = tempCounter + 1
 
        headerKey = 0
        for entry in self.fHeader2:
            h1Num, h1Offset, h2Num, h2Offset, fOffset = entry

            datfile.seek(fOffset)
                
            text = []
            byte = datfile.read(1)
            byte1 = datfile.read(1)
            flag = 1

            while flag == 1:
                text.append(byte)
                text.append(byte1)

                byte = datfile.read(1)
                byte1 = datfile.read(1)

                if byte == '' or byte1 == '' or ord(byte) == 0 and ord (byte1) == 0:
                    flag = 0
                    
            textSize = len(text)

            datfile.seek(fOffset)
            textByte = datfile.read(textSize)
            textDump = textByte.decode('utf-16-le')
            usedSubstitutions[textDump] = 1

            if fileSubstitutions.get(textDump, textDump) == textDump:
                pass
                #print(textDump.encode('utf-8'))
                #print
                #print('no translation found for {0}'.format(textDump.encode('utf-8')))
                #print('', textDump)
            else:
                pass
                #print('substituting {0} for {1}'.format(fileSubstitutions.get(textDump).encode('utf-8'), textDump.encode('utf-8')))
            textArray = []
            for i in fileSubstitutions.get(textDump, textDump).encode('utf-16-le'):
                textArray.append(i)

            self.fData.append(["%04g" %(headerKey), h1Num, h1Offset, h2Num, h2Offset, fOffset, textArray, textDump])

            headerKey = headerKey + 1

        datfile.close()

        for entry in self.fData:
            self.fHeader.append(entry[0])

###############################################################################
    def OnSave(self,filename):
        # Get file name

        saveFileName = filename.split('.')[0]+ "_new.mlb"
          
        dumpFile = open(saveFileName, 'wb')

        # Write header for file

        dumpFile.write(b'\x4D')
        dumpFile.write(b'\x4C')
        dumpFile.write(b'\x54')

        # Figure out Header data
        lengthHeader = len(self.fHeader1)
        dumpFile.write(bytes([lengthHeader]))

        for i in range(lengthHeader):
            dumpFile.write(b'\x00')
            dumpFile.write(b'\x00')
            dumpFile.write(b'\x00')
            dumpFile.write(b'\x00')


        dataHeaderList = []
        dataPointers = []
        dataList = []
        location = 0
        for header in range(len(self.fHeaderTableLength)):
            headerNum, tableNum = self.fHeaderTableLength[header]
            subData = []
            offsetTemp = 0
            offsetArray = []
            for i in range(tableNum):
                data = self.fData[location][6]
                for byte in data:
                    subData.append(bytes([byte]))
                subData.append(b'\x00')
                subData.append(b'\x00')

                offsetArray.append(offsetTemp)
                offsetTemp = offsetTemp + len(data) + 2

                location = location + 1

            if self.fFFList[header] == '1':
                subData.append('\xFF')
                subData.append('\xFF')
                   
            dataList.append(subData)
            dataPointers.append(offsetArray)

        mainHeaderOffset = []

        for i in range(len(dataPointers)):
            header = dataPointers[i]
            data = dataList[i]
            location = dumpFile.tell()

            mainHeaderOffset.append(int(location))
            lengthHeader = len(header)

            dataOffset = location + 4 + lengthHeader*4

            tempData = struct.pack('<I',lengthHeader)
            dumpFile.write(tempData[0:1])
            dumpFile.write(tempData[1:2])
            dumpFile.write(tempData[2:3])
            dumpFile.write(tempData[3:4])

            for item in header:
                headerOffset = item + dataOffset
                tempData = struct.pack('<I',headerOffset)
                dumpFile.write(tempData[0:1])
                dumpFile.write(tempData[1:2])
                dumpFile.write(tempData[2:3])
                dumpFile.write(tempData[3:4])
                  
                
            for byte in data:
                dumpFile.write(byte)
               
        dumpFile.close()

        dumpFile = open(saveFileName, "r+b")
        dumpFile.seek(4)

        for item in mainHeaderOffset:
            tempData = struct.pack('<I',item)
            dumpFile.write(tempData[0:1])
            dumpFile.write(tempData[1:2])
            dumpFile.write(tempData[2:3])
            dumpFile.write(tempData[3:4])

        dumpFile.close()

for entry in os.listdir('data'):
    if entry in translateFolders:
        for file in os.listdir(os.path.join('data', entry, 'Uncompressed')):
            if file in translateFiles:
                parser = Parser()
                parser.OnOpen(os.path.join('data', entry, 'Uncompressed', file), substitutions.get(entry).get(file))
                parser.OnSave(os.path.join('data', entry, 'Uncompressed', file))
if 'MLB_0025.mlb' in translateFiles:
    parser = Parser()
    parser.OnOpen(os.path.join('data', 'MLB_0025.mlb'), substitutions.get('None').get('MLB_0025.mlb'))
    parser.OnSave(os.path.join('data', 'MLB_0025.mlb'))
    os.rename(os.path.join('data', 'MLB_0025_new.mlb'), os.path.join('data', 'MLB_0025.mlb'))
#print('', last)
unusedKeys = availableSubstitutions.difference(set(usedSubstitutions.keys()))
for key in unusedKeys:
    #pass
    print("unused translation: {0}".format(key.encode('utf8')))
