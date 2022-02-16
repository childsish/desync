import inspect


async def resolve(value):
    while inspect.isawaitable(value):
        value = await resolve_future(value)
    if isinstance(value, dict):
        value = await resolve_dict(value)
    elif isinstance(value, list):
        value = await resolve_list(value)
    elif isinstance(value, set):
        value = await resolve_set(value)
    elif isinstance(value, tuple):
        value = await resolve_tuple(value)
    return value


async def resolve_dict(value):
    return {key: await resolve(value) for key, value in value.items()}


async def resolve_future(value):
    return await value


async def resolve_list(value):
    return [await resolve(item) for item in value]


async def resolve_set(value):
    return set([await resolve(item) for item in value])


async def resolve_tuple(value):
    return tuple([await resolve(item) for item in value])
