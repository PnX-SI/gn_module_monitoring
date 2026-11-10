from marshmallow import Schema, fields

from gn_module_monitoring.monitoring.schemas import GenericAdditionalSchema


class DummySchema(Schema):
    name = fields.String()
    specific = fields.Function(lambda obj: (obj.get("data") or {}).get("specific"))
    data = fields.Raw()


class DummySchemaWithAdditional(DummySchema, GenericAdditionalSchema):
    pass


class TestGenericAdditionalSchema:
    def test_additional_data_keys(self):
        obj = {
            "name": "foo",
            "data": {"specific": "declared", "other_module_prop": 42, "name": "ignored"},
        }
        dumped = DummySchemaWithAdditional().dump(obj)

        # `data` est mis à plat
        assert "data" not in dumped
        assert dumped["specific"] == "declared"
        assert dumped["other_module_prop"] == 42
        # Une valeur déjà présente n'est pas écrasée par `data`
        assert dumped["name"] == "foo"
        # Seules les clés non déclarées dans le schéma sont listées
        assert dumped["additional_data_keys"] == ["other_module_prop"]

    def test_additional_data_keys_no_duplicate(self):
        obj = {"name": "foo", "data": {"other_module_prop": 42}}
        dumped = DummySchemaWithAdditional().dump(obj)
        assert dumped["additional_data_keys"].count("other_module_prop") == 1

    def test_additional_data_keys_empty_data(self):
        for data in (None, {}):
            dumped = DummySchemaWithAdditional().dump({"name": "foo", "data": data})
            assert "data" not in dumped
            assert "additional_data_keys" not in dumped

    def test_additional_data_keys_many(self):
        objs = [
            {"name": "foo", "data": {"prop_a": 1}},
            {"name": "bar", "data": {"prop_b": 2}},
        ]
        dumped = DummySchemaWithAdditional(many=True).dump(objs)
        assert dumped[0]["additional_data_keys"] == ["prop_a"]
        assert dumped[1]["additional_data_keys"] == ["prop_b"]
