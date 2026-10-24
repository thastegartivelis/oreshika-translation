import os
import math

def get_file_list(base_dir):
    """
    Recursively walks the Rebuilt game directory and collects file paths and sizes.
    """
    file_list = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            full_path = os.path.join(root, file)
            # We want the path relative to the "oreshika-translation" directory
            # so that umdgenc (running there) can find them.
            # Since the input_dir is "oreshika-translation/Rebuilt game",
            # we want the path to start with "Rebuilt game/"
            # We achieve this by finding the path relative to the parent of the Rebuilt game folder.
            parent_dir = os.path.dirname(base_dir)
            rel_path = os.path.relpath(full_path, parent_dir).replace("\\", "/")
            file_size = os.path.getsize(full_path)
            file_list.append({
                "full_path": full_path,
                "rel_path": rel_path,
                "size": file_size
            })
    return file_list

def write_umi_header(umi_file_path):
    """
    Creates the .umi file header based on the Chovy-GM logic.
    """
    # TitleID is used for the DiscId calculation
    title_id = "SCUS10000"  # Placeholder, user can change
    zone = title_id[0:4]
    identifier = title_id[4:9]
    disc_id = f"{zone}-{identifier}"

    with open(umi_file_path, 'w') as f:
        f.write("[SYS]\n")
        f.write(f"VERSION=1.00\n")
        f.write(f"APPLICATION=PSP GAME\n")
        f.write(f"LAYER_STRUCT=SINGLE\n")
        f.write(f"FORCE16SECTOR=0\n")
        f.write(f"LAYER_TRP=0\n")
        # The .ufl file is the same name as .umi but with .ufl extension
        ufl_path = umi_file_path.replace(".umi", ".ufl")
        f.write(f"FILE_LIST={ufl_path}\n")
        f.write(f"BOOT=0\n")
        f.write(f"UPDATE=1\n")
        f.write(f"CRASH_BOOT_FILE=1\n")
        f.write("[/SYS]\n\n")

        f.write("[MDI]\n")
        f.write(f"DISCNAME={disc_id}\n")
        f.write(f"PRODUCER=Chovy-GM\n")
        f.write(f"COPYRIGHT=CBPS\n")
        f.write(f"REGION_CODE=WW\n")
        f.write("[/MDI]\n\n")

        f.write("[VOL]\n")
        f.write(f"VOLUME=Chovy-GM\n")
        f.write(f"PUBLISHER=CBPS\n")
        f.write(f"VOLUME SET=\n")
        f.write(f"DATA PREPARER=Chovy-GM\n")
        f.write("[/VOL]\n\n")

def create_ufl(ufl_file_path, input_dir):
    """
    Creates the .ufl file based on the Chovy-GM logic.
    """
    files = get_file_list(input_dir)
    # Sort files to ensure consistent sector mapping (alphabetical by path)
    files.sort(key=lambda x: x['rel_path'])

    current_sector = 52767

    with open(ufl_file_path, 'w') as f:
        for item in files:
            file_size = item['size']
            # Sector calculation: (size - (size % 2048)) / 2048 + 1
            sector_count = math.ceil(file_size / 2048)

            # The Ufl format expects: Path,FullPath,Sector,Size
            # We use the rel_path which should start with "Rebuilt game/"
            f.write(f"{item['rel_path']}{item['full_path']}{current_sector}{file_size}\n")

            current_sector += sector_count

if __name__ == "__main__":
    # Configuration
    # The input_dir is the folder containing the files we want to pack
    input_dir = "/mnt/c/Users/jeff's 2021 pc/workspace/decomp/oreshika/oreshika-translation/Rebuilt game"
    # The .umi and .ufl files will be created in the oreshika-translation folder
    umi_path = "/mnt/c/Users/jeff's 2021 pc/workspace/decomp/oreshika/oreshika-translation/blueprint.umi"
    ufl_path = "/mnt/c/Users/jeff's 2021 pc/workspace/decomp/oreshika/oreshika-translation/blueprint.ufl"

    print(f"Generating {umi_path}...")
    write_umi_header(umi_path)

    print(f"Generating {ufl_path}...")
    create_ufl(ufl_path, input_dir)

    print("Done.")
