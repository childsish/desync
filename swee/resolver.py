import inspect


async def resolve(value):
    while inspect.isawaitable(value):
        value = await resolve_future(value)
    if isinstance(value, dict):
        value = await resolve_dict(value)
    elif isinstance(value, (list, tuple)):
        value = await resolve_sequence(value)
    return value


async def resolve_dict(value):
    return {key: await resolve(value) for key, value in value.items()}


async def resolve_future(value):
    return await value


async def resolve_sequence(value):
    return [await resolve(item) for item in value]
