import os
import shutil
import tkinter as tk
from tkinter import messagebox
from threading import Thread
import sys
import subprocess

# --- Util Functions ---

def save_log(folder_path, moved_files):
    log_path = os.path.join(folder_path, "moved_files.txt")
    with open(log_path, 'w', encoding='utf-8') as log:
        for original, moved in moved_files.items():
            log.write(f"{original} -> {moved}\n")

def load_log(folder_path):
    log_path = os.path.join(folder_path, "moved_files.txt")
    if not os.path.exists(log_path):
        return {}
    moved_files = {}
    with open(log_path, 'r', encoding='utf-8') as log:
        for line in log:
            original, moved = line.strip().split("->")
            moved_files[original.strip()] = moved.strip()
    return moved_files

def remove_log(folder_path):
    try:
        os.remove(os.path.join(folder_path, "moved_files.txt"))
    except FileNotFoundError:
        pass

# --- Core Functions ---

def move_files_up(folder_path, base_path):
    moved_files = {}
    for item in os.listdir(folder_path):
        full_item_path = os.path.join(folder_path, item)

        if os.path.isfile(full_item_path):
            target_path = os.path.join(base_path, item)
            if os.path.exists(target_path):
                base, ext = os.path.splitext(item)
                counter = 1
                while os.path.exists(os.path.join(base_path, f"{base}_copy{counter}{ext}")):
                    counter += 1
                target_path = os.path.join(base_path, f"{base}_copy{counter}{ext}")

            shutil.move(full_item_path, target_path)
            moved_files[full_item_path] = target_path

        elif os.path.isdir(full_item_path):
            answer = messagebox.askyesno(
                "Subfolder detected",
                f"Folder '{item}' found inside '{os.path.basename(folder_path)}'.\n"
                "Move its contents all the way to the program directory?"
            )
            if answer:
                moved_files.update(move_files_up(full_item_path, base_path))

    if moved_files:
        save_log(folder_path, moved_files)

    return moved_files

def restore_files(folder_path):
    moved_files = load_log(folder_path)
    for original, moved in moved_files.items():
        if os.path.exists(moved):
            original_dir = os.path.dirname(original)
            if not os.path.exists(original_dir):
                os.makedirs(original_dir)
            shutil.move(moved, original)
    remove_log(folder_path)

def restore_all(base_dir):
    for item in os.listdir(base_dir):
        item_path = os.path.join(base_dir, item)
        if os.path.isdir(item_path):
            restore_files(item_path)

def restart_program(root):
    """Restart the current program and close the existing window."""
    root.destroy()  # Close the current window
    python = sys.executable
    subprocess.run([python, __file__])
    sys.exit()

# --- GUI and threading ---

def on_folder_click(event):
    try:
        selected = folder_list.get(folder_list.curselection())
    except tk.TclError:
        return

    folder_path = os.path.join(base_dir, selected)
    if not os.path.isdir(folder_path):
        messagebox.showerror("Error", f"'{selected}' is not a folder.")
        return

    def move_thread():
        move_files_up(folder_path, base_dir)
        messagebox.showinfo("Done", f"Files from '{selected}' moved to parent directory.")
        refresh_folder_list()

    Thread(target=move_thread).start()

def refresh_folder_list():
    folder_list.delete(0, tk.END)
    for item in os.listdir(base_dir):
        if os.path.isdir(os.path.join(base_dir, item)):
            folder_list.insert(tk.END, item)

# --- Main program ---

base_dir = os.path.dirname(os.path.abspath(__file__))

root = tk.Tk()
root.title("Folder Unfolder")
root.geometry("450x650")
root.configure(bg="#f5f5f5")

# Title
title_label = tk.Label(
    root, 
    text="📁 Folder Unfolder",
    font=("Segoe UI", 20, "bold"),
    fg="#444444",
    bg="#f5f5f5",
    padx=10,
    pady=10
)
title_label.pack()

# Instruction
instruction_label = tk.Label(
    root, 
    text="Double-click a folder to move its files to the program directory:",
    font=("Segoe UI", 12),
    fg="#666666",
    bg="#f5f5f5",
    padx=10,
    pady=5
)
instruction_label.pack()

# Folder List
folder_list = tk.Listbox(root, width=50, height=20, font=("Segoe UI", 11), bg="#ffffff", bd=0, selectbackground="#d1e7dd", highlightthickness=0)
folder_list.pack(pady=15, padx=15)
folder_list.bind("<Double-1>", on_folder_click)

# Refresh Button
refresh_btn = tk.Button(
    root, 
    text="🔄 Refresh Folder List", 
    command=refresh_folder_list,
    font=("Segoe UI", 12, "bold"),
    fg="#ffffff",
    bg="#198754",
    bd=0,
    padx=15,
    pady=8,
    activebackground="#145c32",
    activeforeground="#ffffff",
    relief="flat",
    cursor="hand2"
)
refresh_btn.pack(pady=10)

# Restart Button
restart_btn = tk.Button(
    root, 
    text="🔁 Refolder files", 
    command=lambda: restart_program(root),
    font=("Segoe UI", 12, "bold"),
    fg="#ffffff",
    bg="#dc3545",
    bd=0,
    padx=15,
    pady=8,
    activebackground="#b02a37",
    activeforeground="#ffffff",
    relief="flat",
    cursor="hand2"
)
restart_btn.pack(pady=5)

refresh_folder_list()

# On startup restore all files to original folders (non-blocking)
Thread(target=restore_all, args=(base_dir,), daemon=True).start()

root.mainloop()
