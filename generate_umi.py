import os
import math

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
    
    Sector tracking: We maintain cumulative sector counter starting at 52767 (UMD offset where USER volume begins).
    Each file's sector count is the CURRENT position, which advances after each entry.
    """
    files = get_file_list(input_dir)
    # Sort files to ensure consistent sector mapping (alphabetical by path)
    # Sort files to ensure consistent sector mapping (alphabetical by rel_path)

    current_sector = 52767  # UMD volume start offset for contiguous data + metadata

    with open(ufl_file_path, 'w') as f:
        for item in files:
            rel_path = item['rel_path'].split('PSP_Game/')[1]
            file_size = item['size']
            full_path = item['full_path']
            # Sector calculation: (size - (size % 2048)) / 2048 = sectors to consume
            sector_count = math.ceil(file_size / 2048)

            # Write line with format "relpath" "absolutepath" CURRENT_SECTOR SIZE
            f.write(f'"/PSP_GAME/{rel_path}", "{full_path}", {current_sector}, {file_size},\n')

            current_sector += sector_count  # Advance to next sector for following file

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
