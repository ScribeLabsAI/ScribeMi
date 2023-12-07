import requests
import json
from io import BytesIO
from typing import BinaryIO, Union
from scribeauth import ScribeAuth
from aws_requests_auth.aws_auth import AWSRequestsAuth
from datetime import datetime
from typing_extensions import TypedDict, Optional


class Env(TypedDict):
    API_URL: str
    IDENTITY_POOL_ID: str
    USER_POOL_ID: str
    CLIENT_ID: str
    REGION: str


class MITaskBase(TypedDict):
    jobid: str
    client: str
    status: str
    submitted: int


class MITask(MITaskBase, total=False):
    companyName: Optional[str]
    clientFilename: Optional[str]
    originalFilename: Optional[str]
    clientModelFilename: Optional[str]
    modelUrl: Optional[str]


class SubmitTaskParamsBase(TypedDict):
    filetype: str


class SubmitTaskParams(SubmitTaskParamsBase, total=False):
    filename: Optional[str]
    companyname: Optional[str]


class Value(TypedDict):
    value: str | int | float
    bbox: Optional[str]


class Item(TypedDict):
    tag: str
    term: str
    ogterm: str
    values: list[Value]


class Table(TypedDict):
    title: str
    columnsOrder: list[str]
    items: list[Item]


class MICollatedModelFundPerformance(TypedDict):
    date: Optional[str]
    tables: list[Table]


class MIModelFundPerformance(TypedDict):
    date: str
    tables: list[Table]


class MIModelFinancials(TypedDict):
    company: str
    dateReporting: str
    covering: str
    items: list[Item]


class UnauthenticatedException(Exception):
    """
    Exception raised when current token:

    - Is wrong
    - Has expired and needs to be updated
    """

    pass


class TaskNotFoundException(Exception):
    """
    Exception raised when trying to access an unexistent task.
    """

    pass


class InvalidFiletypeException(Exception):
    """
    Exception raised when trying to upload a file with a wrong filetype.

    Accepted values:
    'pdf', 'xlsx', 'xls', 'xlsm', 'doc', 'docx', 'ppt', 'pptx'
    """

    pass


