"""
test.py
"""

import pytest
from threading import Thread

import os

from typing import Any, Coroutine, Optional, Tuple

from concurrent.futures import Future

from asyncio import Task
import asyncio
import asyncssh
import time

from asyncio import AbstractEventLoop
from asyncssh import SSHCompletedProcess

from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.services.remote.ssh.ssh_fileshare import SshFileShareService


def test_multi_inheritence() -> None:
    """Debugging multi-inheritence"""

    config_service = ConfigPersistenceService({}, {}, None)

    ssh_fileshare = SshFileShareService({
        "hostname": "localhost",
        "username": "username",
    }, {}, config_service)

    print(ssh_fileshare)
    print(ssh_fileshare.__class__.__mro__)


async def async_func() -> str:
    """Asynchronously wait 1 second"""
    start_ts = time.time()
    time.sleep(1)
    end_ts = time.time()
    return f"{async_func.__name__}: {start_ts} + {end_ts - start_ts} = {end_ts}"


async def async_main() -> None:
    """Main function"""
    start_ts = time.time()
    coroutine = async_func()
    cur_ts = time.time()
    print(f"{async_main.__name__}: {start_ts} + {cur_ts - start_ts} = {cur_ts}")
    result = await coroutine
    print(result)


async def ssh_rexec(host: str, port: int, username: Optional[str], cmd: str) -> SSHCompletedProcess:
    """Start an SSH command asynchronously and wait for the result"""
    connect_kwargs = {
        'host': host,
        'port': port,
        'known_hosts': None,
    }
    if username:
        connect_kwargs['username'] = username
    async with asyncssh.connect(**connect_kwargs) as conn:
        return await conn.run(cmd)


def start_ssh_coroutine(ssh_coroutine: Coroutine[Any, Any, SSHCompletedProcess], result: dict, i: int) -> None:
    """Start the SSH Coroutine in an event loop and return a future."""
    result[f'result_{i}'] = asyncio.run(ssh_coroutine)
    return


def test_ssh() -> None:
    """test ssh async funcs"""
    # Dev note: submitting things to a loop on its own does nothing - we need to run the loop.
    #loop = asyncio.get_event_loop()
    #result = loop.run_until_complete(ssh_rexec_coroutine)

    threads = []
    tasks: Task[SSHCompletedProcess] = list()
    results_dict = {}
    for i in range(0, 3):
        ssh_rexec_coroutine = ssh_rexec(
            host='host.docker.internal',
            port=2222,
            username=os.getenv('LOCAL_USER_NAME', os.getenv('USER', os.getenv('USERNAME', None))),
            cmd='sleep 1; printenv')

        #thread = Thread(target=start_ssh_coroutine, args=[ssh_rexec_coroutine, results_dict, i])
        #thread.start()
        #threads.append(thread)
        print("ssh_rexec_coroutine running in background ...")
        #thread.join()

        task = asyncio.create_task(ssh_rexec_coroutine, str(i))
        tasks.append(task)

    for i in range(0, 3):
        #thread = threads[i]
        #thread.join()
        #print(results_dict[f'result_{i}'].stdout)

        task = tasks[i]
        result = task.result()
        print(result.stdout)



if __name__ == "__main__":
    test_ssh()
    print("Done.")
