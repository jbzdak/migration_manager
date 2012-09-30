# -*- coding: utf-8 -*-
__author__ = 'jb'


class MigrationError(Exception):  pass

class SerializationError(MigrationError): pass

class RepositoryError(MigrationError): pass

class Migration(object):

    """
        Represents a migration --- something that has forward and reverse script and also a name.
    """

    def __init__(self, migration_name, forward_script, backward_script):
        super(Migration, self).__init__()

        self.migration_name = migration_name
        self.forward_script = forward_script
        self.backward_script = backward_script

        self.has_backward = backward_script is not None

    def _contents(self):
        return {
            "name" : self.migration_name,
            "forward" : self.forward_script,
            "backward" : self.backward_script
        }

    def __hash__(self):
        return hash(self._contents())

    def __eq__(self, other):
        if self == other:
            return True
        if not isinstance(other, Migration):
            return False
        return self._contents() == other._contents()


class Serializer(object):

    """
        Something that is able to serialize a migration to a specific format
    """

    supports_backward_migration = None
    """
        Whether this format supports backward migration
    """
    extension = None
    """
        Extension this format uses
    """
    saves_migration_name = None
    """
        Whether this format saves migration name
    """

    def save(self, file, migration):
        if not self.supports_backward_migration and migration.has_backward:
            raise SerializationError("Serializer {0} doesn't support backward migrations (such as {1.migration_name})".format(self, migration))
        self._save(file, migration)
        file.flush()

    def load(self, file, migration_name = None, migration_name_guess = None):
        if not any((migration_name is not None, migration_name_guess is not None)):
            raise ValueError("Give eiter migration name or migration_name_guess")
        return self._load(file, migration_name if migration_name else migration_name_guess, migration_name is None)

    def _save(self, file, migration):
        """
        Saves the migration to file
        :param file:
        :param migration:
        :return:
        """
        raise NotImplementedError()

    def _load(self, file, migration_name, is_guess):
        """
        Loads and retuens the migration from file
        :param file: File like object.
        :param migration_name: Name of the migration --- will be used if migration name isn't stored
            in serialized format
        :param is_guess: Whether this migration name was guessed from file name.
        :return: Migration
        """
        raise NotImplementedError()

class Transaction(object):

    """
        Something that is able to execute sql script.
    """

    def execute_script(self, script, set_version):
        raise NotImplementedError()

class VersionChecker(object):

    def __init__(self):
        super(VersionChecker, self).__init__()
#        self.using = None


    @property
    def version(self):
        """
        Reads version id using django settings
        """
        raise NotImplementedError()

    def schema_update_script(self, version):
        """
            Produces SQL command that updates version, it will be used by the Transaction to
            update schema version to have consistency.
        """



class Repository(object):

    """
    Class that represents repository of migrations. In most cases such migrations will lie flat in
    in a folder. Hovewer migration launched from zipfile module would need another repository.
    """

    readonly = None


    def __init__(self, file_extension = None):
        super(Repository, self).__init__()
        self.file_extension = file_extension

    @property
    def migration_filenames(self):
        """
        Returns map that maps migration id to migration filename.
        :return:
        """

        raise NotImplementedError()


    def sanitize_name(self, migration_name):
        """
        Takes a migration name (any string) and turns it into something that may be saved to file system
        wihout loosing to much information
        :param migration_name:
        :return:
        """
        raise NotImplementedError()

    def desanitize_name(self, file_name):
        """
            Gets a filename and tries to recover migration name from it
        """
        raise NotImplementedError()

    @property
    def migration_names(self):
        return dict(map(lambda x: (x[0], self.desanitize_name(x[1])), self.migration_filenames.iteritems()))


    @property
    def migration_ids(self):
        return sorted(self.migration_filenames.keys())

    def _open_migration_file(self, id, migration_name, mode):
        raise  NotImplementedError()

    @property
    def max_version(self):
        return max(self.migration_ids)

    def open_migration_file(self, id = None, migration_name = None, mode = "r"):

        if self.readonly and 'w' in mode:
            raise ValueError("Won't open file for writing in a readonly repo! ")
        if id is None and migration_name is None:
            raise ValueError("Id and migration_name cant be None in open_migration_file_call")
        if id is None:
            id = max(self.migration_ids) + 1
#        if migration_name is None:
#            migration_name = self.migration_filenames[id]
        return self._open_migration_file(id, migration_name, mode)


class Manager(object):


    def __init__(self, repository, serializer, version_check, transaction):
        """

        Initializes manager.

        Repository, serializer, version_check and transaction should not change after
        lifetime of this object --- but enforcing it would be an overkill.

        :param repository:
        :param serializer:
        :param version_check:
        :param transaction:
        :return:
        """

        super(Manager, self).__init__()
        self.repository = repository
        self.repository.file_extension = serializer.extension
        self.serializer = serializer
        self.version_check = version_check
        self.transaction = transaction


    def __getitem__(self, id):
        if id not in self.repository.migration_ids:
            raise RepositoryError("Couldn't find migration with id {0}".format(id))
        id = int(id)
        file = self.repository.open_migration_file(id = id)
        name = self.repository.migration_names[id]
        migration = self.serializer.load(file, migration_name_guess=name)
        return migration

    def __setitem__(self, id, migration):
        if id in self.repository.migration_ids:
            raise RepositoryError("There is migration with id {0}".format(id))
        id = int(id)
        file = self.repository.open_migration_file(id, migration.migration_name, 'w')
        self.serializer.save(file, migration)

    def get_migration_ids(self, target_version = None):
        if target_version is None:
            target_version = self.repository.max_version

        target_version = int(target_version)

        current_version = self.version_check.version

        if target_version == current_version:
            return False, []

        if target_version > current_version: #Forward migration
            versions = [id for id in self.repository.migration_ids if current_version < id <= target_version]
            return False, sorted(versions)

        versions = [id for id in self.repository.migration_ids if current_version >= id > target_version]
        return True, sorted(versions, reverse=True)

    @property
    def migration_ids(self):
        return self.repository.migration_ids

    @property
    def max_version(self):
        return self.repository.max_version

    def __iter__(self):
        return iter(self.repository.migration_ids)

    def migrate_to(self, target_version):

        if target_version is None:
               target_version = self.repository.max_version

        target_version = int(target_version)

        backward, ids = self.get_migration_ids(target_version)

        if backward:
            invalid_migrations = [id for id in ids if not self[id].has_backward]
            if len(invalid_migrations) > 0:
                raise MigrationError("Cant migrate database from {}, to {} because following "
                                     "migrations don't support backward migrations".format(
                                    self.version_check.version, target_version, invalid_migrations
                ))

        for ii, id in enumerate(ids):
            migration = self[id]
            script = migration.forward_script if not backward else migration.backward_script
            id_to_set = id
            if backward:
                if ii == len(ids)-1:
                    id_to_set = target_version
                else:
                    id_to_set = ids[ii+1]

            self.transaction.execute_script(script, self.version_check.schema_update_script(id_to_set))






