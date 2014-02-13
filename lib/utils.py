import os
import subprocess
import signal
import re
import struct
import queue
import threading
import time
import pyudev

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

    def get_image(self):
        return self[self.pointer]

    def selected_image_file(self):
        if self.selected == None:
            return None
        else:
            return str(self[self.selected])

    def selected_post_scripts(self):
        return self[self.selected].post_scripts()

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
            for fl in files:
                # Reverse before split to get cut into only 3 parts from the
                # right. The things to match are therefore then all reversed.
                spl = fl[::-1].split('.',2)
                key = pth + '/' + spl[2][::-1]
                if key not in file_groups:
                    file_groups[key] = { 'post': [] }
                if spl[1] == 'tsop':
                    file_groups[key]['post'].append(spl[0][::-1])
                elif spl[1] == 'gmi' and spl[0] == 'zg':
                    file_groups[key]['format'] = 'img.gz'
    for key in file_groups:
        images.append( DiskImage( key, file_groups[key]['post'] ) )
    images.sort()
    return images

def read_pipe(out, queue):
    """Read from the pipes output of a subprocess """

    for line in iter(out.readline, b''):
        queue.put(str(line))
    out.close()

def write_image(device, image, display):
    """Write the image to the card """

    # Uncompressed size of a gzip file is stored in the last 4 bytes
    fl = open(str(image), 'rb')
    fl.seek(-4, 2)
    r = fl.read()
    fl.close()
    size = struct.unpack('<I', r)[0]

    print("Image:", str(image))

    # Unzip process
    unzip = subprocess.Popen(['zcat', str(image)], stdout=subprocess.PIPE)

    # DD process
    # Output to a pipe to catch status updates
    dd = subprocess.Popen(['dd', 'of=' + device, 'bs=1M'], bufsize=1, stdin=unzip.stdout, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    dd_queue = queue.Queue()
    dd_thread = threading.Thread(target = read_pipe, args=(dd.stdout, dd_queue))
    dd_thread.daemon = True
    dd_thread.start()

    print("unzip PID:", unzip.pid)
    print("dd PID   :", dd.pid)
    probe_sleep = 20
    next_probe = time.time()
    while unzip.poll() is None:
        if dd.poll() is not None:
            unzip.kill()
            return False
        if time.time() > next_probe:
            dd.send_signal(signal.SIGUSR1)
            next_probe = next_probe + probe_sleep

        try:
            line = dd_queue.get(timeout = 0.1)
            m = re.search(r"(\d+) bytes", str(line))
            if m != None:
                percent = 100*int(m.group(1))/size
                display.progress(percent)
                print("Completed: " + str(percent) + "%")
                next_probe = time.time() + 5
        except:
            pass

    # Find partitions
    if len(image.post_scripts()) > 0:
        display.write_queue.put( { 'action': 'write',
                                'pos': [0, 0],
                                'text': 'Post script:',
                                'blank': 1 } )

        # TODO Do this without an external script
        display.write_queue.put( { 'action': 'write',
                                'pos': [0, 1],
                                'text': 'Refresh device',
                                'blank': 1 } )
        subprocess.call(['/home/pi/Bakery/freshen.sh', device])
        environment = { 'IMGDIR': image.directory }
        pn = 1
        for partition in pyudev.Context().list_devices(subsystem='block', DEVTYPE='partition'):
            node = partition.device_node
            if re.search(r"{}".format(device), node):
                environment["PARTITION{}".format(pn)] = node
                pn = pn + 1

        for script in image.post_scripts():
            script_handle = open( script, 'r' )
            # Default title - just the file name
            title = os.path.basename(script)
            for line in script_handle:
                m = re.search(r"#TITLE# (.+)", line)
                if m != None:
                    title = m.group(1)
                    break
            display.write_queue.put( { 'action': 'write',
                                    'pos': [0, 1],
                                    'text': title,
                                    'blank': 1 } )
            script_handle.close()
            subprocess.call([ script ], env = environment)

    print("And finished")
    return True

if __name__ == '__main__':
    sdi = SdImages(['/home/pi/images'])
    print(len(sdi))
