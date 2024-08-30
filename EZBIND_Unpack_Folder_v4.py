import zlib, os, sys, struct, time

dTestTime = 0.0
dStartTime = time.time()

fileListTrack = 'Oreshika_File_List.csv'
fListTrack = open(fileListTrack, 'w+')

fListTrack.write("Folder, File Name, Compressed, Uncompressed \n")


fDir = os.getcwd() + '/data'
os.chdir(fDir)
counter = 0
for i in os.listdir(fDir):
    if i.endswith(".arc"):
        counter = counter + 1
        print(i)

        datfname = i

        scriptdir = fDir

        datfile = open(datfname, 'rb')

        ftype = datfile.read(8).split(b'\x00')[0]
        fnum = struct.unpack('<I', datfile.read(4))[0]
        print("File Name: %s" %(datfname))
        print("Number of Files: %g" %(fnum))
        funknown = datfile.read(4)

        # Read header and get file information

        fentries = []
        for j in range(fnum):
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
                fName = fName + byte.decode('ISO-8859-1')
                byte = datfile.read(1)
           
            fList.append([fName, fNameOffset, fSize, fDataOffset, fCRC])

        dumpdir0 = os.path.splitext(os.path.basename(datfname))[0]
        dumpdir0 = os.path.join(scriptdir, dumpdir0)

        print(dumpdir0)

        try:
            os.mkdir(dumpdir0)
        except WindowsError: pass


        dumpdir = os.path.splitext(os.path.basename(datfname))[0] + '/Compressed'
        dumpdir = os.path.join(scriptdir, dumpdir)

        print(dumpdir)

        try:
            os.mkdir(dumpdir)
        except WindowsError: pass

        dumpdir1 = os.path.splitext(os.path.basename(datfname))[0] + '/Uncompressed'
        dumpdir1 = os.path.join(scriptdir, dumpdir1)

        print(dumpdir1)

        try:
            os.mkdir(dumpdir1)
        except WindowsError: pass

        # Dump Files
        print()
        print("Dumping Files:")

        for entry in fList:
            fName, fNameOffset, fSize, fDataOffset, fCRC = entry
            print(fName)
            tempdir = os.path.join(dumpdir, fName)

            # Dump compressed Files

            dumpfile = open(tempdir, 'wb')
            datfile.seek(fDataOffset)
            data = datfile.read(fSize)
            dumpfile.write(data)
            dumpfile.close()

            # Dump extract and dump uncompressed files

            EZBIND_Name = i.split('.',1)[0]
            print(fName)
            if fName.endswith(".mlb"): # Add any other file extension if compressed with zlib
                print('it did end')

                header = data[0:5]
                print('header is', header)
                print(header[0], header[1], header[2], header[3])
                print(header[0] == b'\x1F')

                if (header[0:1] == b'\x1F' and header[1:2] == b'\x8B' and header[2:3] == b'\x09' and header[3:4] == b'\x00'):
                    print('writing')
            
                    tempdir = os.path.join(dumpdir1, fName)
                    dumpfile = open(tempdir, 'wb')

                    compressedData = data[8:len(data)] # bytes 1-9 header data
                    uncompressedData = zlib.decompress(compressedData, -zlib.MAX_WBITS)
                    
                    dumpfile.write(uncompressedData)

                    dumpfile.close()

                    fListTrack.write(EZBIND_Name + "," + fName + ",1,1 \n")

                else:
                    fListTrack.write(EZBIND_Name + "," + fName + ",1,0 \n")
                    
            else:
                    fListTrack.write(EZBIND_Name + "," + fName + ",1,0 \n")

                    
        datfile.close()

fListTrack.close()     
dTestTime = time.time() - dStartTime
print()
print("Total Test Time = %.3f sec" % dTestTime)   
