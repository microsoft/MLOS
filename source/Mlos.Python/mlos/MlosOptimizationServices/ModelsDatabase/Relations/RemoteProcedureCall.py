#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
class RemoteProcedureCall:
    """ Represents a single row in the RemoteProcedureCalls table in the ModelsDatabase.

    """

    def __init__(
            self,
            request_id=None,
            request_submission_time=None,
            request_status=None,
            expected_current_status=None,
            remote_procedure_name=None,
            execution_context=None,
            arguments=None,
            result=None,
            timeout_dt=None
    ):
        self.request_id = request_id
        self.request_submission_time = request_submission_time
        self.request_status = request_status
        self.expected_current_status = expected_current_status
        self.remote_procedure_name = remote_procedure_name
        self.execution_context = execution_context
        self.arguments = arguments
        self.result = result
        self.timeout_dt = timeout_dt
