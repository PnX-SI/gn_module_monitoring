import json

from jinja2.utils import markupsafe


def json_formatter(view, context, model, name):
    """Prettify JSON data in flask admin lists"""
    value = getattr(model, name)
    json_value = json.dumps(value, ensure_ascii=False, indent=2)
    return markupsafe.Markup("<pre style='max-height: 500px;'>{}</pre>".format(json_value))
