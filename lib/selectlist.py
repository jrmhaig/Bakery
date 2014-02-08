import os

class DiskImage:
    def __init__(self, filepath, post):
        self.name = os.path.basename(filepath)
        self.directory = os.path.dirname(filepath)
        self.post = list(map( lambda x :
                                self.directory + '/' + self.name + '.post.' + x,
                                sorted(post) ) )

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

    def post_scripts(self):
        return self.post

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

    def selected_image_file(self):
        if self.selected == None:
            return None
        else:
            return str(self[self.selected])

    def selected_post_scripts(self):
        return self[self.selected].post_scripts()
        #return []

    def select(self):
        if self.selected == self.pointer:
            self.selected = None
        else:
            self.selected = self.pointer

    def current_is_selected(self):
        return self.selected == self.pointer

def disk_image_list(*sources):
    images = SelectList()
    file_groups = {}
    for dr in sources:
        for sdr in os.listdir(dr):
            pth = dr + '/' + sdr
            files = os.listdir(pth)
            post = []
            for fl in files:
                spl = fl.split('.')
                key = pth + '/' + spl[0]
                if key not in file_groups:
                    file_groups[key] = { 'post': [] }
                if spl[1] == 'post':
                    file_groups[key]['post'].append(spl[2])
                    post.append(spl[2])
                elif spl[1] == 'img' and spl[2] == 'gz':
                    file_groups[key]['format'] = 'img.gz'
    for key in file_groups:
        images.append( DiskImage( key, file_groups[key]['post'] ) )
    images.sort()
    return images

if __name__ == '__main__':
    sdi = SdImages(['/home/pi/images'])
    print(len(sdi))
