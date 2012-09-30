
import os
import tempfile
import base64
import StringIO
import random
import unittest

from migration_manager import api
from migration_manager import serializer
from migration_manager import repository
from migration_manager import transaction

FOLDER = os.path.dirname(__file__)

REPO_DIR = os.path.join(FOLDER, "_test")


TEST_MIGRATION = api.Migration(
    "Test migration",
    """CREATE TABLE auth_user_groups
(
  id serial NOT NULL,
  user_id integer NOT NULL,
  group_id integer NOT NULL,
  CONSTRAINT auth_user_groups_pkey PRIMARY KEY (id ),
  CONSTRAINT auth_user_groups_group_id_fkey FOREIGN KEY (group_id)
      REFERENCES auth_group (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT user_id_refs_id_831107f1 FOREIGN KEY (user_id)
      REFERENCES auth_user (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT auth_user_groups_user_id_group_id_key UNIQUE (user_id , group_id )
);""",
    "DROP TABLE auth_user_groups;"
)

TEST_MIGRATION_NO_BACK = api.Migration(TEST_MIGRATION.migration_name,
                                       TEST_MIGRATION.forward_script, None)

class SerializerTest(object):

    serializer_instance = None

    migration = None

    serialized_migration = None

    def _random_migtation(self):
        return api.Migration(
            base64.encodestring(os.urandom(45)),
            base64.encodestring(os.urandom(45)),
            base64.encodestring(os.urandom(45)) if self.serializer_instance.supports_backward_migration else None
        )

    def test_random_data(self):
        for ii in xrange(10):
            migration = self._random_migtation()
            file = tempfile.NamedTemporaryFile(suffix=self.serializer_instance.extension, delete=False)
            self.serializer_instance.save(file, migration)
            migration2 = self.serializer_instance.load(open(file.name), migration.migration_name)
            self.assertEqual(migration._contents(), migration2._contents())

    def test_serialize_backwars(self):

        if self.serializer_instance.supports_backward_migration:
            return

        try:
            migration = api.Migration("test", "a", "b")
            self.serializer_instance.save(tempfile.TemporaryFile(), migration)
            self.fail("Save should have raised an exception when saving migration instance that has"
                      "backward_script in serializer {} that doesn't support backward migrations"
            .format(self.serializer_instance))
        except api.MigrationError:
            pass


    def test_load_exception(self):
        migration = self._random_migtation()
        file = tempfile.TemporaryFile()
        self.serializer_instance.save(file, migration)
        try:
            self.serializer_instance.load(file)
            self.fail("Load should raise an exception when not given migration name")
        except ValueError:
            pass


    def test_serialization(self):
        if not self.migration or not self.serialized_migration:
            return
        file = StringIO.StringIO()

        self.serializer_instance.save(file, self.migration)

        self.assertEqual(self.serialized_migration, file.getvalue())

    def test_deserialization(self):
        if not self.migration or not self.serialized_migration:
            return

        file = StringIO.StringIO(self.serialized_migration)

        mig = self.serializer_instance.load(file, self.migration.migration_name)

        self.assertEqual(self.migration._contents(), mig._contents())



class XMLSerializerTest(unittest.TestCase, SerializerTest):
    serializer_instance =  serializer.XmlSerializer()
    migration = TEST_MIGRATION
    serialized_migration = """<migrations name="Test migration">
  <forward><![CDATA[CREATE TABLE auth_user_groups
(
  id serial NOT NULL,
  user_id integer NOT NULL,
  group_id integer NOT NULL,
  CONSTRAINT auth_user_groups_pkey PRIMARY KEY (id ),
  CONSTRAINT auth_user_groups_group_id_fkey FOREIGN KEY (group_id)
      REFERENCES auth_group (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT user_id_refs_id_831107f1 FOREIGN KEY (user_id)
      REFERENCES auth_user (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT auth_user_groups_user_id_group_id_key UNIQUE (user_id , group_id )
);]]></forward>
  <reverse><![CDATA[DROP TABLE auth_user_groups;]]></reverse>
</migrations>
"""

class PlaintextSerializerTest(unittest.TestCase, SerializerTest):
    serializer_instance = serializer.PlaintextSerializer()
    migration = TEST_MIGRATION_NO_BACK
    serialized_migration = """CREATE TABLE auth_user_groups
(
  id serial NOT NULL,
  user_id integer NOT NULL,
  group_id integer NOT NULL,
  CONSTRAINT auth_user_groups_pkey PRIMARY KEY (id ),
  CONSTRAINT auth_user_groups_group_id_fkey FOREIGN KEY (group_id)
      REFERENCES auth_group (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT user_id_refs_id_831107f1 FOREIGN KEY (user_id)
      REFERENCES auth_user (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT auth_user_groups_user_id_group_id_key UNIQUE (user_id , group_id )
);"""

class PickleSerializerTest(unittest.TestCase, SerializerTest):
    serializer_instance = serializer.PickleSerializer()



