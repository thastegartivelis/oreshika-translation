import zlib, os, sys, struct, time

dTestTime = 0.0
dStartTime = time.time()

datfname = 'data.ore' # hardcoded for now
dataOREFileSize = os.path.getsize(datfname)

fileName = 'data_new.ore'
dumpfile = open(fileName, 'wb')

scriptdir = os.path.dirname(sys.argv[0])

fDir = './data'

datfile = open(datfname, 'rb')

datfile.seek(16388)

# Read table Header

fnum = struct.unpack('<I', datfile.read(4))[0]
datfile.read(4)
fCRCHeader = struct.unpack('<I', datfile.read(4))[0]

fentries = []
for i in range(fnum+1):
    fCRC = struct.unpack('<I', datfile.read(4))[0]
    fOffset = struct.unpack('<I', datfile.read(4))[0]
    fPointer = fOffset & 2147481600 #0x7FFFF800
    fentries.append([fCRC, fOffset, fPointer])


# Get file list and sort it based on filenumber
sortedList = []

for i in os.listdir(fDir):
    if os.path.isfile(os.path.join(fDir, i)):
        numFile = i.split("_")[1].split(".")[0]
        fileSize = os.path.getsize(fDir + '/'+ i)
        sortedList.append([numFile, i, fileSize])

sortedList.sort()


# Read and write first 16400 bytes and dump to file
datfile.seek(0)
dumpfile.write(datfile.read(16400))

# Compile header table

fOffset = 49152

for i in range(len(fentries)-1):
    fCRC = fentries[i][0]

    fileCRC = struct.pack('<I',fCRC)
    dumpfile.write(fileCRC[0:1])
    dumpfile.write(fileCRC[1:2])
    dumpfile.write(fileCRC[2:3])
    dumpfile.write(fileCRC[3:4])

    fileOffset = struct.pack('<I',fOffset)
    dumpfile.write(fileOffset[0:1])
    dumpfile.write(fileOffset[1:2])
    dumpfile.write(fileOffset[2:3])
    dumpfile.write(fileOffset[3:4])

    fOffset = fOffset + sortedList[i][2]

# Run last case in file    
i = i+1
fCRC = fentries[i][0]
fileCRC = struct.pack('<I',fCRC)
dumpfile.write(fileCRC[0:1])
dumpfile.write(fileCRC[1:2])
dumpfile.write(fileCRC[2:3])
dumpfile.write(fileCRC[3:4])

fileOffset = struct.pack('<I',fOffset)
dumpfile.write(fileOffset[0:1])
dumpfile.write(fileOffset[1:2])
dumpfile.write(fileOffset[2:3])
dumpfile.write(fileOffset[3:4])

# Pad zeros at beginning of file
for i in range(1800):
    dumpfile.write(b'\x00')

# Read and write out data in the file.
for entry in sortedList:
    numFile, nameFile, sizeFile = entry
    print(nameFile)
    tempDir = os.path.join(fDir, nameFile)
    
    tempfile = open(tempDir, 'rb')
    data = tempfile.read(sizeFile)
    dumpfile.write(data)
    tempfile.close()
    

datfile.close()
dumpfile.close()


dTestTime = time.time() - dStartTime
print()
print("Total Test Time = %.3f sec" % dTestTime) 


