import logging
import os
import pickle
import shutil
from tempfile import NamedTemporaryFile
from time import gmtime, strftime
from os import path

from .eq import ValueEqual

FILE_EXT = '.sav'

logger = logging.getLogger(__name__)


class FileEnv:

    def __init__(self, rootPath=None, manifest=False):
        super().__init__()
        if rootPath is None:
            self._rootPath = '.'
        else:
            self._rootPath = rootPath
        logger.debug('Created %s', self)
        os.makedirs(self._rootPath, exist_ok=True)
        if manifest:
            self._manifest = _FileManifest(self._rootPath)
        else:
            self._manifest = None

    def save(self, item, key, timedKey=False):
        if timedKey:
            timeStr = strftime('%Y%m%d-%H%M%S-', gmtime())
            key = timeStr + key
        if not isinstance(item, ValueEqual):
            raise ValueError

        self._safeDump(key, item)
        self._addToInventory(key)
        return key

    def load(self, key):
        with open(self._filePath(key), 'rb') as file:
            item = pickle.load(file)
        return item

    def keys(self):
        if self._manifest is None:
            raise NotImplementedError
        return frozenset(self._manifest.fileKeys())

    def items(self):
        if self._manifest is None:
            raise NotImplementedError
        for key in self.keys():
            yield key, self.load(key)

    def clear(self):
        if self._manifest is None:
            raise NotImplementedError
        for key in self.keys():
            filePath = path.join(self._rootPath, str(key) + FILE_EXT)
            os.remove(filePath)
        self._manifest = _FileManifest(self._rootPath, loadFile=False)
        self._manifest.flush()

    def _addToInventory(self, key):
        if self._manifest is not None:
            self._manifest.add(key)
            self._manifest.update()

    def _safeDump(self, fileName, item):
        tempFile = NamedTemporaryFile(delete=False)
        pickle.dump(item, tempFile)
        tempFile.close()
        filePath = self._filePath(fileName)
        shutil.move(tempFile.name, filePath)
        logger.debug('Moved temp file %s to %s', tempFile.name, filePath)

    def _filePath(self, key):
        fileName = str(key) + FILE_EXT
        filePath = path.join(self._rootPath, fileName)
        return filePath

    def __repr__(self):
        return 'FileEnv({})'.format(self._rootPath)


class _FileManifest(ValueEqual):

    def __init__(self, rootPath, loadFile=True):
        super().__init__()
        self._filePath = rootPath + '/manifest.txt'
        self._keySet = set()
        self._unsyncKeys = set()
        if loadFile:
            self.load()

    def fileKeys(self):
        return self._keySet

    def load(self):
        try:
            with open(self._filePath) as file:
                for line in file.readlines():
                    fileKey = line.rstrip()
                    self._keySet.add(fileKey)
        except FileNotFoundError:
            pass

    def add(self, key):
        self._keySet.add(key)
        self._unsyncKeys.add(key)

    def update(self):
        with open(self._filePath, 'a') as file:
            for fileKey in self._unsyncKeys:
                file.write('{}\n'.format(fileKey))
        self._unsyncKeys.clear()

    def flush(self):
        with open(self._filePath, 'w') as file:
            for fileKey in self._keySet:
                file.write('{}\n'.format(fileKey))
        self.update()


class MemoryEnv:

    def __init__(self):
        super().__init__()
        self._env = {}

    def save(self, item, key):
        if not isinstance(item, ValueEqual):
            raise ValueError

        itemBytes = pickle.dumps(item)
        self._env[key] = itemBytes

    def load(self, key):
        itemBytes = self._env[key]
        item = pickle.loads(itemBytes)
        return item
