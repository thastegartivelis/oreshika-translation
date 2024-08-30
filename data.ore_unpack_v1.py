import zlib, os, sys, struct, time

dTestTime = 0.0
dStartTime = time.time()

datfname = 'data.ore' # hardcoded for now
dataOREFileSize = os.path.getsize(datfname)

fileName = 'Dump_Data_Ore.txt'
f1 = open(fileName, 'w+')

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

fTable = []

for i in range(len(fentries)-1):
    fCRC, fOffset, fPointer = fentries[i]
    fStart = fPointer
    fEnd = fentries[i+1][2]
    fSize = fEnd-fStart

    fTable.append([fCRC, fOffset, fStart, fEnd, fSize])


# Dump files

counterName = 0
scriptdir = os.path.dirname(sys.argv[0])

dumpdir = os.path.splitext(os.path.basename(datfname))[0]
dumpdir = os.path.join(scriptdir, dumpdir)

try:
    os.mkdir(dumpdir)
except WindowsError: pass
os.chdir(dumpdir)

print("****************************************")
print("* Dumping Files")
print("****************************************")
for entry in fTable:
    fCRC, fOffset, fStart, fEnd, fSize = entry
    fileType = ""
    datfile.seek(fStart)
    bytes = datfile.read(8)
    filename = bytes
    if filename[0:6] == "EZBIND".encode('utf8'):
        fName = "EZBIND_%04d.arc" %(counterName)
    elif filename[0:4] == "RIFF".encode('utf8'):
        fName = "RIFF_%04d.rif" %(counterName)
    elif filename[4:7] == "PGF".encode('utf8'):
        fName = "PGF_%04d.pgf" %(counterName)
    elif filename[0:3] == "MLT".encode('utf8'):
        fName = "MLB_%04d.mlb" %(counterName)
    elif filename[0:3] == "ppt".encode('utf8'):
        fName = "PPT_%04d.ppt" %(counterName)
    elif filename[1:4] == "PNG".encode('utf8'):
        fName = "PNG_%04d.png" %(counterName)
    elif filename[0:3] == "ppc".encode('utf8'):
        fName = "PPC_%04d.ppc" %(counterName)   
    else:
        fName = "Unknown_%04d.dat" %(counterName)
        print(filename)

    print(fName)
    counterName = counterName + 1
    f1.write(fName)
    f1.write(',')
    f1.write(hex(fStart))
    f1.write(',')
    f1.write(hex(fEnd))
    f1.write(',')
    f1.write(hex(fSize))
    f1.write("\n")

    # Dump files out
    os.path.join(dumpdir, fName)
    dumpfile = open(fName, 'wb')
    datfile.seek(fStart)
    data = datfile.read(fSize)
    dumpfile.write(data)
    dumpfile.close()


datfile.close()
f1.close()
dTestTime = time.time() - dStartTime
print()
print("Total Test Time = %.3f sec" % dTestTime) 


