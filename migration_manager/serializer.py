# -*- coding: utf-8 -*-
__author__ = 'jb'

# -*- coding: utf-8 -*-
__author__ = 'jb'

import api
import codecs
from lxml import objectify, etree


class PickleSerializer(api.Serializer):
    """
        Just a toy! Rather use migrations that are user editable!
    """

    supports_backward_migration = True
    extension = "bin"
    saves_migration_name = True

    def _save(self, file, migration):
        import pickle
        pickle.dump(migration, file)

    def _load(self, file, migration_name, is_guess):
        import pickle
        return pickle.load(file)


class XmlSerializer(api.Serializer):


    """
        Migrations serialized to following format::

             <migrations>
                <forward>

                </forward>
                <backward>

                </backward>
             </migrations>

        Migration text's are stored in CDATA sestions to make it easier to edit by hant

    """


    supports_backward_migration = True
    extension = "xml"
    saves_migration_name = True

    def _load(self, file, migration_name, name_guessed):

        root = objectify.parse(file).getroot()
        return api.Migration(
            migration_name= root.get("name") if name_guessed else migration_name,
            forward_script=root.forward,
            backward_script=getattr(root, "reverse", None)
        )


    def _save(self, file, obj):
    #        E = objectify.E
        migrations = etree.Element("migrations", name=obj.migration_name)
        forward = etree.SubElement(migrations, "forward")
        forward.text = etree.CDATA(obj.forward_script)
        if obj.backward_script:
            reverse = etree.SubElement(migrations, "reverse")
            reverse.text = etree.CDATA(obj.backward_script)

        file.write(etree.tostring(migrations, pretty_print=True))

        file.flush()

class PlaintextSerializer(api.Serializer):

    """
        Serializer saving files as utf8 encoded plain files.
    """

    supports_backward_migration = False

    extension = "sql"

    saves_migration_name = False

    def __init__(self, encoding = "utf-8"):
        super(PlaintextSerializer, self).__init__()
        self.encoding = encoding

    def _save(self, file, obj):

        file.write(codecs.encode(obj.forward_script, self.encoding))
        file.flush()

    def _load(self, file, migration_name, name_guessed):
        return api.Migration(
            migration_name= migration_name,
            forward_script= codecs.decode(file.read(), self.encoding),
            backward_script=None
        )
