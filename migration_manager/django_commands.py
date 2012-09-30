# -*- coding: utf-8 -*-
from optparse import make_option
import getpass
__author__ = 'jb'


from django.core.management.base import NoArgsCommand
from django.conf import settings

import migration_manager

class DefaultCommand(NoArgsCommand):

    option_list = NoArgsCommand.option_list + (
        make_option('--using', action='store', dest="using",
                    help='Django databse to use'),
        make_option('--get-password', action="store_true", dest="password", default = False,
                    help="Whether user wants to password from settings py. If this option is present "
                         "he will be asked for it via console"),
        make_option("--username", action="store", dest="username", help="Username that overrides "
                                                                        "django settings"),
        make_option("--dbname", action="store", dest="dbname", help="Database to use --- overrides"
                                                                    "django config"),
        make_option("--manager", action="store", dest="manager", help="Which manager to use. Provide manager name. ")


        )

    @classmethod
    def patch_transaction(cls, using, user, password,  dbname = None):
        if using is not None:
            cls.manager.using = using
        cls.manager.update(user, password, dbname = dbname)


    def handle_migration(self, **options):
        raise NotImplementedError()

    def set_up_manager(self, **options):
        import manager
        managers = getattr(settings, "MIGRATION_MANAGERS", None)
        if managers is None:
            raise ValueError("Please set MIGRATION_MANAGERS setting")
        manager_name =options['manager']
        if manager_name is not None:
            try:
                manager_path = dict(managers)[manager_name]
            except KeyError:
                raise ValueError("Requested manager named {name}. This manager is missing from "
                                 "managers config.".format(name = manager_name))
        else:
            manager_path = managers[0][0]
        self.manager = manager.MIGRATION_MANAGERS[manager_path]

    def handle_noargs(self, **options):
        self.set_up_manager(**options)
        password = None
        if options["password"]:
            print "Password override"
            password = getpass.getpass()
        if password or options['using'] or options['username'] or options['dbname']:
            self.patch_transaction(options['using'], options['username'], password, dbname=options['dbname'])
        self.handle_migration(**options)

