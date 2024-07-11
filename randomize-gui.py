import tkinter as tk
from tkinter import filedialog, font
from PIL import Image, ImageTk

from doslib.dos_utils import resolve_path


def browse_file():
    filename = filedialog.askopenfilename(
        filetypes=[("GBA ROM File", "*.gba"), ("All files", "*.*")]
    )
    if filename:
        file_label.config(text=f"Selected file: {filename}")


def check_seed(seed: str):
    print(f"Seed: {seed}")
    return True


def randomize():
    print("Let's randomize things!")


# Initialize the main window
root = tk.Tk()
root.title("Simple GUI")
root.configure(background='white', padx=10, pady=10)

# Load the image using Pillow
image = Image.open(resolve_path("static/hmslogo.jpg"))
image = image.reduce(factor=4)
photo = ImageTk.PhotoImage(image=image)

# Create a label to display the image
image_label = tk.Label(root, image=photo, background="white")
image_label.pack(anchor='w', pady=10)

# Create a label to display selected file
file_label = tk.Label(root, text="No file selected", background="white")
file_label.pack(anchor='w', pady=10)

# Create a button to open file dialog
file_button = tk.Button(root, text="Browse File", command=browse_file, background="white", highlightbackground="white")
file_button.pack(anchor='w')

seed_label = tk.Label(root, text="Seed", background="white", font=("Courier", 24))
seed_label.pack(anchor='w', pady=(10, 0))

validate_seed = root.register(check_seed)
seed_text = tk.Entry(root, background="white", validate="key", validatecommand=(validate_seed, "%P"))
seed_text.pack(anchor='w', pady=(0, 10))

scale = tk.IntVar()
exp_scale = tk.Scale(root, variable=scale, from_=50, to=500, resolution=25, orient=tk.HORIZONTAL)
exp_scale.pack(anchor='w', pady=(0, 10))

# Create checkboxes
var1 = tk.IntVar()
var2 = tk.IntVar()

checkbox1 = tk.Checkbutton(root, text="Option 1", variable=var1, background="white")
checkbox1.pack(anchor='w')

checkbox2 = tk.Checkbutton(root, text="Option 2", variable=var2, background="white")
checkbox2.pack(anchor='w')

randomize_button = tk.Button(root, text="Randomize", command=randomize, background="white",
                             highlightbackground="white")
randomize_button.pack(anchor='w')

fonts = list(font.families())
fonts.sort()
for font in fonts:
    print(f"Font: {font}")

# Start the GUI event loop
root.mainloop()
