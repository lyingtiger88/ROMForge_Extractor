import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import os, subprocess, sys
from romforge.core import extract_rom

class App:
    def __init__(self, root):
        self.root=root
        root.title('ROMForge Extractor v0.2')
        root.geometry('820x560')
        self.rom=tk.StringVar(); self.out=tk.StringVar(); self.status=tk.StringVar(value='Ready')
        top=ttk.Frame(root,padding=14); top.pack(fill='x')
        ttk.Label(top,text='ROMForge Extractor',font=('Segoe UI',20,'bold')).grid(row=0,column=0,columnspan=3,sticky='w')
        ttk.Label(top,text='NES reverse-engineering and resource extraction suite - v0.2').grid(row=1,column=0,columnspan=3,sticky='w',pady=(0,12))
        ttk.Entry(top,textvariable=self.rom).grid(row=2,column=0,sticky='ew')
        ttk.Button(top,text='Browse ROM',command=self.browse).grid(row=2,column=1,padx=6)
        ttk.Button(top,text='Extract',command=self.extract).grid(row=2,column=2)
        top.columnconfigure(0,weight=1)
        body=ttk.Panedwindow(root,orient='horizontal'); body.pack(fill='both',expand=True,padx=14,pady=(0,10))
        left=ttk.Frame(body); right=ttk.Frame(body); body.add(left,weight=1); body.add(right,weight=2)
        ttk.Label(left,text='Extracted resources',font=('Segoe UI',11,'bold')).pack(anchor='w')
        self.tree=ttk.Treeview(left,show='tree'); self.tree.pack(fill='both',expand=True,pady=(6,0)); self.tree.bind('<<TreeviewSelect>>',self.select)
        ttk.Label(right,text='Preview / information',font=('Segoe UI',11,'bold')).pack(anchor='w')
        self.preview=tk.Text(right,wrap='word'); self.preview.pack(fill='both',expand=True,pady=(6,0))
        bottom=ttk.Frame(root,padding=(14,0,14,12)); bottom.pack(fill='x')
        ttk.Label(bottom,textvariable=self.status).pack(side='left')
        ttk.Button(bottom,text='Open output folder',command=self.open_output).pack(side='right')

    def browse(self):
        p=filedialog.askopenfilename(filetypes=[('NES ROM','*.nes'),('All files','*.*')])
        if p: self.rom.set(p)

    def extract(self):
        p=Path(self.rom.get())
        if not p.exists(): messagebox.showerror('ROMForge','Select a valid ROM.'); return
        try:
            self.status.set('Extracting and analysing...'); self.root.update_idletasks()
            out=extract_rom(p); self.out.set(str(out)); self.populate(out); self.status.set(f'Complete: {out}')
        except Exception as e:
            self.status.set('Error'); messagebox.showerror('ROMForge',str(e))

    def populate(self,out):
        self.tree.delete(*self.tree.get_children()); out=Path(out)
        root_id=self.tree.insert('', 'end', text=out.name, open=True, values=(str(out),))
        def add(parent,path):
            for q in sorted(path.iterdir(),key=lambda x:(not x.is_dir(),x.name.lower())):
                iid=self.tree.insert(parent,'end',text=q.name,values=(str(q),))
                if q.is_dir(): add(iid,q)
        add(root_id,out)

    def select(self,_=None):
        sel=self.tree.selection()
        if not sel:return
        vals=self.tree.item(sel[0],'values')
        if not vals:return
        p=Path(vals[0]); self.preview.delete('1.0','end')
        if p.is_file() and p.suffix.lower() in ('.txt','.md','.json','.csv','.asm'):
            self.preview.insert('1.0',p.read_text(encoding='utf-8',errors='replace')[:100000])
        else:self.preview.insert('1.0',str(p))

    def open_output(self):
        if not self.out.get():return
        p=self.out.get()
        if sys.platform.startswith('win'): os.startfile(p)
        elif sys.platform=='darwin': subprocess.Popen(['open',p])
        else: subprocess.Popen(['xdg-open',p])

if __name__=='__main__':
    root=tk.Tk(); App(root); root.mainloop()
