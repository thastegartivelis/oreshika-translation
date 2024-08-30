#!/bin/sh

rm -r data
cp Original\ game/PSP_Game/USRDIR/data.ore .
python3 data.ore_unpack_v1.py
python3 EZBIND_Unpack_Folder_v4.py
rm translations.csv
curl -L "https://docs.google.com/spreadsheets/d/1WGbyOT_U6ErMef8GOxGm7yQcT9sqpaA6POoba4LsbTA/export?gid=973457807&format=csv" -o translations.csv
python3 autosubstitute.py
python3 MLB_compress_v1.py
python3 EZBIND_Pack_v2.py
python3 data.ore_pack_v2.py
mv data_new.ore Rebuilt\ game/PSP_GAME/USRDIR/data.ore
