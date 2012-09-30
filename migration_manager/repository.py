# -*- coding: utf-8 -*-

__author__ = 'jb'

import os
import re

import api


NAME_EXTENSION_PATTERN = "([\w\d\-_]+)$"

ANY_MIGRATION_PATTERN = "^(\d{5})\-" + NAME_EXTENSION_PATTERN

#SPECIFIC_MIGRATION_PATTERN = "({id:05d})" + NAME_EXTENSION_PATTERN

FILE_NAME_PATTERN = "{id:05d}-{name}.{ext}"

class FileSystemRepository(api.Repository):

    def __init__(self, folder, any_migration_pattern = ANY_MIGRATION_PATTERN, new_file_template = FILE_NAME_PATTERN):
        """

        :param folder:
        :param any_migration_pattern: pattern that matches any migration filename (minus extension!)

        :return:
        """
        super(FileSystemRepository, self).__init__()
        self.folder = folder
        self.migration_pattern = re.compile(any_migration_pattern)
        self.new_file_template = new_file_template

    @property
    def raw_migration_names(self):
        return map(lambda x: x + "." + self.file_extension, self.migration_filenames)

    @property
    def migration_filenames(self):
        files = os.listdir(self.folder)
        extension_pattern = re.compile(".*\.{0}".format(self.file_extension))

        files = filter(lambda x : re.match(extension_pattern, x), files) #Filter by extension
        files = map(lambda x : x[:-len(self.file_extension)-1], files) #Strip extensions

        result = {}

        for file in files:
            match = re.match(self.migration_pattern, file)
            if not match:
                continue
            id = int(match.group(1))
            if id in result:
                raise api.RepositoryError("Repository contains two migrations with the same id {}. "
                                          "Migration names are {} and {}", id, result[id], file)
            result[id] = file + "." + self.file_extension

        return result

    def sanitize_name(self, migration_name):
        return re.sub("[\s]+", "_", re.sub("[^\w\d\-_]", "_", migration_name))

    def desanitize_name(self, file_name):
        file_name = file_name[:-(len(self.file_extension) + 1)]
        migration_name = re.match(self.migration_pattern, file_name).group(2)
        return re.sub("_", " ", migration_name)

    def _open_migration_file(self, id, migration_name, mode):
        if id in self.migration_ids:
            return open(os.path.join(self.folder, self.migration_filenames[id]), mode)
        else:
            file_name = self.new_file_template.format(
                                        id = id, name = self.sanitize_name(migration_name), ext = self.file_extension)
            return open(os.path.join(self.folder, file_name), mode)


