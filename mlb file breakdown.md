mlb file breakdown




4d4c 54(section pointer count in 1 byte)


for each section pointer (ordered sequentially, starting at byte 5), expect 4 bytes for section start location


for each section, expect a 4 byte header with the count of strings

for each string in section, expect 4 bytes with the address in the file of each string

for each address, continue reading until 2 bytes of 0s or ffs








_NAME files have the same few strings every time, so let's leave them alone for now.



Above works for non _narration/_v/_NA files. These other files seem to work off of individual bytes? But also they seem to match the equivalent non-narration file, so may not need modification, or may need special modification.


moviesubtitle also doesn't seem to fit the pattern, so will probably need its own parsing logic, since it for sure has strings to localize.
