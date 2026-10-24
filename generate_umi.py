import os
import csv

def get_file_list(base_dir):
    """
    Recursively walks the Rebuilt game directory and collects file paths and sizes.
    Input directory is 'oreshika-translation/Rebuilt game' - contains all files (SYSDIR, USRDIR, ICON0.PNG, etc.)
    We need this for UMDImageGenerator to find all contents to pack into the ISO.
    """
    file_list = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            full_path = os.path.join(root, file)
            # We want the path relative to the "Rebuilt game" directory
            parent_dir = os.path.dirname(base_dir)
            rel_path = os.path.relpath(full_path, base_dir).replace("\\", "/")
            file_size = os.path.getsize(full_path)
            file_list.append({
                "full_path": full_path,
                "rel_path": rel_path,
                "size": file_size
            })
    file_list.sort(key=lambda item: item["rel_path"].casefold())
    return file_list

def write_umi_header(umi_file_path):
    """
    Creates the .umi file header
    """
    # TitleID is used for the DiscId calculation
    title_id = "UCJS10117"
    zone = title_id[0:4]
    identifier = title_id[4:9]
    disc_id = f"{zone}-{identifier}"

    # Determine the directory of the .umi file and make paths relative to it
    umi_dir = os.path.dirname(umi_file_path)
    
    with open(umi_file_path, 'w') as f:
        f.write("[SYS]\n")
        f.write(f"VERSION=\"1.00\"\n")
        f.write(f"APPLICATION=\"PSP GAME\"\n")
        f.write(f"LAYER_STRUCT=\"SINGLE\"\n")
        f.write(f"FORCE16SECTOR=0\n")
        f.write(f"LAYER_TRP=0\n")
        # The .ufl file is the same name as .umi but with .ufl extension
        ufl_path = os.path.basename(umi_file_path).replace(".umi", ".ufl")
        f.write(f"FILE_LIST=\"{ufl_path}\"\n")
        
        f.write(f"BOOT=0\n")
        f.write(f"UPDATE=1\n")
        f.write(f"CRASH_BOOT_FILE=1\n")
        f.write("[/SYS]\n\n")

        f.write("[MDI]\n")
        f.write(f"DISCNAME=\"{disc_id}\"\n")
        f.write(f"PRODUCER=\"Gart\"\n")
        f.write(f"COPYRIGHT=\"xxx\"\n")
        f.write(f"REGION_CODE=\"WW\"\n")
        f.write("[/MDI]\n\n")

        f.write("[VOL]\n")
        f.write(f"VOLUME=\"Oreshika\"\n")
        f.write(f"PUBLISHER=\"Gart\"\n")
        f.write(f"VOLUME SET=\"\"\n")
        f.write(f"DATA PREPARER=\"Gart\"\n")
        f.write("[/VOL]\n\n")

def create_ufl(ufl_file_path, input_dir):
    """
    Creates .ufl file specifying file layout for UMDISO (Contiguous Data + Metadata).
    
    Format is:
        "{isopath}", "{pcpath}", {sector}, {size}
    Where isopath = path relative to ISO root (/PSP_GAME/), pcpath = absolute file path.
    
    Sector locations come from umd_layout.csv, which records the extents
    observed in the original ISO. UMDGen relocates two boot files whose
    original extents are before its user-data area.
    """
    files = get_file_list(input_dir)
    sector_map = {}
    with open("umd_layout.csv", newline="") as layout_file:
        for row in csv.DictReader(layout_file):
            sector_map[row["path"]] = int(row["sector"])

    file_paths = {item["rel_path"] for item in files}
    missing = file_paths - sector_map.keys()
    stale = sector_map.keys() - file_paths
    if missing or stale:
        raise ValueError(f"UMD layout mismatch; missing={sorted(missing)}, stale={sorted(stale)}")

    files.sort(key=lambda item: sector_map[item["rel_path"]])

    with open(ufl_file_path, 'w') as f:
        for item in files:
            rel_path = item['rel_path'].split('PSP_Game/')[1]
            file_size = item['size']
            full_path = item['full_path']
            sector = sector_map[item['rel_path']]

            f.write(f'"/PSP_GAME/{rel_path}", "{full_path}", {sector}, {file_size},\n')

if __name__ == "__main__":
    # Configuration
    # The input_dir is the folder containing the files we want to pack
    input_dir = "Rebuilt game"
    # The .umi and .ufl files will be created in the oreshika-translation folder
    umi_path = "blueprint.umi"
    ufl_path = "blueprint.ufl"

    print(f"Generating {umi_path}...")
    write_umi_header(umi_path)

    print(f"Generating {ufl_path}...")
    create_ufl(ufl_path, input_dir)

    print("Done.")
