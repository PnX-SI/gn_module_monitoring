import collections.abc


def to_int(s):
    try:
        return int(s)
    except Exception:
        return None


def dict_deep_update(dct, merge_dct):
    """Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``.
    :param dct: dict onto which the merge is executed
    :param merge_dct: dct merged into dct
    :return: None
    """
    for k, v in merge_dct.items():
        if (
            k in dct
            and isinstance(dct[k], dict)
            and isinstance(merge_dct[k], collections.abc.Mapping)
        ):
            dict_deep_update(dct[k], merge_dct[k])
        else:
            dct[k] = merge_dct[k]


def extract_keys(test_dict, keys=None):
    """
    Fonction permettant d'extraire de façon récursive les clés d'un dictionnaire
    """
    if not keys:
        keys = []
    for key, val in test_dict.items():
        keys.append(key)
        if isinstance(val, dict):
            extract_keys(val, keys)
    return keys
