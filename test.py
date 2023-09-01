"""
test.py
"""

from typing import Any, Coroutine

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


async def ssh_rexec_start(host: str, port: int, cmd: str) -> SSHCompletedProcess:
    """Start an SSH command asynchronously and wait for the result"""
    async with asyncssh.connect(host=host, port=port) as conn:
        return await conn.run(cmd)


def test_ssh() -> None:
    """test ssh async funcs"""
    ssh_rexec_coroutine = ssh_rexec_start(host='host.docker.internal', port=2222, cmd='sleep 1; printenv')
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(ssh_rexec_coroutine)
    print(result.stdout)


if __name__ == "__main__":
    test_ssh()
    print("Done.")
