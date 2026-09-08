# ui/caption_window.py

import tkinter as tk


class CaptionWindow:

    def __init__(self):

        self.root = tk.Tk()

        self.root.title("Live Caption")

        self.root.attributes("-topmost", True)

        self.root.configure(
            bg="black"
        )

        self.root.attributes("-alpha", 0.92) # 半透明

        window_width = 1000
        window_height = 120

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = (screen_width - window_width) // 2

        # 距離底部 120px
        y = screen_height - window_height - 120

        self.root.geometry(
            f"{window_width}x{window_height}+{x}+{y}"
        )

        self.english_label = tk.Label(
            self.root,
            text="",
            fg="#DDDDDD",
            bg="black",
            font=("Segoe UI", 18),
            wraplength=850,
            justify="center",
        )

        self.chinese_label = tk.Label(
            self.root,
            text="等待字幕...",
            fg="white",
            bg="black",
            font=("Microsoft JhengHei", 18, "bold"),
            wraplength=850,
            justify="center",
        )

        self.english_label.pack(
            fill="x",
            pady=(5, 0)
        )

        self.chinese_label.pack(
            fill="x",
            pady=(0, 5)
        )

    def update_text(
        self,
        english_text,
        chinese_text,
        chinese_color="white"
    ):

        self.root.after(
            0,
            lambda: (
                self.english_label.config(
                    text=english_text
                ),
                self.chinese_label.config(
                    text=chinese_text,
                    fg=chinese_color
                )
            )
        )

    def run(self):

        self.root.mainloop()