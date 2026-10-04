class ROMPlugin:
    name = 'base'
    def detect(self, data, path):
        raise NotImplementedError
    def extract(self, data, path, output):
        raise NotImplementedError
