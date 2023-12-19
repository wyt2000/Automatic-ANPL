import asyncio
from typing import Callable, Coroutine

__all__ = ['await_with_semaphone']

async def await_with_semaphone(async_func: Callable[[...], Coroutine], semaphone: asyncio.Semaphore, *args):
    # Use with semaphone to limit active coroutine numbers
    async with semaphone:
        return await async_func(*args)