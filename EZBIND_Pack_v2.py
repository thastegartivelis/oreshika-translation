import zlib, os, sys, struct, time, csv, codecs

import binascii

dTestTime = 0.0
dStartTime = time.time()

dirName = './data'

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

for folder in translateFolders:
    file = folder + '.arc'
    if file.endswith('.arc') and not file.endswith('_new.arc'):
        dTestTime = 0.0
        dStartTime = time.time()

        datfile = open(os.path.join(dirName, file), 'rb')
        fileName = os.path.join(dirName, os.path.splitext(os.path.basename(file))[0]) + '_new.arc'
        fileDir = os.path.join(dirName, os.path.splitext(os.path.basename(file))[0]) + '/Compressed'

        # Read original file

        ftype = datfile.read(8).split(b'\x00')[0]
        fnum = struct.unpack('<I', datfile.read(4))[0]
        print("File Name: %s" %(file))
        print("Number of Files: %g" %(fnum))
        funknown = datfile.read(4)

        fentries = []
        for i in range(fnum):
            fNameOffset = struct.unpack('<I', datfile.read(4))[0]
            fSize = struct.unpack('<I', datfile.read(4))[0]
            fDataOffset = struct.unpack('<I', datfile.read(4))[0]
            fCRC = struct.unpack('<I', datfile.read(4))[0] # Some sort of CRC

            fentries.append([fNameOffset, fSize, fDataOffset, fCRC])

        fList = []
        for entry in fentries:
            fNameOffset, fSize, fDataOffset, fCRC = entry
            datfile.seek(fNameOffset)
            byte = datfile.read(1)
    
            fName = ""
            while byte != b'\x00':
                fName = fName + byte.decode('utf8')
                byte = datfile.read(1)
   
            fList.append([fName, fNameOffset, fSize, fDataOffset, fCRC])

        datfile.close()

        dumpfile = open(fileName, 'wb')

        dumpfile.write(b'\x45')
        dumpfile.write(b'\x5A')
        dumpfile.write(b'\x42')
        dumpfile.write(b'\x49')
        dumpfile.write(b'\x4E')
        dumpfile.write(b'\x44')
        dumpfile.write(b'\x00')
        dumpfile.write(b'\x00')
        fileNumber = struct.pack('<I',fnum)
        dumpfile.write(fileNumber[0:1])
        dumpfile.write(fileNumber[1:2])
        dumpfile.write(fileNumber[2:3])
        dumpfile.write(fileNumber[3:4])
        dumpfile.write(b'\x04')
        dumpfile.write(b'\x00')
        dumpfile.write(b'\x00')
        dumpfile.write(b'\x00')

        # Cycle through files to get information to put into EZBIND

        fEZBIND = []
        if len(fList) == 0:
            continue

        fDataOffsetCounter = fList[0][3]

        for entry in fList:
            fName, fNameOffset, fSize, fDataOffset, fCRC =  entry
            tempDir = os.path.join(fileDir, fName)
            fSizeNew = os.path.getsize(tempDir)

            if (fSizeNew % 4 == 0): 
                zeroPadding = 0
            elif(fSizeNew % 4 == 1):
                zeroPadding = 3
            elif(fSizeNew % 4 == 2):
                zeroPadding = 2
            else:
                zeroPadding = 1

            fEZBIND.append([fName, fNameOffset, fSizeNew, fDataOffsetCounter, fCRC, zeroPadding])

            fDataOffsetCounter = fDataOffsetCounter + fSizeNew + zeroPadding


        # Dump header table to new EZBIND arc

        for entry in fEZBIND:
            fName, fNameOffset, fSize, fDataOffset, fCRC, zeroPadding = entry

            # Dump file name offset
            fNO = struct.pack('<I',fNameOffset)
            dumpfile.write(fNO[0:1])
            dumpfile.write(fNO[1:2])
            dumpfile.write(fNO[2:3])
            dumpfile.write(fNO[3:4])

            # Dump file size
            fS = struct.pack('<I',fSize)
            dumpfile.write(fS[0:1])
            dumpfile.write(fS[1:2])
            dumpfile.write(fS[2:3])
            dumpfile.write(fS[3:4])

            # Dump file data offset
            fDO = struct.pack('<I',fDataOffset)
            dumpfile.write(fDO[0:1])
            dumpfile.write(fDO[1:2])
            dumpfile.write(fDO[2:3])
            dumpfile.write(fDO[3:4])

            # Dump CRC
            fC = struct.pack('<I',fCRC)
            dumpfile.write(fC[0:1])
            dumpfile.write(fC[1:2])
            dumpfile.write(fC[2:3])
            dumpfile.write(fC[3:4])
    
        # Dump file name table
        for entry in fEZBIND:
            fName, fNameOffset, fSize, fDataOffset, fCRC, zeroPadding = entry
            dumpfile.write(fName.encode('utf8'))
            dumpfile.write(b'\x00')
    
        dumpfile.write(b'\x00')
        dumpfile.write(b'\x00')
        dumpfile.write(b'\x00')

        # Dump files in new EZBIND
        for entry in fEZBIND:
            fName, fNameOffset, fSize, fDataOffset, fCRC, zeroPadding = entry

            tempDir = os.path.join(fileDir, fName)
            tempfile = open(tempDir, 'rb')

            data = tempfile.read(fSize)

            dumpfile.write(data)

            for i in range(zeroPadding):
                dumpfile.write(b'\x00')

            tempfile.close()

        # Pad file with zero to make fsize % 0x1000

        zeroPadding = 4096 - (dumpfile.tell() % 4096)
        for i in range(zeroPadding):
            dumpfile.write(b'\x00')

        dumpfile.close()
        os.rename(fileName, os.path.join(dirName, file))

dTestTime = time.time() - dStartTime
print("Total Test Time = %.3f sec" % dTestTime)




