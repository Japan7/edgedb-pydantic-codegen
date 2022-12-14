# edgedb-pydantic-codegen

This library generates Python typesafe code for EdgeQL queries with [Pydantic](https://pydantic-docs.helpmanual.io/) parsed models.

## Install

```
pip install git+https://github.com/Japan7/edgedb-pydantic-codegen.git
```

## Usage

In an EdgeDB initialized project run

```
python3 -m edgedb_pydantic_codegen <directory>
```

where `<directory>` contains your `*.edgeql` queries.

## Generated code example

```py
import asyncio
from enum import Enum
from typing import cast

import orjson
from edgedb import AsyncIOExecutor
from pydantic import BaseModel, parse_raw_as

EDGEQL_QUERY = r"""
with
  discord_id := <int64>$discord_id,
  moecoins := <optional int32>$moecoins,
  blood_shards := <optional int32>$blood_shards,
  updated := (
    update waicolle::Player
    filter .user.discord_id = discord_id
    set {
      moecoins := .moecoins + (moecoins ?? 0),
      blood_shards := .blood_shards + (blood_shards ?? 0),
    }
  )
select updated {
  game_mode,
  moecoins,
  blood_shards,
  user: { discord_id },
}
"""


class WaicolleGameMode(str, Enum):
    WAIFU = "WAIFU"
    HUSBANDO = "HUSBANDO"
    ALL = "ALL"


class PlayerAddCoinsResultUser(BaseModel):
    discord_id: int


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
    parsed = await asyncio.to_thread(
        parse_raw_as, PlayerAddCoinsResult | None, resp, json_loads=orjson.loads
    )
    return cast(PlayerAddCoinsResult | None, parsed)
```
