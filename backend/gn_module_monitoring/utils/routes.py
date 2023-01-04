from typing import Tuple

from flask import Response
from flask.json import jsonify
from marshmallow import Schema
from sqlalchemy.orm import Query
from werkzeug.datastructures import MultiDict

from gn_module_monitoring.monitoring.schemas import paginate_schema


def get_limit_offset(params: MultiDict) -> Tuple[int]:
    return params.pop("limit", 50), params.pop("offset", 1)


def paginate(query: Query, schema: Schema, limit: int, page: int) -> Response:
    result = query.paginate(page=page, error_out=False, max_per_page=limit)
    pagination_schema = paginate_schema(schema)
    data = pagination_schema().dump(
        dict(items=result.items, count=result.total, limit=limit, offset=page - 1)
    )
    return jsonify(data)


def filter_params(query: Query, params: MultiDict) -> Query:
    if len(params) != 0:
        query = query.filter_by(**params)
    return query
