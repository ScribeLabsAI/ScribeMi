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

        Args
        ----
        url -- For the application to use
        api_key -- The api key for the application.
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
        params = {"includePresigned": True}
        if companyName != None:
            params["company"] = companyName
        return self.call_endpoint("GET", "/tasks", params=params).get("tasks")

    def get_task(self, jobid: str) -> MITask:
        return self.call_endpoint("GET", "/tasks/{}".format(jobid))

    def fetch_model(self, task: MITask):
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
        jobids = list(map(lambda task: task.get("jobid"), tasks))
        jobids_param = ";".join(jobids)
        res = self.call_endpoint("GET", "/fundportfolio?jobids={}".format(jobids_param))
        return res.model

    def submit_task(
        self, file_or_filename: Union[str, BytesIO, BinaryIO], params: SubmitTaskParams
    ):
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
        return self.call_endpoint("DELETE", "/tasks/{}".format(task["jobid"]))


def upload_file(file, url):
    res = requests.put(url, data=file)
    if res.status_code != 200:
        raise Exception("Error uploading file: {}".format(res.status_code))
