#! /usr/bin/env python

from Tkinter import *
from ttk import *
import FileDialog
from collections import OrderedDict

from backend import settings




class Gui(object):
    def __init__(self, root):
        self.root = root
        self.master = Frame(root, name='master') # create Frame in "root"
        self.filename = None

        root.title('Python Wizard') # title for top-level window
        # quit if the window is deleted
        root.protocol("WM_DELETE_WINDOW", self.quit)
        self.graph_frame = self._make_graphs()
        self.settings_frame = self._make_settings()
        self.table_frame = self._make_table()
        self.menu = self._make_menus()
        root.option_add('*tearOff', FALSE)

    def quit(self):
        self.master.quit()
     
    def _file_open(self):
        dlg = FileDialog.LoadFileDialog(self.master)
        self.filename = dlg.go(pattern="*.wav")
        self.run = True


    def _make_menus(self):
        menubar = Menu(self.master)
        self.root['menu'] = menubar
        
        menu_file = Menu(menubar)
        menubar.add_cascade(menu=menu_file, label="File")

        menu_file.add_command(label="Open WAV", command=self._file_open)
        menu_file.add_command(label="Quit", command=self.quit)

        return menubar

    def _make_graphs(self):
        graphs = Frame(self.root)

        #graph_original_img = Image.fromarray(arr)
        #graph_original = = ImageTk.PhotoImage(graph_original_img)

        return graphs

    def _make_settings(self):
        settings_vars = {}
        self.settings_widgets = {}
        settings_frame = Frame(self.root)
        raw_settings = settings.export_to_odict()
        self.raw_settings = raw_settings
        row = 1
        col = 1
        rows = 6
        var = {}
        for key in raw_settings:
            Label(settings_frame, text=key).grid(row=row,column=col)

            v = None
            typ = type(raw_settings[key]) 
            if typ is float:
                v=DoubleVar()
            elif typ is int:
                v=IntVar()
            elif typ is bool:
                v=IntVar()
            else:
                v=StringVar()
            v.set(raw_settings[key])
            if typ is not bool:
                e = Entry(settings_frame, textvar=v)
            else:
                e = Checkbutton(settings_frame, variable=v)

            e.grid(row=row,column=col+1)
            self.settings_widgets[key] = e

            settings_vars[key] = v
            settings_vars[key].set(raw_settings[key])
            row += 1
            if (row>rows):
                col += 2 
                row = 1

        self.settings_vars = settings_vars
        settings_frame.pack()
        return settings_frame

    def _get_data(self):
        to_import = OrderedDict()
        for key in self.raw_settings:
            try:
                to_import[key] = self.settings_vars[key].get()
            except ValueError:
                self.settings_widgets[key].configure(background='red')
                return None

        return to_import

    def check_change(self):
        new_cfg = self._get_data()
        if new_cfg is None:
            return

        raw_settings = settings.export_to_odict()
        
        if new_cfg != raw_settings:
            for k in raw_settings:
                if new_cfg[k] != raw_settings[k]:
                    print k, raw_settings[k], new_cfg[k]
            errors = settings.import_from_dict(new_cfg)
            if errors is None:
                # TODO Recalculate
                if self.filename is not None:
                    self.run = True
            else:
                # Mark wrong input fiels appropriately
                for e in errors:
                    self.settings_widgets[e].configure(background='red')
                pass

    def _make_table(self, data=None):
        table=Frame(self.root)
        table_data=Frame(table)
        table_scrollbar=Scrollbar(table, orient="vertical")
        #table_data.grid(row=1, column=1)
        #table_scrollbar.grid(row=1, column=2)
        table.pack(side="left")

        d=( ( Label(table, text="A"), Label(table, text="B"), Label(table, text="C") ),
          ( Label(table, text="1"), Label(table, text="2"), Label(table, text="3") ) )

        for row in range(len(d)):
            for col in range(len(d[row])):
                d[row][col].grid(row=row, column=col)

        table.pack()
        return table

    def _repeatedly(self):
        self.root.after(500, self._repeatedly)
        self.check_change()
        print "Hi!"

    def mainloop(self):
        self.root.after(500, self._repeatedly)
        self.master.mainloop()

# start the app
root = Tk() # create a top-level window
gui = Gui(root)
if __name__ == "__main__":
    gui.mainloop() # call master's Frame.mainloop() method.
    #root.destroy() # if mainloop quits, destroy window
