import hashlib
import pprint
import random
import tkinter as tk
import tomllib
from pathlib import Path
from tkinter import filedialog, font
from PIL import Image, ImageTk

from doslib.dos_utils import resolve_path
from randomizer.flags import Flags
from randomizer.randomize import randomize


def browse_file():
    global rom_full_path

    filename = filedialog.askopenfilename(
        filetypes=[("GBA ROM File", "*.gba"), ("All files", "*.*")]
    )
    rom_full_path = filename
    rom_filename.set(Path(filename).name)
    randomize_button["state"] = tk.NORMAL
    root.focus_set()


def add_option(parent: tk.Widget, option_text: str, init_value: bool = True) -> tk.BooleanVar:
    check_var = tk.BooleanVar(value=init_value)
    tk.Checkbutton(parent, text=option_text, anchor="w", variable=check_var).pack(anchor='w', fill="x")
    return check_var


def pick_new_seed():
    title = random.choice(seed_data["titles"])
    prefix = random.choice(seed_data["prefixes"])
    creature = random.choice(seed_data["creatures"])
    check_seed(f"{title} {prefix} {creature}")


def check_seed(seed: str):
    digest = hashlib.sha256(bytearray(seed, encoding="utf-8")).hexdigest()
    hex_seed_var.set(f"Encoded: {digest[0:10]}")
    seed_value.set(seed)
    return True


def randomize_rom():
    if rom_full_path is None:
        # This shouldn't happen since the button should be disabled,
        # but if it does, just ignore it
        return

    flags = Flags()
    flags.no_shuffle = not progression.get()
    flags.standard_shops = not shops.get()
    flags.standard_treasure = not treasure.get()
    flags.default_start_gear = not gear.get()
    flags.boss_shuffle = fiends.get()
    flags.new_items = shops.get()
    flags.fiend_ribbons = ribbons.get()

    flags.scale_levels = exp_scale_var.get() / 100.0

    with open(rom_full_path, "rb") as rom_file:
        rom_data = bytearray(rom_file.read())

    base_name = rom_file.name.replace(".gba", "")
    rom_seed = hex_seed_var.get()[len("Encoded: "):]
    randomized_rom = randomize(rom_data, rom_seed, flags)

    output_name = f"{base_name}_{flags.encode()}_{rom_seed}.gba"
    with open(output_name, "wb") as output:
        output.write(randomized_rom)


# Initialize the main window
root = tk.Tk()

# Variables used in the UI
hex_seed_var = tk.StringVar(value="")
rom_filename = tk.StringVar(value="No ROM selected")

# Load the image using Pillow
image = Image.open(resolve_path("static/ff.png"))
photo = ImageTk.PhotoImage(image=image)

root.title("Final Fantasy: HMS Jayne")
root.wm_iconphoto(False, photo)
root.configure(bg="white", padx=10, pady=10)
root.option_add("*background", "white")

# Load the image using Pillow
image = Image.open(resolve_path("static/hmslogo.jpg"))
image = image.reduce(factor=5)
photo = ImageTk.PhotoImage(image=image)

# Create a label to display the image
image_label = tk.Label(root, image=photo)
image_label.pack(anchor='w', pady=10)

# ROM + core options first
rom_frame = tk.LabelFrame(root, text="Settings")
rom_frame.columnconfigure(0, weight=1)
rom_frame.columnconfigure(1, weight=1)

rom_full_path: str | None = None
rom_label = tk.Label(rom_frame, textvariable=rom_filename, font=("Courier", 12), anchor="w")
file_button = tk.Button(rom_frame, text="Select ROM", command=browse_file, highlightbackground="white")
randomize_button = tk.Button(rom_frame, text="Randomize", command=randomize_rom, background="white",
                             highlightbackground="white", state=tk.DISABLED)

rom_label.grid(row=0, column=0, sticky="ew", padx=(10, 10), pady=(3, 3))
file_button.grid(row=0, column=1, sticky="e", padx=(10, 10), pady=(3, 3))
randomize_button.grid(row=1, column=1, sticky="e", padx=(10, 10), pady=(3, 3))

seed_label = tk.Label(rom_frame, text="Seed")

seed_frame = tk.Frame(rom_frame, bg="blue")
new_seed = tk.Button(seed_frame, text="↻", command=pick_new_seed, highlightbackground="white")

seed_value = tk.StringVar()
validate_seed = root.register(check_seed)
seed_text = tk.Entry(seed_frame, validate="key", textvariable=seed_value, validatecommand=(validate_seed, "%P"))
new_seed.pack(anchor="w", side="left")
seed_text.pack(side="left", fill="x", expand=1)

hex_seed_label = tk.Label(rom_frame, textvariable=hex_seed_var, anchor="w")
check_seed("")

seed_label.grid(row=1, column=0, sticky="w", padx=(10, 10), pady=(3, 3))
seed_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=(10, 10), pady=(3, 3))
hex_seed_label.grid(row=3, column=0, sticky="we", padx=(10, 10), pady=(3, 3))

rom_frame.pack(anchor='w', fill="x")

exp_scale_var = tk.IntVar()
exp_scale_var.set(150)
exp_scale = tk.Scale(root, variable=exp_scale_var, from_=50, to=500, resolution=25, orient=tk.HORIZONTAL)
exp_scale.pack(anchor='w', pady=(0, 10))

options_frame = tk.LabelFrame(root, text='Options')

progression = add_option(options_frame, "Shuffle key items")
shops = add_option(options_frame, "Random shops (item, weapon, armor, or magic shops)")
treasure = add_option(options_frame, "Random treasure chests")
gear = add_option(options_frame, "Random starting gear")
fiends = add_option(options_frame, "Random fiend fights")
ribbons = add_option(options_frame, "Fiend 1s always drop a ribbon")

options_frame.pack(anchor='w', fill="x")

with open(resolve_path("static/seed_data.toml"), "rb") as seed_data_file:
    seed_data = tomllib.load(seed_data_file)

pick_new_seed()

# Start the GUI event loop
root.mainloop()
