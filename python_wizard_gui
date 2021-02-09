from tkinter.ttk import *
from tkinter import *
from tkinter import filedialog, messagebox
import logging
from collections import OrderedDict
try:
        import pyaudio
except ModuleNotFoundError:
        pyaudio = None

#from backend import BitPacker, Processor, Buffer, settings, CodingTable
from pywizard.FrameDataBinaryEncoder import BitPacker
from pywizard.Processor import Processor
from pywizard.Buffer import Buffer
from pywizard.CodingTable import CodingTable
from pywizard.userSettings import settings

class Gui(object):
    NUM_ROWS = 15

    def __init__(self, root):
        self.codingTable = CodingTable(settings.tablesVariant)
        self.root = root
        self.master = Frame(root, name='master') # create Frame in "root"
        self.filename = None
        self.statusbar = Label(root, text="Ready…",bd=1, relief=SUNKEN, anchor=W)
        self.statusbar.pack(side=BOTTOM, fill=X)

        self.output_text = None

        root.title('Python Wizard') # title for top-level window
        # quit if the window is deleted
        root.protocol("WM_DELETE_WINDOW", self.quit)
        self.graph_frame = self._make_graphs()
        self.settings_frame = self._make_settings()
        self.table_frame = self._make_table()
        self.menu = self._make_menus()
        root.option_add('*tearOff', FALSE)

        self.first_line = 0
        self.run = False
        self.frames = []
        self.bytes=0


    def quit(self):
        self.master.quit()

    def _file_open(self):
        self.filename = filedialog.askopenfilename(parent=self.master,filetypes=[('Waves',"*.wav")])
        self.run = True


    def _make_menus(self):
        menubar = Menu(self.master)
        self.root['menu'] = menubar

        menu_file = Menu(menubar)
        menubar.add_cascade(menu=menu_file, label="File")

        menu_file.add_command(label="Open WAV", command=self._file_open)
        menu_file.add_command(label="Quit", command=self.quit)
        
        # menu_play = Menu(menubar)
        # menubar.add_cascade(menu=menu_play,label="Play")
        if pyaudio:
            menubar.add_command(label="Play",command=self.play)
        

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
                    logging.info(f"{k}, {raw_settings[k]}, {new_cfg[k]}")
            errors = settings.import_from_dict(new_cfg)
            if errors is None:
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
        table_scrollbar=Scrollbar(table, orient="vertical",
        command=self._scrolled)
        table_data.grid(row=1, column=1)
        table_scrollbar.grid(row=1, column=2, sticky="NS")

        output_text = Text(table, width=40, height=20)
        output_text.grid(row=1, column=3)
        output_text_scrollbar = Scrollbar(table)
        output_text_scrollbar.grid(row=1, column=4, sticky="NS")
        output_text_scrollbar.config(command=output_text.yview)
        output_text.config(yscrollcommand=output_text_scrollbar.set)
        self.output_text = output_text
        table.pack(side="left")

        # Create header
        parameters = self.codingTable.parameters()
        for (p,col) in zip(parameters, range(len(parameters))):
            p = p[10:]
            Label(table_data, text=p).grid(row=1, column=col+2)
        Label(table_data, text='size').grid(row=1, column=col+1 + 2)
        
        table_vars = {}
        table_labels = {}
        for row in range(self.NUM_ROWS):
            table_labels[row] = StringVar()
            table_labels[row].set(str(row))
            Label(table_data, textvariable=table_labels[row]).grid(row=row+2, column=1,padx=5)
            
            for (p, col) in zip(parameters, range(len(parameters))):
                v = IntVar()
                e = Entry(table_data, width=5, textvariable=v)
                table_vars[ (row, p) ] = v
                e.grid(row=row+2, column=col+2)
            v = IntVar()
            size=Label(table_data,width=5,textvariable=v)
            table_vars[(row, 'size')] = v
            size.grid(row=row+2, column=col+1+2)
        self.table_labels = table_labels
        table.pack()


        print (0, max( [1, self.NUM_ROWS / len(parameters)] ) )
        table_scrollbar.set(0, max( [1, self.NUM_ROWS / len(parameters)] ) )
        self.table_scrollbar = table_scrollbar
        self.table_vars = table_vars

        return table

    def _make_scroll_pos(self):
        frame_count = float(len(self.frames))
        # First line of scrolled data
        scroll_offset = self.first_line / (frame_count+self.NUM_ROWS)
        page_size = float(self.NUM_ROWS) / (frame_count+self.NUM_ROWS)

        top = scroll_offset
        bottom = scroll_offset + page_size

        # Clip to bottom
        if bottom > 1:
            top = 1 - page_size
            bottom = 1

        return (top, bottom)

    def _scrolled(self, cmd, value, opt=None):
        frame_count = float(len(self.frames))
        logging.debug("cmd={}, value={}, opt={}, frame_count={}".format(cmd, value, opt, frame_count))
        page_size = float(self.NUM_ROWS) / frame_count

        if cmd == SCROLL:
            if opt == "units":
                self.first_line += int(value)
            if opt == "pages":
                self.first_line += int(self.NUM_ROWS * int(value))
        elif cmd == MOVETO:
            self.first_line = int( (float(value)) * frame_count - self.NUM_ROWS / 2)
            if self.first_line < 0:
                self.first_line = 0
            elif self.first_line+self.NUM_ROWS > frame_count:
                self.first_line = frame_count - self.NUM_ROWS

        self.first_line = max(0, self.first_line)
        self.first_line = int(min(frame_count-self.NUM_ROWS, self.first_line))

        self.table_scrollbar.set( *self._make_scroll_pos() )

        #self.first_line = int(self.table_scrollbar.get()[0] * frame_count)
        self._update_table()


    def _table_iterator(self, frames):
        if frames is not None:
            self.frames = frames
        else:
            frames = self.frames

        if len(frames)==0:
            return []

        scroll_offset = self.first_line / float(self.NUM_ROWS)

        l = min( ( self.first_line+self.NUM_ROWS, len(frames) ) )

        page_size = float(self.NUM_ROWS) / len(frames)

        scroll_pos = self.first_line * page_size

        self.table_scrollbar.set(scroll_offset, scroll_offset+page_size )

        return zip(range(0, self.NUM_ROWS), range(self.first_line,l), frames[self.first_line:l])

    def _update_table(self, frames = None):
        prev=0
        parameters = self.codingTable.parameters()
        for (line, n, frame) in self._table_iterator(frames):
            params = frame.parameters()
            self.table_labels[line].set( str(n) )
            for p in parameters:
                self.table_vars[(line, p)].set(0)
            for p in params:
                self.table_vars[ (line, p) ].set(params[p])
            if (line-1, 'size') in self.table_vars:
                prev=self.table_vars[(line-1, 'size')].get()
            self.table_vars[(line, 'size')].set(prev+15)
            
    def _readback_table(self, frames = None):
        for (line, n, frame) in self._table_iterator(frames):
            params = frame.parameters()
            self.table_labels[line].set( str(n) )
            changed = False
            for p in params:
                value = self.table_vars[ (line, p) ].get()
                changed = changed or not ( int(params[p]) == int(value) )
                if not (int(params[p]) == int(value)):
                    print(p, value)
                params[p] = int(value)
            if changed:
                self._update_output()

    def _repeatedly(self):
        self.root.after(500, self._repeatedly)
        self.check_change()
        self._readback_table()
        if self.run:
            self.run = False
            self.codingTable = CodingTable(settings.tablesVariant)
            b = Buffer.fromWave(self.filename)
            if b is None:
                messagebox.showerror("Could not read file", "The specified file could not be read!\nMust be mono, 8 or 16 bit WAV file.")
                return
            self.processor = Processor(b, settings.tablesVariant)
            self._update_table(self.processor.frames)
            self._update_output()

    def _update_output(self):
            result = BitPacker.pack(self.processor)
            self.output_text.delete(1.0, END)
            self.output_text.insert(END, result)

    def play(self):
        encoded_frames = BitPacker.raw_stream(self.processor)
        self.statusbar['text'] = str(len(encoded_frames)) + " bytes"
        from lpcplayer import player,tables
        player = player.LpcDecoder(tables.tms5100 if settings.tablesVariant=='tms5100' else tables.tms5220)
        samples=player.decode(encoded_frames)
        # instantiate PyAudio (1)
        p = pyaudio.PyAudio()
        # open stream (2)
        stream = p.open(format=pyaudio.paUInt8, channels=1, rate=8000, output=True)
        # play stream (3)
        stream.write(bytes(samples))
        # stop stream (4)
        stream.stop_stream()
        stream.close()
        # close PyAudio (5)
        p.terminate()

    def mainloop(self):
        self.root.after(500, self._repeatedly)
        self.master.mainloop()

settings.outputFormat='python'
settings.tablesVariant='tms5100'


logging.basicConfig(level=logging.INFO)
# start the app
root = Tk() # create a top-level window
gui = Gui(root)
if __name__ == "__main__":
    gui.mainloop() # call master's Frame.mainloop() method.
    #root.destroy() # if mainloop quits, destroy window
