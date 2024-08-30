import os
import struct
import csv

values = []

for entry in os.listdir('data'):
    if not entry.endswith('.arc') and entry.startswith('EZBIND_'):
        for filename in os.listdir(os.path.join('data', entry, 'Uncompressed')):
            if filename.endswith('.mlb') and not filename.endswith('_new.mlb') and not filename.endswith('_narration.mlb') and not filename == 'moviesubtitle.mlb' and not filename.endswith('_v.mlb') and not filename.endswith('_NA.mlb') and not filename.endswith('_NAME.mlb'):
                path = os.path.join('data', entry, 'Uncompressed', filename)
                print('opening', path)
                with open(path, 'rb') as file:
                    data = file.read(3)
                    if data != b'\x4d\x4c\x54':
                        raise Error
                    sectionCount = int.from_bytes(file.read(1), byteorder='little')
                    sectionStarts = []
                    for i in range(sectionCount):
                        sectionStarts.append(int.from_bytes(file.read(4), byteorder='little'))
                    print('sections start at', sectionStarts)
                    for sectionIndex, sectionStart in enumerate(sectionStarts):
                        file.seek(sectionStart)
                        count = int.from_bytes(file.read(4), byteorder='little')
                        print('section has', count, 'strings')
                        stringStarts = []
                        for i in range(count):
                            stringStarts.append(int.from_bytes(file.read(4), byteorder='little'))
                        print('string starts:', stringStarts)
                        for stringIndex, stringStart in enumerate(stringStarts):
                            if stringStart % 2 == 1:
                                print(path, 'section starting at', sectionStart, 'has a string at', stringStart, 'that is odd')
                                continue
                            file.seek(stringStart)
                            string = b''
                            done = False
                            while not done:
                                byte1 = file.read(1)
                                byte2 = file.read(1)
                                if byte1 == b'' or byte2 == b'':
                                    break 
                                #print('got two bytes', byte1, byte2)
                                if byte1 == b'\x00' and byte2 == b'\x00' or byte1 == b'\xff' and byte2 == b'\xff': # or byte1 == b'' and byte2 == b'':
                                    done = True
                                else:
                                    string += byte1
                                    string += byte2
                            print('full string is', string.decode('utf-16-le'))
                            values.append({'filename': filename, 'sector': entry, 'text': string.decode('utf-16-le'), 'section': sectionIndex, 'string': stringIndex, 'stringLocation': stringStart})

path = os.path.join('data', 'MLB_0025.mlb')
print('opening', path)
with open(path, 'rb') as file:
    data = file.read(3)
    if data != b'\x4d\x4c\x54':
        raise Error
    sectionCount = int.from_bytes(file.read(1), byteorder='little')
    sectionStarts = []
    for i in range(sectionCount):
        sectionStarts.append(int.from_bytes(file.read(4), byteorder='little'))
    print('sections start at', sectionStarts)
    for sectionIndex, sectionStart in enumerate(sectionStarts):
        file.seek(sectionStart)
        count = int.from_bytes(file.read(4), byteorder='little')
        print('section has', count, 'strings')
        stringStarts = []
        for i in range(count):
            stringStarts.append(int.from_bytes(file.read(4), byteorder='little'))
        print('string starts:', stringStarts)
        for stringIndex, stringStart in enumerate(stringStarts):
            if stringStart % 2 == 1:
                print(path, 'section starting at', sectionStart, 'has a string at', stringStart, 'that is odd')
                continue
            file.seek(stringStart)
            string = b''
            done = False
            while not done:
                byte1 = file.read(1)
                byte2 = file.read(1)
                #print('got two bytes', byte1, byte2)
                if byte1 == b'\x00' and byte2 == b'\x00' or byte1 == b'\xff' and byte2 == b'\xff': # or byte1 == b'' and byte2 == b'':
                    done = True
                else:
                    string += byte1
                    string += byte2
            print('full string is', string.decode('utf-16-le'))
            values.append({'filename': 'MLB_0025.mlb', 'sector': 'None', 'text': string.decode('utf-16-le'), 'section': sectionIndex, 'string': stringIndex, 'stringLocation': stringStart})

with open('strings.csv', 'w') as csvfile:
    fieldnames = ['sector', 'filename', 'section', 'string', 'stringLocation', 'text']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for record in values:
        writer.writerow({ 'sector': record.get('sector'), 'filename': record.get('filename'), 'text': record.get('text'), 'section': record.get('section'), 'string': record.get('string'), 'stringLocation': record.get('stringLocation') })
