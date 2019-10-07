import json
import os
import os.path
import re
import shutil
import subprocess

def insert(lines, update):
    for k, v in update.items():
        offset = v[0]
        for i, line in enumerate(v[1 :], 1):
            if lines[lines.index(k) + offset + i] == line:
                break
            lines.insert(lines.index(k) + offset + i, line)

def main():
    latest_ver = (-1, -1, -1)
    discord_local_dir = os.path.join(os.getenv("LOCALAPPDATA"), "Discord")
    for name in os.listdir(discord_local_dir):
        if (os.path.isdir(os.path.join(discord_local_dir, name))
                and re.match(r"^app-\d+\.\d+\.\d+$", name)):
            version = tuple(map(int, name[4 :].split(".")))
            if version > latest_ver:
                latest_ver = version
    assert latest_ver != (-1, -1, -1), "Invalid version"

    # Set up paths
    desktop_core_dir = os.path.join(os.getenv("APPDATA"), "Discord",
                                    "{}.{}.{}".format(*latest_ver),
                                    "modules", "discord_desktop_core")
    core_file = os.path.join(desktop_core_dir, "core.asar")
    core_dir = os.path.join(desktop_core_dir, "core")
    cwd = os.path.dirname(__file__)

    # Extract "core.asar" and create back up
    extract_cmd = ["asar", "extract", core_file, core_dir]
    subprocess.call(extract_cmd, cwd=desktop_core_dir, shell=True)
    shutil.copy2(core_file, core_file + ".bak")

    func_map = {
        "insert": insert
    }
    with open(os.path.join(cwd, "updates.json"), "r") as f:
        updates = json.load(f)
        for file in updates:
            with open(os.path.join(core_dir, file), "r+") as target:
                lines = target.readlines()
                for cmd in updates[file]:
                    try:
                        func_map[cmd](lines, updates[file][cmd])
                    except KeyError:
                        print("Invalid function")
                target.seek(0)
                target.writelines(lines)
                target.truncate()

    # Pack "core.asar" and remove "core" dir
    pack_cmd = ["asar", "pack", core_dir, core_file]
    subprocess.call(pack_cmd, cwd=desktop_core_dir, shell=True)
    shutil.rmtree(core_dir)

    shutil.copy2(os.path.join(cwd, "custom.css"), desktop_core_dir)

if __name__ == "__main__":
    main()
