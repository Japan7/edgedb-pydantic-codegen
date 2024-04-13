from dataclasses import dataclass
from dataclasses import field as dc_field

TYPE_MAPPING = {
    "std::str": "str",
    "std::float32": "float",
    "std::float64": "float",
    "std::int16": "int",
    "std::int32": "int",
    "std::int64": "int",
    "std::bigint": "int",
    "std::bool": "bool",
    "std::uuid": "UUID",
    "std::bytes": "bytes",
    "std::decimal": "Decimal",
    "std::datetime": "datetime",
    # "std::duration": "timedelta",
    "std::json": "Any",
    "cal::local_date": "date",
    "cal::local_time": "time",
    "cal::local_datetime": "datetime",
    # "cal::relative_duration": "RelativeDuration",
    # "cal::date_duration": "DateDuration",
    # "cfg::memory": "ConfigMemory",
    # "ext::pgvector::vector": "array",
}


@dataclass
class EdgeQLEnumMember:
    name: str
    value: str


@dataclass
class EdgeQLEnum:
    name: str
    members: list[EdgeQLEnumMember]


@dataclass
class EdgeQLLiteral:
    alias: str
    values: tuple[str, ...]


@dataclass
class EdgeQLNamedTuple:
    name: str
    fields: list["EdgeQLNamedTupleField"] = dc_field(default_factory=list)


@dataclass
class EdgeQLNamedTupleField:
    name: str
    type_str: str


@dataclass
class EdgeQLModel:
    name: str
    fields: list["EdgeQLModelField"] = dc_field(default_factory=list)


@dataclass
class EdgeQLModelField:
    name: str
    type_str: str
    optional: bool
    alias: str | None


@dataclass
class EdgeQLArgument(EdgeQLModelField):
    is_json: bool


@dataclass
class ProcessData:
    query: str
    literals: dict[str, EdgeQLLiteral] = dc_field(default_factory=dict)
    enums: dict[str, EdgeQLEnum] = dc_field(default_factory=dict)
    models: dict[str, EdgeQLModel] = dc_field(default_factory=dict)
    namedtuples: dict[str, EdgeQLNamedTuple] = dc_field(default_factory=dict)
    args: dict[str, EdgeQLArgument] = dc_field(default_factory=dict)
    optional_args: dict[str, EdgeQLArgument] = dc_field(default_factory=dict)
    return_type: str = "None"
    return_single: bool = True
