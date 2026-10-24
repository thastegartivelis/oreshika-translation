mlb file breakdown

Most or all mlb files seem to be UTF16le.

# structure

## Main headers
4d 4c 54

1 byte for section count

## Section locations block

For each section identified in the count:

4 bytes for section start location

## Section block

In any given section, which starts at the location identified in the "section locations" block, expect:

### String information block
4 byte header with the count of strings

for each string in the section, 4 bytes with the address in the file of each string

### Strings block

for each string address, the string should be terminated with either 2 null bytes or 0xff 0xff


## Tools
The `mlb_extractor.py` script in `oreshika-translation/tools/` can be used to extract strings from `.mlb` files.

Usage:
`python3 oreshika-translation/tools/mlb_extractor.py <path_to_file>`

Example:
`python3 oreshika-translation/tools/mlb_extractor.py oreshika-translation/data/EZBIND_2210/Uncompressed/ev_d03a02r05_00.mlb`

_NAME files have the same few strings every time, so let's leave them alone for now.

Above works for non _narration/_v/_NA files. These other files seem to work off of individual bytes? But also they seem to match the equivalent non-narration file, so may not need modification, or may need special modification.

moviesubtitle also doesn't seem to fit the pattern, so will probably need its own parsing logic, since it for sure has strings to localize.
