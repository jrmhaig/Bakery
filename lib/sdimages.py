from os import listdir, path

class _Img:
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

class SdImages(list):
    def __init__(self, *sources):

        self.sources = [] 
        list.__init__(self)
        self.pointer = 0

        # TODO: Do something a bit more to check that the files are valid
        for dir in sources:
            self.extend([ _Img(dir + '/' + f) for f in listdir(dir) ])
            self.sources.append(dir)
        self.sort()

#    def __getitem__(self, n):
#        return str(list.__getitem__(self, n))

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
        return self[self.pointer]

if __name__ == '__main__':
    sdi = SdImages(['/home/pi/images'])
    print(len(sdi))
