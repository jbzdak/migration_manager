# -*- coding: utf-8 -*-
__author__ = 'jb'

import api
import os
import subprocess

class PSQLException(IOError): pass

class PostgresDBLocation(object):
    def __init__(self, **kwargs):
        super(PostgresDBLocation, self).__init__()
        self.username = kwargs.get('username')
        self.password = kwargs.get('password')
        self.port = kwargs.get('port')
        self.host = kwargs.get('host')
        self.dbname = kwargs.get('dbname')



    def update_from_django_config(self, using):

        from django.conf import settings

        self.using = using

        database = settings.DATABASES[using]

        to_update = (
            ('username', 'USER'),
            ('dbname', 'NAME'),
            ('password', 'PASSWORD'),
            ('host', 'HOST'),
            ('port', 'PORT')
        )

        def update(tuple):
            if database[tuple[1]] is not None:
                setattr(self, tuple[0], database[tuple[1]])

        map(update, to_update)

class PsqlManager(api.Manager):
    def __init__(self, db_location, **kwargs):
        if 'transaction' not in kwargs:
            import transaction
            kwargs['transaction'] = transaction.PostgresqlTransaction(db_location)
        self.db_location = db_location
        super(PsqlManager, self).__init__(**kwargs)
        if 'transaction' in kwargs:
            self.transaction.db_location =  db_location

    @property
    def using(self):
        return self._using

    @using.setter
    def using(self, value):
        if value is not None:
            self.db_location.update_from_django_config(value)
        self._using = value

    def update(self, username, password, dbname = None):
        if username is not None:
            self.db_location.username = username
        if password is not None:
            self.db_location.password = password
        if dbname is not None:
            self.db_location.dbname = dbname



def _update_arglist(arglist, db_location):

    arg_commands = (
        ('host', '--host={}'),
        ('port', '--port={}'),
        ('username', '--username={}'),
        ('dbname', '{}')
    )

    def append(tuple):
        if getattr(db_location, tuple[0]) is not None:
            arglist.append(tuple[1].format(getattr(db_location, tuple[0])))

    map(append, arg_commands)

def _update_enviorment(env, db_location):
    if db_location.password is not None:
        env["PGPASSWORD"] = db_location.password

def psql(db_location, script, echo = True):

    arglist = ['psql', '--echo-all', '-v', 'ON_ERROR_STOP=1']

    env = {}

    _update_arglist(arglist, db_location)

    _update_enviorment(env, db_location)

    print "CALLING " + " ".join(arglist)

    stdout = None
    stderr = None
    if not echo:
        stdout = open(os.devnull, 'w')
        stderr = open(os.devnull, 'w')


    process = subprocess.Popen(
        arglist,
        env = env,
        stdin = subprocess.PIPE,
        stdout = stdout,
        stderr = stderr
    )

    process.communicate(script)

    returncode = process.wait()

    if returncode != 0:
        raise PSQLException(returncode)

def pg_dump(db_location, target = None, echo = True, exclude_tables_pattern = None,
            include_table_patterns = None, schema_only = False, data_only=False,
            disable_triggers = False):

    arglist = ['pg_dump',]

    env = {}
    _update_arglist(arglist, db_location)

    _update_enviorment(env, db_location)

    if exclude_tables_pattern:
        for table in exclude_tables_pattern:
            arglist.append("--exclude-table=\"" + table + '\"')

    if include_table_patterns:
        for table in include_table_patterns:
            arglist.append("--table=\"{}\"".format(table))

    if schema_only:
        arglist.append("--schema-only")

    if data_only:
        arglist.append("--data-only")

    if disable_triggers:
        arglist.append("--disable-triggers")

    print "CALLING " + " ".join(arglist)

    target_file = None
    stdout = None
    stderr = None
    if not echo:
        stderr = open(os.devnull, 'w')
    if target:
        target_file = open(target, 'w')
        stdout = target_file

    process = subprocess.Popen(
        arglist,
        env = env,
        stdin = subprocess.PIPE,
        stdout = stdout,
        stderr = stderr
    )

    if target_file:
        target_file.close()

    returncode = process.wait()

    if returncode != 0:
           raise PSQLException(returncode)