from DB import DataBase
from tkinter import END, ACTIVE, filedialog
from copy import copy
from PIL import ImageTk, Image
from sqlite3 import IntegrityError
from Tagger import Tagger
from collections.abc import Iterable
from os.path import isdir, join
from threading import Thread


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
        self.curr_img = -1
        self.list_queue()
        self.show_image()

    def show_image(self, pth=None):
        """
        Display image, if no argument is present get from queue. Called automatically when queue changes
        :arg pth: Path to image
        """

#       Next image from queue
        if pth is None:
            self.curr_img += 1
            self.curr_img %= len(self.queue)
            pth = self.queue[self.curr_img]
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

#       Mark current image in listbox
        lb = self.ui.builder.get_object("ListResults")
        lb.selection_clear(0, END)
        lb.selection_set(self.curr_img)

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

    def path_input(self, pth):
        """Handle request for new input file. If new tag and display else display"""

        self.clear_results()
        tfiles = None

#       Single image path
        if not isdir(pth):
            new = True
#           SQL exception if path is not unique
            try:
                DataBase.add_image(pth)
            except IntegrityError:
                new = False

#          Tag new
            if new:
                tags = Tagger.tag_file(pth)
                for tag in tags:
                    DataBase.tag_image(tag, pth=pth)
#       Directory path
        else:
            tags, tfiles = Tagger.tag_dir(pth)
            for i in range(len(tfiles)):
                f = tfiles[i]
#               Full path to image
                fpth = join(pth, f)
                tfiles[i] = fpth
#               Continue if already present
                if DataBase.exists(pth=fpth):
                    continue
                else:
                    DataBase.add_image(fpth)
#                   Tuple results
                    if not isinstance(tags[i], str):
                        for t in tags[i]:
                            DataBase.tag_image(t, pth=fpth)
#                   String result
                    else:
                        DataBase.tag_image(tags[i], pth=fpth)

        L = 1
#       Display
        if tfiles is None:
            self.queue_images(pth)
        else:
            #Number of listbox for results length
            L = len(tfiles)
            nlb = max(3, L)
            nlb = min(nlb, 12)
            self.ui.builder.get_object("ListResults").config(height=nlb)

            self.queue_images(tfiles)

        self.update_info("Processed " + str(L) + " images")

    def choose_dir(self, event):

        directory = filedialog.askdirectory()
        self.path_input(directory)

    def choose_file(self, event):

        file = filedialog.askopenfilename(title="Select file", filetypes=(("jpeg files", "*.jpg"),
                                                                          ("jpeg files", "*.jpeg")))
        self.path_input(file)

    def next_image(self, event):

        self.show_image()

    def prev_image(self, event):

        self.curr_img -= 2
        if self.curr_img < 0:
            self.curr_img = -1
        self.show_image()

    def listbox_image(self, event):

        idx = event.widget.index(ACTIVE)
        self.curr_img = idx - 1
        self.show_image()

    def update_info(self, info=" "):

        linfo = self.ui.builder.get_object("LInfo")
        linfo.configure(text=info)
