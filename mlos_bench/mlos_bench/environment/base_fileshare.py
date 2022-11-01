"""
Base class for remote file shares.
"""

from abc import ABCMeta, abstractmethod

from mlos_bench.environment.base_service import Service


class FileShareService(Service, metaclass=ABCMeta):
    """
    An abstract base of all file shares.
    """

    def __init__(self, config):
        """
        Create a new file share with a given config.

        Parameters
        ----------
        config : dict
            Free-format dictionary that contains the file share configuration.
            It will be passed as a constructor parameter of the class
            specified by `class_name`.
        """
        super().__init__(config)

        self.register([
            self.download,
            self.upload,
        ])

    @abstractmethod
    def download(self, remote_path: str, local_path: str, recursive: bool = True):
        """
        Downloads contents from a remote share path to a local path.

        Parameters
        ----------
        remote_path : str
            Path to download from the remote file share, a file if recursive=False
            or a directory if recursive=True.
        local_path : str
            Path to store the downloaded content to.
        recursive : bool
            To download a single file if False, or recursively download a directory if True.
        """

    @abstractmethod
    def upload(self, local_path: str, remote_path: str, recursive: bool = True):
        """
        Uploads contents from a local path to remote share path.

        Parameters
        ----------
        local_path : str
            Path to the local directory to upload contents from.
        remote_path : str
            Path in the remote file share to store the downloaded content to.
        recursive : bool
            To upload a single file if False, or recursively upload a directory if True.
        """