class MI:
    def __init__(self, env):
        """
        Construct an MI client.

        :param env: environment vars.
        :type env: :typeddict:`~.Env`
        """
        self.env = env
        self.auth_client = ScribeAuth(
            {
                "client_id": env["CLIENT_ID"],
                "user_pool_id": env["USER_POOL_ID"],
                "identity_pool_id": env["IDENTITY_POOL_ID"],
            }
        )
        self.tokens = None
        self.user_id = None
        self.request_auth = None

    def authenticate(self, param):
        """
        To authenticate a user.

        It is possible to pass a dictionary with a Username and Password or a Refresh Token:

        :param username: usually an email address.
        :type username: str
        :param password: associated with this username.
        :type password: str

        Or

        :param refresh_token: Refresh Token to use.
        :type refresh_token: str
        """
        self.tokens = self.auth_client.get_tokens(**param)
        id_token = self.tokens.get("id_token")
        if id_token != None:
            self.user_id = self.auth_client.get_federated_id(id_token)
            self.credentials = self.auth_client.get_federated_credentials(
                self.user_id, id_token
            )
            host = self.env["API_URL"].split("/")[0]
            self.request_auth = AWSRequestsAuth(
                aws_access_key=self.credentials["AccessKeyId"],
                aws_secret_access_key=self.credentials["SecretKey"],
                aws_token=self.credentials["SessionToken"],
                aws_host=host,
                aws_region=self.env["REGION"],
                aws_service="execute-api",
            )
        else:
            raise UnauthenticatedException("Authentication failed")

    def reauthenticate(self):
        """
        To reauthenticate a user without sending parameters. Must be called after authenticate.
        """
        if self.tokens == None or self.user_id == None:
            raise UnauthenticatedException("Must authenticate before reauthenticating")
        refresh_token = self.tokens.get("refresh_token")
        if refresh_token != None:
            self.tokens = self.auth_client.get_tokens(refresh_token=refresh_token)
            id_token = self.tokens.get("id_token")
            if id_token != None:
                self.credentials = self.auth_client.get_federated_credentials(
                    self.user_id, id_token
                )
                host = self.env["API_URL"].split("/")[0]
                self.request_auth = AWSRequestsAuth(
                    aws_access_key=self.credentials["AccessKeyId"],
                    aws_secret_access_key=self.credentials["SecretKey"],
                    aws_token=self.credentials["SessionToken"],
                    aws_host=host,
                    aws_region=self.env["REGION"],
                    aws_service="execute-api",
                )
            else:
                raise UnauthenticatedException("Authentication failed")
        else:
            raise UnauthenticatedException("Authentication failed")

    def call_endpoint(self, method, path, data=None, params=None):
        """
        To call an endpoint.

        :meta private:
        :param method: HTTP method to use: GET, POST or DELETE.
        :type method: str
        :param path: URL path to use, not including any prefix.
        :type path: str
        :param data: request body to send.
        :type data: str
        :param params: URL query params.
        :type params: dict

        :return: JSON response.
        :rtype: str
        """
        if self.request_auth == None:
            raise UnauthenticatedException("Not authenticated")
        if self.credentials["Expiration"] < datetime.now(
            self.credentials["Expiration"].tzinfo
        ):
            self.reauthenticate()
        res = requests.request(
            method=method,
            url="https://{host}{path}".format(host=self.env["API_URL"], path=path),
            params=params,
            json=data,
            auth=self.request_auth,
        )
        if res.status_code == 200:
            return json.loads(res.text)
        elif res.status_code == 401 or res.status_code == 403:
            raise UnauthenticatedException(
                "Authentication failed ({})".format(res.status_code)
            )
        elif res.status_code == 404:
            raise TaskNotFoundException("Not found")
        else:
            raise Exception("Unexpected error ({})".format(res.status_code))

    def list_tasks(self, companyName=None) -> list[MITask]:
        """
        To list the tasks.

        :param companyName: list tasks for a specific company.
        :type companyName: str

        :return: list of tasks.
        :rtype: list[MITask]
        """
        params = {"includePresigned": True}
        if companyName != None:
            params["company"] = companyName
        return self.call_endpoint("GET", "/tasks", params=params).get("tasks")

    def get_task(self, jobid: str) -> MITask:
        """
        To get a task by jobid.

        :param jobid: jobid of the task to get.
        :type jobid: str

        :return: a task.
        :rtype: :typeddict:`~.MITask`
        """
        return self.call_endpoint("GET", "/tasks/{}".format(jobid))

    def fetch_model(self, task: MITask):
        """
        Fetch the model for a task.

        :param task: task to fetch the model for.
        :type task: MITask

        :return: model.
        :rtype: Union[:typeddict:`~.MIModelFundPerformance`, :typeddict:`~.MIModelFinancials`]
        """
        modelUrl = task.get("modelUrl")
        if modelUrl == None:
            raise Exception(
                "Cannot load model for task {}: model is not ready for export".format(
                    task.get("jobid")
                )
            )
        res = requests.get(modelUrl)
        if res.status_code == 200:
            return json.loads(res.text)
        elif res.status_code == 401 or res.status_code == 403:
            raise UnauthenticatedException(
                "{} Authentication failed (possibly due to timeout: try calling get_task immediately before fetch_model)".format(
                    res.status_code
                )
            )
        else:
            raise Exception("Unexpected error ({})".format(res.status_code))

    def consolidate_tasks(self, tasks: list[MITask]):
        """
        To consolidate tasks.

        :param tasks: list of tasks to consolidate.
        :type tasks: list[:typeddict:`~.MITask`]

        :return: consolidated model.
        :rtype: :typeddict:`~.MICollatedModelFundPerformance`
        """
        jobids = list(map(lambda task: task.get("jobid"), tasks))
        jobids_param = ";".join(jobids)
        res = self.call_endpoint("GET", "/fundportfolio?jobids={}".format(jobids_param))
        return res.model

    def submit_task(
        self, file_or_filename: Union[str, BytesIO, BinaryIO], params: SubmitTaskParams
    ):
        """
        To submit a task.

        :param file_or_filename: file to upload -- Union[str, BytesIO, BinaryIO]
        :param params: SubmitTaskParams -- Dictionary {filetype: “str”, filename: “Optional[str]”, companyname: “Optional[str]”}

        :return: jobid of the task.
        :rtype: str
        """
        filetype_list = ["pdf", "xlsx", "xls", "xlsm", "doc", "docx", "ppt", "pptx"]
        if params.get("filetype") not in filetype_list:
            raise InvalidFiletypeException(
                "Invalid filetype. Accepted values: 'pdf', 'xlsx', 'xls', 'xlsm', 'doc', 'docx', 'ppt', 'pptx'."
            )

        if isinstance(file_or_filename, str) and params.get("filename") == None:
            params["filename"] = file_or_filename

        post_res = self.call_endpoint("POST", "/tasks", params)
        put_url = post_res["url"]

        if isinstance(file_or_filename, str):
            with open(file_or_filename, "rb") as file:
                upload_file(file, put_url)
        else:
            return upload_file(file_or_filename, put_url)

        return post_res["jobid"]

    def delete_task(self, task: MITask):
        """
        To delete a task.

        :param task: task to delete.
        :type task: MITask

        :return: JSON response.
        :rtype: str
        """
        return self.call_endpoint("DELETE", "/tasks/{}".format(task["jobid"]))


def upload_file(file, url):
    res = requests.put(url, data=file)
    if res.status_code != 200:
        raise Exception("Error uploading file: {}".format(res.status_code))
