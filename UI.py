import pygubu
import tkinter as tk
import Intermediary


class UI(pygubu.TkApplication):

    def _create_ui(self):

        #pygubu builder
        self.builder = pygubu.Builder()
        #Load an ui file
        self.builder.add_from_file("UI.ui")

        self.intermediary = Intermediary.Intermediary(self)
        self.mainframe = self.builder.get_object("FrameMain")
        self.set_title("Ryśnik, Muravytskyi ; JPWP")

        self.builder.get_object("LImage").config(anchor="center")

        #GUI event handling
        self.add_listeners()

    def run(self):

        self.mainframe.mainloop()

    def add_listeners(self):
        """Bind events"""

        confirm = self.builder.get_object("BConfirm")
        confirm.bind("<Button-1>", self.intermediary.confirmed)

        clear = self.builder.get_object("BClear")
        clear.bind("<Button-1>", self.intermediary.clear)

        eadd = self.builder.get_object("EAdd")
        eadd.bind("<Return>", self.intermediary.list_tag)

        badd = self.builder.get_object("BAdd")
        badd.bind("<Button-1>", self.intermediary.list_tag)

        lb = self.builder.get_object("ListSelected")
        lb.bind("<Double-Button-1>", self.intermediary.remove_tag)

        radio_any = self.builder.get_object("RAny")
        radio_any.bind("<Button-1>", self.intermediary.rany)

        radio_all = self.builder.get_object("RAll")
        radio_all.bind("<Button-1>", self.intermediary.rany)

        file_input = self.builder.get_object("PathInput")
        file_input.bind("<<PathChooserPathChanged>>", self.intermediary.file_input)


if __name__ == "__main__":

    root = tk.Tk()
    ui = UI(root)
    ui.run()
