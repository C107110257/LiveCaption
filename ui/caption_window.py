import tkinter as tk
from tkinter import messagebox

from config.settings import (
    WINDOW_ALPHA,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_BOTTOM_MARGIN,
    WRAP_LENGTH,
    BG_COLOR,
    ENGLISH_TEXT_COLOR,
    CHINESE_DEFAULT_COLOR,
    ENGLISH_FONT_FAMILY,
    CHINESE_FONT_FAMILY,
    FONT_SIZE,
    PLACEHOLDER_TEXT,
    AUTHOR_NAME,
    AUTHOR_CONTACT,
    APP_VERSION
)


TOOLBAR_HEIGHT = 18  # 頂部工具列高度,滑桿放在這裡,跟字幕分開


class CaptionWindow:

    def __init__(self):

        self.root = tk.Tk()
        self.root.title("English Live Caption")
        self.root.attributes("-topmost", True)
        self.root.configure(bg=BG_COLOR)

        self.current_alpha = WINDOW_ALPHA
        self.root.attributes("-alpha", self.current_alpha)

        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        x = (self.screen_width - WINDOW_WIDTH) // 2
        y = self.screen_height - WINDOW_HEIGHT - WINDOW_BOTTOM_MARGIN

        self.min_height = WINDOW_HEIGHT
        self.max_height = 300

        self.root.geometry(
            f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}"
        )

        # ---- 頂部工具列:專門放滑桿,跟字幕內容分開,不會互相重疊 ----
        self.toolbar = tk.Frame(
            self.root,
            bg=BG_COLOR,
            height=TOOLBAR_HEIGHT,
        )
        self.toolbar.pack(fill="x", side="top")
        self.toolbar.pack_propagate(False)  # 防止 Frame 被裡面的元件撐縮


        # 用 grid 取代 pack,方便精準控制對齊
        self.toolbar.grid_columnconfigure(1, weight=1)  # 左邊留白,把內容推到右邊
        self.toolbar.grid_rowconfigure(0, weight=1)      # 讓整列垂直置中

        # about 按鈕:靠左
        self.about_button = tk.Label(
            self.toolbar,
            text="ⓘ",
            fg="#888888",
            bg=BG_COLOR,
            font=(ENGLISH_FONT_FAMILY, 12),
            cursor="hand2",
        )
        self.about_button.grid(row=0, column=0, padx=(8, 0), sticky="w")
        self.about_button.bind("<Button-1>", lambda e: self._show_about())
        self.about_button.bind("<Enter>", lambda e: self.about_button.config(fg="#DDDDDD"))
        self.about_button.bind("<Leave>", lambda e: self.about_button.config(fg="#888888"))

        self.alpha_label = tk.Label(
                    self.toolbar,
                    text="透明度",
                    fg="#CECECE",
                    bg=BG_COLOR,
                    font=(CHINESE_FONT_FAMILY, 12),
                )
        self.alpha_label.grid(row=0, column=1, padx=(0, 4), sticky="e")
        
        self.alpha_slider = tk.Scale(
            self.toolbar,
            from_=0.2,
            to=1.0,
            resolution=0.05,
            orient="horizontal",
            length=100,
            width=12,
            showvalue=False,
            bg="#5DADE2",
            fg=ENGLISH_TEXT_COLOR,
            troughcolor="#333333",
            activebackground="#85C1E9",
            highlightthickness=0,
            border=1,
            command=self._on_alpha_change,
        )
        self.alpha_slider.set(self.current_alpha)
        self.alpha_slider.grid(row=0, column=2, padx=(0, 10), sticky="e")

        
        # ---- 字幕文字:放在工具列下方 ----
        self.english_label = tk.Label(
            self.root,
            text="",
            fg=ENGLISH_TEXT_COLOR,
            bg=BG_COLOR,
            font=(ENGLISH_FONT_FAMILY, FONT_SIZE),
            wraplength=WRAP_LENGTH,
            justify="center",
        )

        self.chinese_label = tk.Label(
            self.root,
            text=PLACEHOLDER_TEXT,
            fg=CHINESE_DEFAULT_COLOR,
            bg=BG_COLOR,
            font=(CHINESE_FONT_FAMILY, FONT_SIZE, "bold"),
            wraplength=WRAP_LENGTH,
            justify="center",
        )

        self.english_label.pack(fill="x", pady=(5, 0))
        self.chinese_label.pack(fill="x", pady=(0, 5))

    def _show_about(self):
        lines = ["Live Caption (English only)"]
        if APP_VERSION:
            lines.append(f"版本: {APP_VERSION}")
        if AUTHOR_NAME:
            lines.append(f"作者: {AUTHOR_NAME}")
        if AUTHOR_CONTACT:
            lines.append(f"聯絡方式: {AUTHOR_CONTACT}")

        messagebox.showinfo("關於", "\n".join(lines))

    def _on_alpha_change(self, value):
        alpha = float(value)
        self.current_alpha = alpha
        self.root.attributes("-alpha", alpha)

    def _resize_to_fit_content(self):
        """依目前文字實際佔用的高度,重新調整視窗高度,只改高度,不動使用者手動調整過的位置"""
        self.root.update_idletasks()

        content_height = (
            TOOLBAR_HEIGHT
            + self.english_label.winfo_reqheight()
            + self.chinese_label.winfo_reqheight()
            + 15
        )

        new_height = max(self.min_height, min(content_height, self.max_height))

        current_x = self.root.winfo_x()
        current_y = self.root.winfo_y()
        current_height = self.root.winfo_height()

        height_diff = new_height - current_height
        new_y = current_y - height_diff

        self.root.geometry(f"{WINDOW_WIDTH}x{new_height}+{current_x}+{new_y}")

    def update_text(
        self,
        english_text,
        chinese_text,
        chinese_color=CHINESE_DEFAULT_COLOR
    ):

        def _update():
            self.english_label.config(text=english_text)
            self.chinese_label.config(text=chinese_text, fg=chinese_color)
            self._resize_to_fit_content()

        self.root.after(0, _update)

    def run(self):
        self.root.mainloop()