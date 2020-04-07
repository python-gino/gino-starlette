# gino-starlette

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/0bec53f18d3b49aea6f558a269df318a)](https://app.codacy.com/gh/python-gino/gino-starlette?utm_source=github.com&utm_medium=referral&utm_content=python-gino/gino-starlette&utm_campaign=Badge_Grade_Settings)

## Introduction

An extension for GINO to support starlette server.

## Usage

The common usage looks like this:

```python
from starlette.applications import Starlette
from gino.ext.starlette import Gino

app = Starlette()
db = Gino(app, **kwargs)
```

## Configuration

GINO adds a middleware to the Starlette app to setup and cleanup database according to
the configurations that passed in the `kwargs` parameter.

The config includes:

| Name                         | Description                                                                                                       | Default     |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------- | ----------- |
| `driver`                     | the database driver                                                                                               | `asyncpg`   |
| `host`                       | database server host                                                                                              | `localhost` |
| `port`                       | database server port                                                                                              | `5432`      |
| `user`                       | database server user                                                                                              | `postgres`  |
| `password`                   | database server password                                                                                          | empty       |
| `database`                   | database name                                                                                                     | `postgres`  |
| `dsn`                        | a SQLAlchemy database URL to create the engine, its existence will replace all previous connect arguments.        | N/A         |
| `retry_times`                | the retry times when database failed to connect                                                                   | `20`        |
| `retry_interval`             | the interval in **seconds** between each time of retry                                                            | `5`         |
| `pool_min_size`              | the initial number of connections of the db pool.                                                                 | N/A         |
| `pool_max_size`              | the maximum number of connections in the db pool.                                                                 | N/A         |
| `echo`                       | enable SQLAlchemy echo mode.                                                                                      | N/A         |
| `ssl`                        | SSL context passed to `asyncpg.connect`                                                                           | `None`      |
| `use_connection_for_request` | flag to set up lazy connection for requests.                                                                      | N/A         |
| `retry_limit`                | the number of retries to connect to the database on start up.                                                     | 1           |
| `retry_interval`             | seconds to wait between retries.                                                                                  | 1           |
| `kwargs`                     | other parameters passed to the specified dialects, like `asyncpg`. Unrecognized parameters will cause exceptions. | N/A         |

## Lazy Connection

If `use_connection_for_request` is set to be True, then a lazy connection is available
at `request['connection']`. By default, a database connection is borrowed on the first
query, shared in the same execution context, and returned to the pool on response.
If you need to release the connection early in the middle to do some long-running tasks,
you can simply do this:

```python
await request['connection'].release(permanent=False)
```
