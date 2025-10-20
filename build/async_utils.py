"""
Utility functions for handling async operations in Tkinter applications
"""
import asyncio
import concurrent.futures
import threading
from functools import wraps


def run_async_in_thread(async_func):
    """
    Decorator to run async functions in a separate thread to avoid event loop conflicts
    """
    @wraps(async_func)
    def wrapper(*args, **kwargs):
        try:
            # Check if we're already in an event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in a running event loop, use thread pool
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, async_func(*args, **kwargs))
                    return future.result()
            else:
                # No event loop running, we can use asyncio.run
                return asyncio.run(async_func(*args, **kwargs))
        except RuntimeError:
            # No event loop exists, create a new one
            return asyncio.run(async_func(*args, **kwargs))
    return wrapper


def safe_async_run(async_func, *args, **kwargs):
    """
    Safely run an async function without causing event loop conflicts
    """
    try:
        # Check if we're already in an event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're in a running event loop, use thread pool
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, async_func(*args, **kwargs))
                return future.result()
        else:
            # No event loop running, we can use asyncio.run
            return asyncio.run(async_func(*args, **kwargs))
    except RuntimeError:
        # No event loop exists, create a new one
        return asyncio.run(async_func(*args, **kwargs))


def run_in_thread_pool(func, *args, **kwargs):
    """
    Run a synchronous function in a thread pool
    """
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(func, *args, **kwargs)
        return future.result()
