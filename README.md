# edgedb-pydantic-codegen

This tool generates Python typesafe async code for EdgeQL queries using [Pydantic V2](https://github.com/pydantic/pydantic).

The generated models can be directly used with other libraries such as [FastAPI](https://github.com/tiangolo/fastapi).

This is an alternative to the [built-in code generator](https://github.com/edgedb/edgedb-python/tree/master/edgedb/codegen) of the official [edgedb-python](https://github.com/edgedb/edgedb-python/tree/master) library.

## Install

<p>
  <a href="https://pypi.org/project/edgedb-pydantic-codegen" alt="Python version compatibility">
    <img src="https://img.shields.io/pypi/pyversions/edgedb-pydantic-codegen" /></a>
  <a href="https://pypi.org/project/edgedb-pydantic-codegen" alt="PyPI version">
    <img src="https://img.shields.io/pypi/v/edgedb-pydantic-codegen" /></a>
  <a href="https://calver.org" alt="Calendar Versioning scheme">
    <img src="https://img.shields.io/badge/calver-YYYY.0M.MICRO-22bfda" /></a>
</p>

```sh
pip3 install edgedb-pydantic-codegen
```

## Usage

In an EdgeDB initialized project, simply run

```sh
edgedb-pydantic-codegen <directory>
```

All `*.edgeql` files in `<directory>` and its subdirectories will be processed and the generated code saved next to them.

## Generated code example

```py
from enum import StrEnum

from edgedb import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <int64>$discord_id,
  moecoins := <optional int32>$moecoins,
  blood_shards := <optional int32>$blood_shards,
  updated := (
    update waicolle::Player
    filter .client = global client and .user.discord_id = discord_id
    set {
      moecoins := .moecoins + (moecoins ?? 0),
      blood_shards := .blood_shards + (blood_shards ?? 0),
    }
  )
select updated {
  game_mode,
  moecoins,
  blood_shards,
  user: {
    discord_id,
    discord_id_str,
  },
}
"""


class WaicolleGameMode(StrEnum):
    WAIFU = "WAIFU"
    HUSBANDO = "HUSBANDO"
    ALL = "ALL"


class PlayerAddCoinsResultUser(BaseModel):
    discord_id: int
    discord_id_str: str


class PlayerAddCoinsResult(BaseModel):
    game_mode: WaicolleGameMode
    moecoins: int
    blood_shards: int
    user: PlayerAddCoinsResultUser


adapter = TypeAdapter(PlayerAddCoinsResult | None)


async def player_add_coins(
    executor: AsyncIOExecutor,
    *,
    discord_id: int,
    moecoins: int | None = None,
    blood_shards: int | None = None,
) -> PlayerAddCoinsResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
        moecoins=moecoins,
        blood_shards=blood_shards,
    )
    return adapter.validate_json(resp, strict=False)
```
