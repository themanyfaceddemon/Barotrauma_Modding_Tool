import logging
import traceback
from tkinter import Button, Frame, Label, Scrollbar, Text, Tk, messagebox
from tkinter.constants import BOTH, LEFT, RIGHT, Y


def setup_clipboard(text: str):
    import pyperclip

    try:
        pyperclip.copy(text)
        logging.info("Stack trace copied to clipboard.")

    except Exception as e:
        logging.error(f"Failed to copy to clipboard: {e}\nText: {text}")


def show_error_message_with_traceback(title: str, exception: Exception):
    traceback_exception = traceback.TracebackException.from_exception(exception)
    traceback_text = "".join(traceback_exception.format())
    error_type = type(exception).__name__
    error_message = str(exception)

    root = Tk()
    root.title(title)
    root.geometry("600x400")
    root.configure(bg="#f9f9f9")

    Label(
        root,
        text="An error occurred",
        font=("Arial", 16, "bold"),
        bg="#f9f9f9",
        fg="#333",
    ).pack(pady=10)

    Label(
        root, text=f"Type: {error_type}", font=("Arial", 12), bg="#f9f9f9", fg="#555"
    ).pack(pady=5)
    Label(
        root, text="Description:", font=("Arial", 12, "bold"), bg="#f9f9f9", fg="#333"
    ).pack(anchor="w", padx=20)

    frame = Frame(root, bg="#f9f9f9")
    frame.pack(padx=20, pady=10, fill=BOTH, expand=True)

    scrollbar = Scrollbar(frame)
    scrollbar.pack(side=RIGHT, fill=Y)

    text_widget = Text(
        frame,
        height=5,
        wrap="word",
        font=("Arial", 12),
        bg="#fff",
        fg="#333",
        yscrollcommand=scrollbar.set,
        relief="solid",
        bd=1,
    )
    text_widget.insert("1.0", error_message)
    text_widget.config(state="disabled")
    text_widget.pack(side=LEFT, fill=BOTH, expand=True)
    scrollbar.config(command=text_widget.yview)

    Frame(root, height=2, bg="#ccc").pack(fill="x", padx=20, pady=10)

    def on_copy_button_click():
        setup_clipboard(traceback_text)
        messagebox.showinfo("Copied", "Stack trace has been copied to clipboard!")

    button_frame = Frame(root, bg="#f9f9f9")
    button_frame.pack(pady=10)

    Button(
        button_frame,
        text="Copy Stack Trace",
        command=on_copy_button_click,
        font=("Arial", 12),
        bg="#0078D7",
        fg="white",
        activebackground="#005A9E",
        activeforeground="white",
        relief="flat",
        width=20,
    ).pack(side=LEFT, padx=10)

    Button(
        button_frame,
        text="Close",
        command=root.destroy,
        font=("Arial", 12),
        bg="#E81123",
        fg="white",
        activebackground="#C50F1F",
        activeforeground="white",
        relief="flat",
        width=20,
    ).pack(side=LEFT, padx=10)

    root.mainloop()
