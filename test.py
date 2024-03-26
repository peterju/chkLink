import tkinter as tk


def open_message_window():
    global top
    top = tk.Toplevel(root)
    top.title("訊息視窗")
    message_label = tk.Label(top, text="這是一則訊息")
    message_label.pack(padx=20, pady=20)

    # 監聽視窗關閉事件
    def close_window():
        top.destroy()

    top.protocol("WM_DELETE_WINDOW", close_window)


def close_message_window():
    if 'top' in globals() and top.winfo_exists():
        top.destroy()


root = tk.Tk()
root.title("主視窗")
open_message_window()

close_button = tk.Button(root, text="關閉訊息", command=close_message_window)
close_button.grid(row=1, column=0, pady=10)


root.mainloop()
