#from os import listdir, path
import os
import re

class DiskImage:
    def __init__(self, filepath):
        self.name = os.path.basename(filepath)
        self.directory = os.path.dirname(filepath)

    def __lt__(self, other):
        """Sorting rule

        Sort by file name first and then, if the filenames are the same
        compare the directory name.

        """
        if ( self.name < other.name
           or (self.name == other.name and
           self.directory < other.directory) ):
            return 1

    def __str__(self):
        return self.directory + '/' + self.name + '.img.gz'

class SelectList(list):
    def __init__(self):

        self.sources = [] 
        list.__init__(self)
        self.pointer = 0
        self.selected = None

    def next(self):
        self.pointer += 1
        if self.pointer >= len(self):
            self.pointer = 0
        return self.current()

    def prev(self):
        self.pointer -= 1
        if self.pointer < 0:
            self.pointer = len(self)-1
        return self.current()

    def current(self):
        return self[self.pointer].name

    def selected_full_path(self):
        if self.selected == None:
            return None
        else:
            return str(self[self.selected])

    def select(self):
        if self.selected == self.pointer:
            self.selected = None
        else:
            self.selected = self.pointer

    def current_is_selected(self):
        return self.selected == self.pointer

def disk_image_list(*sources):
    images = SelectList()
    for dr in sources:
        for sdr in os.listdir(dr):
            pth = dr + '/' + sdr
            for fl in os.listdir(pth):
                m = re.search(r"(.+)\.img\.gz", fl)
                if m != None:
                    images.extend( [ DiskImage( pth + '/' + m.group(1) ) ] )
    images.sort()
    return images

if __name__ == '__main__':
    sdi = SdImages(['/home/pi/images'])
    print(len(sdi))
