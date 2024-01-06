import os
import re
import subprocess
from dataclasses import dataclass
from dataclasses import field as dc_field
from pathlib import Path

import autoflake
import edgedb
import isort
from edgedb import describe
from edgedb.enums import Cardinality
from jinja2 import Environment, FileSystemLoader
from ruff.__main__ import find_ruff_bin

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
    "std::bytes": "str",
    "std::decimal": "Decimal",
    "std::datetime": "datetime",
    "std::duration": "timedelta",
    "cal::local_date": "date",
    "cal::local_time": "time",
    "cal::local_datetime": "datetime",
    "std::json": "Any",
}


@dataclass
class EdgeQLEnum:
    name: str
    members: tuple[str]


@dataclass
class EdgeQLLiteral:
    alias: str
    values: tuple[str]


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
    args: dict[str, EdgeQLArgument] = dc_field(default_factory=dict)
    optional_args: dict[str, EdgeQLArgument] = dc_field(default_factory=dict)
    return_type: str = "None"
    return_single: bool = True


class Generator:
    def __init__(self) -> None:
        self._client = edgedb.create_client()  # type: ignore

    def process_directory(self, directory: Path):
        print(f"Processing directory {directory}")
        for file in directory.glob("**/*.edgeql"):
            self.process_file(file)

    def process_file(self, file: Path):
        print(f"Processing {file}")
        with file.open("r") as f:
            query = f.read()

        process_data = ProcessData(query)

        describe_result = self._client._describe_query(query, inject_type_names=True)

        return_model = None
        if describe_result.output_type is not None:
            return_model_name = snake_to_camel(file.stem) + "Result"
            return_model = self.parse_model(
                return_model_name,
                describe_result.output_type,  # type: ignore
                process_data,
            )

            return_cardinality = describe_result.output_cardinality
            if return_cardinality is Cardinality.NO_RESULT:
                process_data.return_type = "None"
                process_data.return_single = True
            elif return_cardinality is Cardinality.AT_MOST_ONE:
                process_data.return_type = f"{return_model.name} | None"
                process_data.return_single = True
            elif return_cardinality is Cardinality.ONE:
                process_data.return_type = f"{return_model.name}"
                process_data.return_single = True
            elif return_cardinality is Cardinality.MANY:
                process_data.return_type = f"list[{return_model.name}]"
                process_data.return_single = False
            elif return_cardinality is Cardinality.AT_LEAST_ONE:
                process_data.return_type = f"list[{return_model.name}]"
                process_data.return_single = False

        if describe_result.input_type is not None:
            for name, arg in describe_result.input_type.elements.items(  # type: ignore
            ):
                type_str = self.parse_type(
                    name,
                    arg.type,
                    snake_to_camel(file.stem),
                    process_data,
                    prefer_literal=True,
                )
                is_json = type_str == "Any"
                if arg.cardinality in (Cardinality.AT_MOST_ONE, Cardinality.MANY):
                    process_data.optional_args[name] = EdgeQLArgument(
                        name, type_str, True, None, is_json
                    )
                else:
                    process_data.args[name] = EdgeQLArgument(
                        name, type_str, False, None, is_json
                    )

        self.save(file, process_data)

    def save(self, file: Path, process_data: ProcessData):
        jinja_env = Environment(loader=FileSystemLoader(Path(__file__).parent))
        template = jinja_env.get_template("template.py.jinja")

        rendered = template.render(
            stem=file.stem,
            query=process_data.query.strip(),
            literals=process_data.literals.values(),
            enums=process_data.enums.values(),
            models=process_data.models.values(),
            args=(
                list(process_data.args.values())
                + list(process_data.optional_args.values())
            ),
            return_type=process_data.return_type,
            return_single=process_data.return_single,
        )

        imports_fixed = isort.code(
            autoflake.fix_code(rendered, remove_all_unused_imports=True)
        )

        path = file.with_suffix(".py")
        with path.open("w") as f:
            f.write(imports_fixed)

        ruff = find_ruff_bin()
        completed_process = subprocess.run(
            [os.fsdecode(ruff), "format", path.absolute()]
        )
        if completed_process.returncode != 0:
            raise RuntimeError("Ruff failed to format the generated code")

    @classmethod
    def parse_type(
        cls,
        name: str,
        type: describe.AnyType,
        parent_model_name: str,
        process_data: ProcessData,
        prefer_literal: bool = False,
    ) -> str:
        type_str = None

        if isinstance(type, describe.ScalarType):
            assert type.base_type.name is not None
            type_str = TYPE_MAPPING.get(type.base_type.name, "Any")

        elif isinstance(type, describe.BaseScalarType):
            assert type.name is not None
            type_str = TYPE_MAPPING.get(type.name, "Any")

        elif isinstance(type, describe.EnumType):
            if (
                not prefer_literal and type.name is not None
            ):  # an enum present in the schema
                module, enum_name = type.name.split("::")
                if module != "default":
                    enum_name = module.title() + enum_name
                else:
                    enum_name = enum_name
                process_data.enums[enum_name] = EdgeQLEnum(enum_name, type.members)
                type_str = enum_name
            else:  # use a literal
                alias = (camel_to_snake(parent_model_name) + "_" + name).upper()
                process_data.literals[alias] = EdgeQLLiteral(alias, type.members)
                type_str = alias

        elif isinstance(type, describe.ObjectType):
            model_name = parent_model_name + snake_to_camel(name)
            cls.parse_model(
                model_name, type, process_data, prefer_literal=prefer_literal
            )
            type_str = model_name

        elif isinstance(type, describe.ArrayType):
            element_type_str = cls.parse_type(
                name,
                type.element_type,
                parent_model_name,
                process_data,
                prefer_literal=prefer_literal,
            )
            type_str = f"list[{element_type_str}]"

        if type_str is None:
            raise ValueError(f"Unknown type: {type}")

        return type_str

    @classmethod
    def parse_model(
        cls,
        model_name: str,
        type: describe.ObjectType,
        process_data: ProcessData,
        prefer_literal: bool = False,
    ) -> EdgeQLModel:
        new_model = EdgeQLModel(model_name)
        process_data.models[model_name] = new_model

        fields: dict[str, EdgeQLModelField] = {}
        for field_name, field in type.elements.items():
            # handle link props
            alias = None
            if field_name.startswith("@"):
                alias = field_name
                field_name = f"link_{field_name[1:]}"
            field_type = cls.parse_type(
                field_name,
                field.type,
                model_name,
                process_data,
                prefer_literal=prefer_literal,
            )
            is_optional = (
                field.is_implicit or field.cardinality is Cardinality.AT_MOST_ONE
            )
            fields[field_name] = EdgeQLModelField(
                field_name, field_type, is_optional, alias
            )

        if "id" in fields:
            if len(fields) == 1:
                fields["id"].optional = False
            elif fields["id"].optional:
                del fields["id"]

        new_model.fields = list(fields.values())

        return new_model


def snake_to_camel(snake_str: str) -> str:
    components = snake_str.split("_")
    return "".join(x.title() for x in components)


def camel_to_snake(camel_str: str) -> str:
    return re.sub("([A-Z])", "_\\1", camel_str).lower().lstrip("_")
