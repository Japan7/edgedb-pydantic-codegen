# edgedb-pydantic-codegen

This library generates Python typesafe code for EdgeQL queries with [Pydantic](https://pydantic-docs.helpmanual.io/) parsed models.

## Install

```sh
pip install edgedb-pydantic-codegen
```

## Usage

In an EdgeDB initialized project run

```sh
edgedb_pydantic_codegen <directory>
```

where `<directory>` contains your `*.edgeql` queries.

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
    return TypeAdapter(PlayerAddCoinsResult | None).validate_json(resp, strict=False)
```
