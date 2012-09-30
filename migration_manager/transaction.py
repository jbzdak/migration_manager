# -*- coding: utf-8 -*-
__author__ = 'jb'

import api

import psql_misc_utils as psql

class NoopTransaction(api.Transaction):
    def execute_script(self, script, _):
        raise ValueError()

class TestTransaction(api.Transaction):
    def __init__(self):
        import StringIO
        super(TestTransaction, self).__init__()

        self.memory = StringIO.StringIO()

    def execute_script(self, script, set_version):
        self.memory.write(script)
        self.memory.write("\n")
        self.memory.write(set_version)
        self.memory.write("\n")

    @property
    def contents(self):
        return self.memory.getvalue()

class PostgresqlTransaction(api.Transaction):

    def __init__(self, db_location):
        super(PostgresqlTransaction, self).__init__()
        self.db_location = db_location

    def execute_script(self, script, set_version):

        try:
            full_script = "\n".join(map(str, ("BEGIN;", script, set_version, "COMMIT;")))
        except UnicodeDecodeError:
            raise ValueError("Sorry because of technical reasons we dont support (unicode in scripts).")
        psql.psql(self.db_location, full_script)