class RepositoryTestBad(unittest.TestCase):

#    repository_type = None

    def setUp(self):
        self.repository = repository.FileSystemRepository(os.path.join(REPO_DIR, "_repository_multiple_ids"))
        self.repository.file_extension = "sql"

    def test_migration_filenames(self):
        self.assertRaises(api.RepositoryError, getattr, self.repository, "migration_filenames")

class RepositoryTestOK(unittest.TestCase):
    def setUp(self):
        self.repository = repository.FileSystemRepository(os.path.join(REPO_DIR, "_repository_ok"))
        self.repository.file_extension = "sql"

    def test_migration_filenames(self):
        self.assertEqual(self.repository.migration_filenames, {
            0 :  "00000-initial.sql",
            100 : "00100-foo.sql",
            200 : "00200-bar.sql"
        })

    def test_migration_ids(self):
        self.assertEqual(self.repository.migration_ids,
            [0, 100, 200])

    def test_migration_names(self):
        self.assertEqual(self.repository.migration_names, {
            0 : 'initial',
            100 : 'foo',
            200 : 'bar'}
        )

    def test_max_migration(self):
        self.assertEqual(self.repository.max_version, 200)

class MockVersionCheck(object):

    def __init__(self):
        super(MockVersionCheck, self).__init__()
        self.version = 0

    def schema_update_script(self, version):
        return "SeT_ScHeMa({:05d})".format(version)

class ManagerNoBack(unittest.TestCase):

    def setUp(self):
        self.manager = api.Manager(
            repository.FileSystemRepository(os.path.join(REPO_DIR, "_repository_ok")),
            serializer.PlaintextSerializer(),
            MockVersionCheck(),
            transaction.TestTransaction()
        )

    def test_migrate(self):
        self.manager.version_check.version = 200
        self.assertRaises(api.MigrationError, self.manager.migrate_to, 0)
#        self.manager.migrate_to(0)



class ManagerTests(unittest.TestCase):
    def setUp(self):
        self.manager = api.Manager(
            repository.FileSystemRepository(os.path.join(REPO_DIR, "_manager_test_repository")),
            serializer.XmlSerializer(),
            MockVersionCheck(),
            transaction.TestTransaction()
        )

    def test_migate_id(self):
        self.assertEqual((False, [100, 200]), self.manager.get_migration_ids())

    def test_migate_id1a(self):
        self.assertEqual((False, [100, 200]), self.manager.get_migration_ids(200))

    def test_migate_id2(self):
        self.assertEqual((False, [100]), self.manager.get_migration_ids(100))

    def test_migate_id3(self):
        self.manager.version_check.version = 100
        self.assertEqual((False, [200]), self.manager.get_migration_ids())

    def test_migate_id4(self):
        self.manager.version_check.version = 200
        self.assertEqual((False, []), self.manager.get_migration_ids())

    def test_migate_id_back(self):
        self.manager.version_check.version = 200
        self.assertEqual((True, [200, 100]), self.manager.get_migration_ids(0))

    def test_migate_id_back_2(self):
        self.manager.version_check.version = 200
        self.assertEqual((True, [200]), self.manager.get_migration_ids(100))

    def test_migate_id_back_2(self):
        self.manager.version_check.version = 100
        self.assertEqual((True, [100]), self.manager.get_migration_ids(0))



    def test_migration_forward(self):
        self.manager.migrate_to(200)
        self.assertEqual(self.FORWARD_MIGRATION_CONTENTS, self.manager.transaction.contents)


    FORWARD_MIGRATION_CONTENTS = """CREATE TABLE auth_permission
(
id serial NOT NULL,
name character varying(50) NOT NULL,
content_type_id integer NOT NULL,
codename character varying(100) NOT NULL,
CONSTRAINT auth_permission_pkey PRIMARY KEY (id ),
CONSTRAINT content_type_id_refs_id_728de91f FOREIGN KEY (content_type_id)
    REFERENCES django_content_type (id) MATCH SIMPLE
    ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,
CONSTRAINT auth_permission_content_type_id_codename_key UNIQUE (content_type_id , codename )
):
SeT_ScHeMa(00100)
CREATE TABLE django_comment_flags
  (
    id serial NOT NULL,
    user_id integer NOT NULL,
    comment_id integer NOT NULL,
    flag character varying(30) NOT NULL,
    flag_date timestamp with time zone NOT NULL,
    CONSTRAINT django_comment_flags_pkey PRIMARY KEY (id ),
    CONSTRAINT django_comment_flags_comment_id_fkey FOREIGN KEY (comment_id)
        REFERENCES django_comments (id) MATCH SIMPLE
        ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT django_comment_flags_user_id_fkey FOREIGN KEY (user_id)
        REFERENCES auth_user (id) MATCH SIMPLE
        ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT django_comment_flags_user_id_comment_id_flag_key UNIQUE (user_id , comment_id , flag )
  )
SeT_ScHeMa(00200)
"""

