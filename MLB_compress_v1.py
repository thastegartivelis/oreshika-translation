import zlib, os, sys, struct, time, csv, codecs

dTestTime = 0.0
dStartTime = time.time()

translateFiles = set()
translateFolders = set()
with codecs.open('translations.csv', 'r') as file:
    reader = csv.reader(file)
    for row in reader:
        folder = row[0]
        file = row[1]
        original = row[5]
        translation = row[6]
        translateFolders.add(folder)
        translateFiles.add(file)

for entry in os.listdir('data'):
    if entry in translateFolders:
        for file in os.listdir(os.path.join('data', entry, 'Uncompressed')):
            if file.endswith('_new.mlb'):
                datfname = os.path.join('data', entry, 'Uncompressed', file)
                fSize = os.path.getsize(datfname)
                datfile = open(datfname, 'rb')

                fileName = file.replace('_new', '')

                dumpfile = open(fileName, 'wb')

                # Write Header to compressed file

                dumpfile.write(b'\x1F')
                dumpfile.write(b'\x8B')
                dumpfile.write(b'\x09')
                dumpfile.write(b'\x00')

                fSizeNum = struct.pack('<I',fSize)

                dumpfile.write(fSizeNum[0:1])
                dumpfile.write(fSizeNum[1:2])
                dumpfile.write(fSizeNum[2:3])
                dumpfile.write(fSizeNum[3:4])

                uncompressedData = datfile.read(fSize)
                compressedData = zlib.compress(uncompressedData, 9)

                dumpfile.write(compressedData[2:len(compressedData)-4])

                dumpfile.close()

                datfile.close()
                os.remove(datfname)
                os.rename(fileName, os.path.join('data', entry, 'Compressed', fileName))

dTestTime = time.time() - dStartTime
print()
print("Total Test Time = %.3f sec" % dTestTime)
