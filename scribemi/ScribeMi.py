import requests
import json
from io import BytesIO
from typing import BinaryIO, Union
from scribeauth import ScribeAuth
from datetime import datetime
from typing_extensions import TypedDict, Optional, List
from hashlib import md5
from base64 import b64encode


class Env(TypedDict):
    """
    Represents the environment configuration.
    """

    API_URL: str
    """
    The URL of the API.
    """
    USER_POOL_ID: str
    """
    The ID of the user pool.
    """
    CLIENT_ID: str
    """
    The ID of the client.
    """
    REGION: str
    """
    The region where the resources are located.
    """


class MITaskBase(TypedDict):
    """
    Represents a base MI task.
    """

    jobid: str
    """
    The ID of the task.
    """
    client: str
    """
    The client associated with the task.
    """
    status: str
    """
    The status of the task.
    """
    submitted: int
    """
    The timestamp when the task was submitted.
    """


class MITask(MITaskBase, total=False):
    """
    Represents a MI task.
    """

    companyName: Optional[str]
    """
    The name of the company associated with the task.
    """
    clientFilename: Optional[str]
    """
    The filename of the client's document.
    """
    originalFilename: Optional[str]
    """
    The original filename of the document.
    """
    clientModelFilename: Optional[str]
    """
    The filename of the client's model.
    """
    modelUrl: Optional[str]
    """
    The URL of the model associated with the task.
    """


class SubmitTaskParamsBase(TypedDict):
    filetype: str


class SubmitTaskParams(SubmitTaskParamsBase, total=False):
    filename: Optional[str]
    companyname: Optional[str]


class Value(TypedDict):
    """
    Represents a value with optional bounding box information.
    """

    value: str | int | float
    """
    The actual value, which can be a string, integer, or float.
    """
    bbox: Optional[str]
    """
    The bounding box information for the value, if available.
    """


class Item(TypedDict):
    """
    Represents an item with its attributes.

    :param values: The list of values associated with the item.
    :type values: List[:typeddict:`~.Value`]
    """

    tag: str
    """
    The tag of the item.
    """
    term: str
    """
    The term of the item.
    """
    ogterm: str
    """
    The original term of the item.
    """
    values: List[Value]
    """
    The list of values associated with the item.
    """


class Table(TypedDict):
    """
    Represents a table with a title, column order, and items.

    :param items: The list of items in the table.
    :type items: List[:typeddict:`~.Item`]
    """

    title: str
    """
    The title of the table.
    """
    columnsOrder: List[str]
    """
    The order of the columns in the table.
    """
    items: List[Item]
    """
    The list of items in the table.
    """


class MICollatedModelFundPerformance(TypedDict):
    """
    Represents the MI collated model fund performance.
    """

    date: Optional[str]
    """
    The date of the performance.
    """
    tables: List[Table]
    """
    The list of tables containing fund performance data.
    """


class MIModelFundPerformance(TypedDict):
    """
    Represents the MI model of the fund performance.
    """

    date: str
    """
    The date of the fund performance data.
    """
    tables: List[Table]
    """
    A list of tables containing the fund performance details.
    """


class MIModelFinancials(TypedDict):
    """
    Represents the MI model for financials.

    :param items: The list of financial items.
    :type items: List[:typeddict:`~.Item`]
    """

    company: str
    """
    The name of the company.
    """

    dateReporting: str
    """
    The date of the financial reporting.
    """

    covering: str
    """
    The period covered by the financial information.
    """

    items: List[Item]
    """
    The list of financial items.
    """


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


class MissingFilenameException(Exception):
    """
    Exception raised when trying to upload a file without specifying a filename
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
            }
        )
        self.tokens = None

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
        access_token = self.tokens.get("access_token")
        if access_token == None:
            raise UnauthenticatedException("Authentication failed")

    def reauthenticate(self):
        """
        To reauthenticate a user without sending parameters. Must be called after authenticate.
        """
        if self.tokens == None:
            raise UnauthenticatedException("Must authenticate before reauthenticating")
        refresh_token = self.tokens.get("refresh_token")
        if refresh_token == None:
            raise UnauthenticatedException("Reuthentication failed (no refresh token)")

        self.tokens = self.auth_client.get_tokens(refresh_token=refresh_token)
        access_token = self.tokens.get("access_token")
        if access_token == None:
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
        if self.tokens == None:
            raise UnauthenticatedException("Not authenticated")
        res = requests.request(
            method=method,
            url="https://{host}{path}".format(host=self.env["API_URL"], path=path),
            params=params,
            json=data,
            headers={"Authorization": self.tokens["access_token"]},
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

    def list_tasks(self, companyName=None) -> List[MITask]:
        """
        To list the tasks.

        :param companyName: list tasks for a specific company.
        :type companyName: str

        :return: list of tasks.
        :rtype: List[:typeddict:`~.MITask`]
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
        :type task: :typeddict:`~.MITask`

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
            verify_etag_checksum(res)

            return json.loads(res.text)
        elif res.status_code == 401 or res.status_code == 403:
            raise UnauthenticatedException(
                "{} Authentication failed (possibly due to timeout: try calling get_task immediately before fetch_model)".format(
                    res.status_code
                )
            )
        else:
            raise Exception("Unexpected error ({})".format(res.status_code))

    def consolidate_tasks(self, tasks: List[MITask]):
        """
        To consolidate tasks.

        :param tasks: list of tasks to consolidate.
        :type tasks: List[:typeddict:`~.MITask`]

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
        :param params: SubmitTaskParams -- Dictionary {filetype: “str”, md5checksum: “str”, filename: “Optional[str]”, companyname: “Optional[str]”}

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

        if params["filename"] == None:
            raise MissingFilenameException()

        if isinstance(file_or_filename, str):
            with open(file_or_filename, "rb") as file:
                file_content = file.read()
        else:
            file_content = file_or_filename.read()

        hash = md5(file_content, usedforsecurity=False)
        md5checksum = b64encode(hash.digest()).decode()
        params["md5checksum"] = md5checksum

        post_res = self.call_endpoint("POST", "/tasks", params)
        put_url = post_res["url"]

        upload_file(file_content, md5checksum, put_url)

        return post_res["jobid"]

    def delete_task(self, task: MITask):
        """
        To delete a task.

        :param task: task to delete.
        :type task: :typeddict:`~.MITask`

        :return: JSON response.
        :rtype: str
        """
        return self.call_endpoint("DELETE", "/tasks/{}".format(task["jobid"]))


def upload_file(file, md5checksum, url):
    res = requests.put(url, data=file, headers={"Content-MD5": md5checksum})
    if res.status_code != 200:
        raise Exception("Error uploading file: {}".format(res.status_code))


def verify_etag_checksum(res: requests.Response):
    md5checksum_expected = res.headers["ETag"].replace('"', "")
    md5checksum = md5(res.text.encode(), usedforsecurity=False).hexdigest()
    if md5checksum != md5checksum_expected:
        raise Exception("Integrity Error: invalid checksum. Please retry.")
