from os import listdir

class SdImages:
    def __init__(self, sources):
        self.sources = sources

    def list(self):
        """Return a list of available images"""
        # TODO: Do something a bit more to check that the files are valid
        files = []
        for dir in self.sources:
            files.extend([ dir + '/' + f for f in listdir(dir) ])
        return files
