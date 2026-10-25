import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

from doslib.dos_utils import resolve_path
from randomizer.api import randomize_rom as run_randomizer
from randomizer.options import RandomizerOptions
from randomizer.seed import generate_seed, normalize_seed, seed_checksum
from randomizer.share import build_filename


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
    check_seed(generate_seed())


def check_seed(seed: str):
    try:
        normalized = normalize_seed(seed)
        hex_seed_var.set(f"Checksum: {seed_checksum(normalized)}")
        seed_value.set(normalized)
    except ValueError:
        hex_seed_var.set("Invalid seed (1-32 printable ASCII characters)")
    return True


def randomize_rom():
    if rom_full_path is None:
        # This shouldn't happen since the button should be disabled,
        # but if it does, just ignore it
        return

    try:
        rom_seed = normalize_seed(seed_value.get())
    except ValueError as exc:
        messagebox.showerror("Invalid seed", str(exc))
        return

    options = RandomizerOptions(
        shuffle_key_items=progression.get(),
        randomize_shops=shops.get(),
        randomize_treasure=treasure.get(),
        randomize_starting_gear=gear.get(),
        randomize_bosses=fiends.get(),
        new_item_distribution=new_items.get(),
        fiend_ribbons=ribbons.get(),
        xp_rate_percent=exp_scale_var.get(),
    )

    with open(rom_full_path, "rb") as rom_file:
        rom_data = bytearray(rom_file.read())

    base_path = Path(rom_full_path)
    result = run_randomizer(rom_data, rom_seed, options)
    output_name = base_path.parent / build_filename(
        rom_seed, options, base_name=base_path.stem, extension="gba"
    )
    output_name.write_bytes(result.rom_data)


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

seed_label.grid(row=1, column=0, sticky="w", padx=(10, 10), pady=(3, 3))
seed_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=(10, 10), pady=(3, 3))
hex_seed_label.grid(row=3, column=0, sticky="we", padx=(10, 10), pady=(3, 3))

rom_frame.pack(anchor='w', fill="x")

options_frame = tk.LabelFrame(root, text='Options')

# XP Scaling UI
exp_scale_frame = tk.Frame(options_frame)
exp_scale_frame.pack(fill="x", padx=5, pady=5)

exp_scale_var = tk.IntVar(value=150)
exp_label_var = tk.StringVar()


def update_exp_label(val):
    exp_label_var.set(f"Level-up speed: {val}% of normal")


update_exp_label(exp_scale_var.get())

exp_label = tk.Label(exp_scale_frame, textvariable=exp_label_var, width=30, anchor="w")
exp_label.pack(side=tk.LEFT, padx=(0, 10))

exp_scale = tk.Scale(exp_scale_frame, variable=exp_scale_var, from_=50, to=500, resolution=10,
                     orient=tk.HORIZONTAL, showvalue=False, command=update_exp_label)
exp_scale.pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))

progression = add_option(options_frame, "Shuffle key items")
shops = add_option(options_frame, "Random shops (item, weapon, armor, or magic shops)")
treasure = add_option(options_frame, "Random treasure chests")
gear = add_option(options_frame, "Random starting gear")
fiends = add_option(options_frame, "Random fiend fights")
new_items = add_option(options_frame, "New item distribution (experimental)", False)
ribbons = add_option(options_frame, "Fiend 1s always drop a ribbon", False)

options_frame.pack(anchor='w', fill="x")

pick_new_seed()

# Start the GUI event loop
root.mainloop()
