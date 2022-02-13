import asyncio


def ensure_future(value) -> asyncio.Future:
    if is_future(value):
        return value
    loop = asyncio.get_running_loop()
    future = loop.create_future()
    future.set_result(value)
    return future


def is_future(value):
    return isinstance(value, (asyncio.Future, asyncio.Task))
