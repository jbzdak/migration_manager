# -*- coding: utf-8 -*-


__author__ = 'jb'

import migration_manager
from optparse import make_option

class Command(migration_manager.DefaultCommand):

    option_list = migration_manager.DefaultCommand.option_list + (
        make_option("--id", action="store", dest='migration_id', help = "Id of this migration. May be left blanck. ", default=None),
        make_option("--force-bad-id", action="store_true", dest="force_bad_id", help = "Youll get notified when it will be needed", default = False),
        make_option("--name", action="store", dest="migration_name", help = "Migration name", default=None),
        make_option("--no-backwards", action="store_true", dest="no_backwards", help = "Write migration with disabled backwards migration", default=False),
        )

    def handle_migration(self, **options):

        id = options['migration_id']

        if id is None:
            id = self.manager.max_version + 1

        if id in self.manager.migration_ids:
            raise ValueError("There already is migraion with id {:05d}.".format(id))

        if id < self.manager.max_version and not options['force_bad_id']:
            raise ValueError("This would create migration that has lower id that last migration in repository. This could fuck your database somewhere wery much."\
                             "If you know what to do pass --force-bad-id option.".format(id))

        if not options['migration_name']:
            raise ValueError("Please provide name for this migration!")

        m = migration_manager.Migration(options['migration_name'], "Write migration here", "Write migration here" if not options['no_backwards'] else None)

        self.manager[id] = m


