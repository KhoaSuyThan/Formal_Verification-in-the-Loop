"""Bounded parallel execution for independent benchmark cases.

Only worker functions run in background threads. Callers consume results and
update their UI or output files on the main thread.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from typing import TypeVar


Task = TypeVar("Task")
Result = TypeVar("Result")


def iter_completed(
    tasks: Iterable[Task],
    worker: Callable[[Task], Result],
    *,
    workers: int = 1,
    stop_requested: Callable[[], bool] | None = None,
) -> Iterator[tuple[int, Task, Result]]:
    """Yield completed cases with a bounded number of in-flight tasks.

    Indices refer to input order, even when parallel tasks finish out of order.
    A stop request prevents further submissions; tasks already running finish.
    Exceptions from workers are propagated instead of being counted as results.
    """
    if workers < 1:
        raise ValueError("workers must be at least 1")

    numbered = iter(enumerate(tasks))

    def stopped() -> bool:
        return bool(stop_requested and stop_requested())

    if workers == 1:
        for index, task in numbered:
            if stopped():
                break
            yield index, task, worker(task)
        return

    with ThreadPoolExecutor(max_workers=workers) as executor:
        pending: dict[Future[Result], tuple[int, Task]] = {}

        def submit_next() -> bool:
            if stopped():
                return False
            try:
                index, task = next(numbered)
            except StopIteration:
                return False
            pending[executor.submit(worker, task)] = (index, task)
            return True

        for _ in range(workers):
            if not submit_next():
                break

        while pending:
            done, _ = wait(pending, return_when=FIRST_COMPLETED)
            for future in sorted(done, key=lambda item: pending[item][0]):
                index, task = pending.pop(future)
                result = future.result()
                submit_next()
                yield index, task, result
