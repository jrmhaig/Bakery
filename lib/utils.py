#   Copyright 2014 Joseph Haig
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
import os
import subprocess
import signal
import re
import struct
import queue
import threading
import time
import pyudev
import tempfile

class DiskImage:
    def __init__(self, filepath, file_format, post, variables):
        self.name = os.path.basename(filepath)
        self.directory = os.path.dirname(filepath)
        self.file_format = file_format
        self.post = list(map( lambda x :
                                self.directory + '/' + self.name + '.post.' + x,
                                sorted(post) ) )
        self.variables = variables

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
        return self.directory + '/' + self.name + '.' + self.file_format

    def get_post_scripts(self):
        return self.post

    def info(self, key):
        if key == 'name':
            return self.name
        elif key == 'n_post_scripts':
            return "{0} post scripts".format(len(self.post))
        elif key == 'n_variables':
            return "{0} variables".format(len(self.variables))
        else:
            return "Unknown key"

class Drive:
    def __init__(self, path, model):
        self.path = path
        self.model = model
        self.present = False

    def __str__(self):
        return self.model

    def path(self):
        return self.path

    def info(self, key):
        if key == 'model':
            return self.model
        elif key == 'node_path':
            return self.path
        else:
            return "Unknown key"

class SelectList(list):
    """ Select List

    Extend the normal list with:
      * A pointer to the current item
      * A selected item of the list, which may be different from the pointer
        or None
      * A flag to indicate that the list has been changed

    """
    def __init__(self):

        list.__init__(self)
        self.pointer = 0
        self.selected = None
        self.updated = False

    def next(self):
        if len(self) > 0:
            self.pointer += 1
            if self.pointer >= len(self):
                self.pointer = 0
            return self.current()
        else:
            return None

    def prev(self):
        if len(self) > 0:
            self.pointer -= 1
            if self.pointer < 0:
                self.pointer = len(self)-1
            return self.current()
        else:
            return None

    def current(self):
        if self.pointer >= len(self):
            return None
        else:
            #return self[self.pointer].name
            return self[self.pointer]

    def select(self):
        if self.selected == self.pointer:
            self.selected = None
        else:
            self.selected = self.pointer

    def current_is_selected(self):
        return self.selected == self.pointer

    def append(self, item):
        self.updated = True
        super().append(item)

    def remove(self, item):
        self.updated = True
        super().remove(item)

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
                key = pth + '/' + spl[-1][::-1]
                if key not in file_groups:
                    file_groups[key] = {
                                         'post': [],
                                         'file_format': None,
                                         'variables': {},
                                       }
                if len(spl) == 3:
                    if spl[1] == 'tsop':
                        # Post install script
                        file_groups[key]['post'].append(spl[0][::-1])
                    elif spl[1] == 'gmi' and spl[0] == 'zg':
                        # Zipped image
                        file_groups[key]['file_format'] = 'img.gz'
                elif len(spl) == 2:
                    if spl[0] == 'gmi':
                        # Uncompressed image
                        file_groups[key]['file_format'] = 'img'
                    elif spl[0] == 'srav':
                        # Variables file
                        vs = open(pth + '/' + fl)
                        for line in vs:
                            parts = line.rstrip().split(':',1)
                            if len(parts) > 1:
                                file_groups[key]['variables'][parts[0]] = parts[1]
    for key in file_groups:
        if file_groups[key]['file_format'] != None:
            images.append( DiskImage( key, file_groups[key]['file_format'], file_groups[key]['post'], file_groups[key]['variables'] ) )
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
    print("Image:", str(image))
    print("File format:", image.file_format)

    unzip = None
    dd = None
    size = None
    if image.file_format == 'img.gz':
        fl = open(str(image), 'rb')
        fl.seek(-4, 2)
        r = fl.read()
        fl.close()
        size = struct.unpack('<I', r)[0]

        # Unzip process
        unzip = subprocess.Popen(['zcat', str(image)], stdout=subprocess.PIPE)

        # Make sure it starts
        while unzip.poll() is not None:
            print("Waiting for unzip to start")
            sleep(0.1)

        print("unzip PID:", unzip.pid)
        dd = subprocess.Popen(['dd', 'of=' + str(device), 'bs=1M'], bufsize=1, stdin=unzip.stdout, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    elif image.file_format == 'img':
        fl = open(str(image), 'rb')
        fl.seek(0, 2)
        size = fl.tell()
        fl.close()
        
        dd = subprocess.Popen(['dd', 'of=' + str(device), 'if=' + str(image), 'bs=1M'], bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    else:
        return False

    # DD process
    # Output to a pipe to catch status updates
    dd_queue = queue.Queue()
    dd_thread = threading.Thread(target = read_pipe, args=(dd.stdout, dd_queue))
    dd_thread.daemon = True
    dd_thread.start()

    # Gather required variables
    environment = { 'IMGDIR': image.directory, 'DEVICE': str(device) }
    for var in image.variables:
        environment[var] = display.question(var, image.variables[var])

    display.progress_title()

    print("dd PID   :", dd.pid)
    probe_sleep = 3
    next_probe = time.time()
    while dd.poll() is None:
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
                # In case it has hung and recovered
                while time.time() > next_probe:
                    next_probe = next_probe + probe_sleep
        except:
            pass

    if dd.returncode != 0:
        return False

    # Find partitions
    if len(image.get_post_scripts()) > 0:
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
        #environment = { 'IMGDIR': image.directory }
        pn = 1
        for partition in pyudev.Context().list_devices(subsystem='block', DEVTYPE='partition'):
            node = partition.device_node
            if re.search(r"{}".format(device), node):
                environment["PARTITION{}".format(pn)] = node
                pn = pn + 1

        for script in image.get_post_scripts():
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

def get_device_partitions(device):
    partitions = []
    for partition in pyudev.Context().list_devices(subsystem='block', DEVTYPE='partition'):
        node = partition.device_node
        if re.search(r"{}".format(str(device)), node):
            partitions.append(node)
    return partitions

def mount(path):
    directory = tempfile.mkdtemp()
    try:
        subprocess.check_call(["mount", path, directory])
        return directory
    except CalledProcessError:
        return False

def umount(directory):
    try:
        subprocess.check_call(["umount", directory])
        os.rmdir(directory)
        return True
    except CalledProcessError:
        return False

def scan(path):
    images = {}
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            m = re.search(r"^(.+).img.gz$", str(name))
            if m != None:
                images[root] = m.group(1)

    return images
