import tkinter as tk

class CustomDropdown:
    def __init__(self, parent, x, y, width, options):
        self.parent = parent
        self.options = options
        self.selected = tk.StringVar(value="Select")

        # Rectangle (Entry look)
        self.entry = tk.Label(parent, textvariable=self.selected, bd=1, relief="solid", anchor="w")
        self.entry.place(x=x, y=y, width=width, height=30)

        # Button
        self.button = tk.Button(parent, text="▼", command=self.toggle_menu, bd=1, relief="solid")
        self.button.place(x=x+width-30, y=y, width=30, height=30)

        # Dropdown menu (hidden by default)
        self.menu_frame = None

    def toggle_menu(self):
        if self.menu_frame:
            self.menu_frame.destroy()
            self.menu_frame = None
        else:
            self.menu_frame = tk.Frame(self.parent, bd=1, relief="solid")
            self.menu_frame.place(x=self.entry.winfo_x(), y=self.entry.winfo_y()+30, width=self.entry.winfo_width())

            for option in self.options:
                b = tk.Button(self.menu_frame, text=option, anchor="w", relief="flat",
                              command=lambda opt=option: self.select_option(opt))
                b.pack(fill="x")

    def select_option(self, option):
        self.selected.set(option)
        self.toggle_menu()

# Example usage
root = tk.Tk()
root.geometry("400x300")

dropdown = CustomDropdown(root, x=100, y=100, width=200, options=["Option 1", "Option 2", "Option 3"])

root.mainloop()
