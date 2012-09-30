# -*- coding: utf-8 -*-
__author__ = 'jb'


import migration_manager
from optparse import make_option


class Command(migration_manager.DefaultCommand):

    option_list = migration_manager.DefaultCommand.option_list + (
        make_option("--id", action="store", dest='migration_id', help = "Id of this migration. May be left blanck. ", default=None),
        )


    def handle_migration(self, **options):

        print "Migrationg from {} to {}".format(self.manager.version_check.version, options['migration_id'])

        backward, ids = self.manager.get_migration_ids(options['migration_id'])

        print backward, ids

        if len(ids) == 0:
            print "No migration needed, already at {}.".format(options['migration_id'])
            return
        if backward:
            print "Performing backward migration. Will execute following migrations {}".format(ids)
        else:
            print "Migrating forward. Will execute following migrations {}".format(ids)


        self.manager.migrate_to(options['migration_id'])


