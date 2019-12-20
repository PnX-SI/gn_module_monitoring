from json import load
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def validable(cls):
    """
        Décorateur de classe
        Ajoute une fonction de valider des jsonschema sur un colonne JSONB
    """

    def is_valid(self, col_name, file_schema_path):
        """
        Function qui renvoie True si la colonne indiquée par colname est
        conforme au schema contenu dans le fichier de chemin file_schema_path,
        False Sinon.
        Renvoie None si la colonne référencée par col_name n'existe pas ou n'
        est pas de type JSONB.

        :param col_name: Nom de la colonne
        :param file_schema_path: chemin absolu du fichier contenant le schema
        """

        # test col_name valide
        data = getattr(self, col_name)
        if not data:
            return

        # test type JSONB
        type = getattr(cls.__mapper__.c, col_name).type

        if not str(type)[:5] == "JSONB":
            return

        # test si l'objet json est conforme au schema
        with open(file_schema_path, 'r') as f:
            schema = load(f)

            try:
                data = getattr(self, col_name)
                validate(instance=data, schema=schema)
                return True

            except ValidationError:
                return False

    cls.is_valid = is_valid
    return cls
