from DB import DataBase
from tkinter import END, ACTIVE
from copy import copy
from PIL import ImageTk, Image
from sqlite3 import IntegrityError
from Tagger import Tagger
from collections.abc import Iterable


class Intermediary:

    def __init__(self, ui):

        self.ui = ui
        self.any = True
        self.queue = None
        self.curr_img = 0

    def confirmed(self, event):

        #Listbox items
        tags = self.ui.builder.get_object("ListSelected").get(0, END)
#       Unique images' ids
        res = set()
        for tg in tags:
            ids = DataBase.get_tagged_items(tg)
            #TODO maybe sth better if nth found
            if len(ids) < 1:
                return
#           Add else intersection
            if self.any:
                res |= set(ids)
            else:
                res &= set(ids)

        lt = list()
        for r in res:
            lt.append(DataBase.get_path(r))
        self.queue_images(lt)

    def clear(self, event):
        """Clears tags listbox"""

        #Listbox clearing
        self.ui.builder.get_object("ListSelected").delete(0, END)
        #TODO remove - testing feature
        self.show_image("")

    def list_tag(self, event):
        """Add tag to listbox ListSelected"""

        eadd = self.ui.builder.get_object("EAdd")
        val = eadd.get()
        eadd.delete(0, END)

        self.ui.builder.get_object("ListSelected").insert(END, val)

    def remove_tag(self, event):
        """Remove tag from listbox ListSelected"""

        event.widget.delete(ACTIVE)

    def rany(self, event):
        """Changes search method"""

        var = self.ui.builder.get_variable("VarAny").get()
        if var != "Any":
            self.any = True
        else:
            self.any = False

    def queue_images(self, ids):
        """Queue images to display"""

#       Converting to list from different types of arguments
        if isinstance(ids, str):
            ids = [ids]
        elif isinstance(ids, Iterable):
            ids = list(ids)

        self.queue = copy(ids)
        self.curr_img = 0
        self.list_queue()
        self.show_image()

    def show_image(self, pth=None):
        """
        Display image, if no argument is present get from queue. Called automatically when queue changes
        :arg pth: Path to image
        """

#       Next image from queue
        if pth is None:
            pth = self.queue[self.curr_img]
            self.curr_img += 1
            self.curr_img %= len(self.queue)
        else:
            self.queue_images(list(pth))

#       Wrong path
        if pth is None:
            return

#       Prepare image
        img = Image.open(pth)

        if img.width > 800 or img.height > 450:
            factor = min(800/img.width, 450/img.height)
            img = img.resize((int(img.width*factor), int(img.height*factor)))

        img = ImageTk.PhotoImage(img)

#       Display image
        label = self.ui.builder.get_object("LImage")
        label.config(image=img)
        label.image = img

#       List tags
        self.list_image_tags()

    def list_queue(self):
        """Called by queue_images. Lists queued paths in ListResults listbox"""

        lb = self.ui.builder.get_object("ListResults")
        self.clear_results()
        for pth in self.queue:
            lb.insert(END, pth.split(sep="\\")[-1])

    def list_image_tags(self):
        """Called by show image. Adds current tags to ListTags listbox"""

        tags = DataBase.get_image_tags(pth=self.queue[self.curr_img])
        lt = self.ui.builder.get_object("ListTags")
        self.clear_tags()
        for tag in tags:
            lt.insert(END, tag)

    def clear_results(self):

        self.ui.builder.get_object("ListResults").delete(0, END)

    def clear_tags(self):

        self.ui.builder.get_object("ListTags").delete(0, END)

    def file_input(self, event):
        """Handle request for new input file. If new tag and display else display"""

        self.clear_results()
        pth = event.widget.cget("path")
        new = True
#       SQL exception if path is not unique
        try:
            DataBase.add_image(pth)
        except IntegrityError:
            new = False

#       Tag new
        if new:
            tags = Tagger.tag_file(pth)
            for tag in tags:
                DataBase.tag_image(tag, pth=pth)

#       Display
        self.queue_images(pth)

