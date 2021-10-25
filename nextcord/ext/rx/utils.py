import asyncio

__all__ = [
    '_'
]

def _(coro):
    """This function runs ensures the future of a coroutine (ie from a lambda).
    """
    def run(*args):
        return asyncio.ensure_future(coro(*args), loop=asyncio.get_event_loop())
    return run
