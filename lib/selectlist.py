from os import listdir, path

class DiskImage:
    def __init__(self, filepath):
        self.name = path.basename(filepath)
        self.directory = path.dirname(filepath)

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
        return self.directory + '/' + self.name

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

# TODO: Do something a bit more to check that the files are valid
def disk_image_list(*sources):
    images = SelectList()
    for dir in sources:
        images.extend([ DiskImage(dir + '/' + f) for f in listdir(dir) ])
    images.sort()
    return images

if __name__ == '__main__':
    sdi = SdImages(['/home/pi/images'])
    print(len(sdi))
