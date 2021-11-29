from __future__ import annotations


async def hello_world(foobar):
    await foobar()
    foo = await foobar()
    bar = await (await foo)
    (qux := foobar(await foo))
    return bar, qux
