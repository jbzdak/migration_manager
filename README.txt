
===============================
Django migration manager
===============================

This is a package that is manages folders containing handmane migration sql code, applies this code,
and allows trawersal between versions.

What this application enables:

* Keeps a repository of migration files (either sql, xml or whatever).

 * Helps to manage such a repository

* Allows automatical migration between versions (backward migrations supported)

 * Executes scripts via `psql` command, this is due to the fact that there is no way (at least none
    I'm aware of) to execute multicommand sql scripts via python DB-API, without parsing this
    sql by hand.

and that's all.

It works with postgresql only (but I guess that using other databases would be straightforward).

Side note
----------

Ordinarily you should rather try to use django ORM and South to provide migration functionality!
But then I needed a database that has some psql extensions (which transcend django's orm
functionality).

Concepts
========

Repository
----------
Something that stores migrations. Repositories should use api of `migration_manager.api.Repository`.

There is one repository defined, namely the `FileSystemRepository`, that storesm= migration in
particular folder using following naming convention:
'"<migration_id>_<migration_name>.<file extension>"'

Db location
-----------

Something that stores database credentials, it is able to get these from settings, but most probably
you'll want to override these, as django database user shouldn't be able to change schema.

Serializer
----------

Someting that stores sql snippets to a file.

There are following defined serializers:

PlaintextSerializer:
    this serializer stores sql snippets as plain sql, unicode encoded, files. It does not support
    backward migrations.
XmlSerializer:
   stores sql migration snippets as XML files with brain dead simple schema. It supports backward
   migrations.

Version check
-------------

Is an object that checks current version of schema stored in the database, and is able to produce
SQL string that updates this version no.


Manager
-------

Object that manages the repository.

Provided Commands
=================

These are django commands that provide this module's functionality.

New migration
-------------

Adds new migration.

Migrate
-------

Migrates to particular migration number, raising error if there is no migration path.


Setup
=====

Create version checker
----------------------

Is an object that checks current version of schema stored in the database, and is able to produce
SQL string that updates this version no.

I use following::

 class VersionCheck(object):

    def __init__(self, db_location):
        super(VersionCheck, self).__init__()
        self.db_location = db_location

    @property
    def using(self):
        return self.db_location.using

    def schema_update_script(self, version):
        return "SELECT set_schema_version('{:05d}');\n".format(int(version))

    @property
    def version(self):
        return int(utils.execute_string_query("SELECT get_schema_version();", database=self.using)[0][0][0])


Create repository instance
---------------------------

Create a repository instance and put it somewhere global::

 def my_manager(db_location = None, repository = REPOSITORY):

    if db_location is None:
        db_location = migration_manager.PostgresDBLocation()
        db_location.update_from_django_config('default')

    manager = migration_manager.PsqlManager(
        db_location,
        repository= migration_manager.FileSystemRepository(repository),
        serializer=migration_manager.XmlSerializer(),
        version_check=version check
    )
    return manager

Setup settings py
-----------------

Set `MIGRATION_MANAGERS` setting. It should look like that::

 MIGRATION_MANAGERS = (
    ("manager_name", "manager_module.MANAGER"),
    ("other", "manager_module.OTHER_MANAGER"),
 )

it is a touple of name -- manager path mappings. Paths should point to
`migration_manager.api.Manager` instances. Names can be passed to management commands.

First defined manager is the 'default' one.


I want to do
============

I want to manage part of my django database that doesn't use ORM, and I use postgresql
---------------------------------------------------------------------------------------

Than you have found your solution.

I want to manage part of my django database that doesn't use ORM, and I **don't** use postgresql
------------------------------------------------------------------------------------------------

If you are willing to write code that connects to the database it will work.

You will have to write own `migration_manager.api.Transaction` that connects to your database.

I want to manage database but I don't use django
------------------------------------------------

Should be easy, look at 'django_commands' and rewrite this code using your command line utility.







