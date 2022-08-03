import requests
import json
from io import BytesIO
from typing import BinaryIO, List, Optional, TypedDict, Union

class Job(TypedDict):
    filename: str
    status: str
    url: Optional[str]

class Archive(TypedDict):
    name: str
    url: str
    last_modified: str

class JobCreated(TypedDict):
    jobid: str
    url: str

class MI:
    def __init__(self, url: str, api_key: str):
        """
        Construct an MI client.

        Args
        ----
        url -- For the application to use
        api_key -- The api key for the application.
        """
        self.url = url
        self.headers = {'x-api-key' : api_key}

    def update_id_token(self, id_token: str) -> None:
        """
        Updates id token to be able to use the service.

        Args
        ----
        id_token -- Id token to access archives and jobs.
        """
        self.headers.update({'Authorization' : id_token})

    def list_archives(self) -> list[Archive]:
        """
        List all the archives uploaded.
                
        Returns
        ----
        list[Archive] -- List of Dictionary {"name": "str", "url": "str", "last_modified": "str"}
        """
        response = requests.get(self.url + '/archives', headers=self.headers)
        self.__validate_response(response)
        body = json.loads(response.text).get('archives')
        archives: List = []
        for a in body:
            archives.append(Archive(name=a.get('key'), url=a.get('link'), last_modified=a.get('lastModified')))
        return archives

    def delete_archive(self, filename: str) -> True:
        """
        Delete archive by name.
                
        Args
        ----
        filename -- Name of the archive to delete.

        Returns
        ----
        bool
        """
        response = requests.delete(self.url + '/archive', headers=self.headers, json={'key': filename})
        self.__validate_response(response)
        return True

    def upload_archive(self, file_or_filename: Union[str, BytesIO, BinaryIO]) -> True:
        """
        Upload archive by filepath or file loaded in memory.
                               
        Args
        ----
        file_or_filename -- Filepath of the file or file present in memory ready to be uploaded.

        Returns
        ----
        bool
        """
        response_get_link = requests.get(self.url + '/archive', headers=self.headers)
        self.__validate_response(response_get_link)
        url = json.loads(response_get_link.content)
        if isinstance(file_or_filename, str):
            file = open(file_or_filename, 'rb')
        else:
            file = file_or_filename
        response = requests.put(url, headers={'Content-Type' : 'application/zip'}, files={'file': file})
        self.__validate_response(response)
        return url.split('?')[0].split('/')[-1].replace('%3A', ':')

    def create_job(self, file_or_filename: Union[str, BytesIO, BinaryIO], filetype, filename: Optional[str] = None) -> JobCreated:
        """
        Create and upload job.
                               
        Args
        ----
        file_or_filename -- Filepath of the file or file present in a var in memory ready to be uploaded.

        Returns
        ----
        JobCreated -- Dictionary {"jobid": "str", "url": "str"}
        """
        filetype_list = ['pdf', 'xlsx', 'xls', 'xlsm', 'doc', 'docx', 'ppt', 'pptx']
        if filetype not in filetype_list:
            raise Exception("Invalid filetype. Accepted values: 'pdf', 'xlsx', 'xls', 'xlsm', 'doc', 'docx', 'ppt', 'pptx'.")
        if isinstance(file_or_filename, str):
            file = open(file_or_filename, 'rb')
        else:
            file = file_or_filename
        headers = self.headers.copy()
        headers.update({'Content-Type' : 'application/json'})
        body = {'filetype': filetype}
        if filename is not None:
            body.update({'filename': filename})
        response_get_link = requests.post(self.url + '/mi', headers=headers, json=body)
        self.__validate_response(response_get_link)
        body = json.loads(response_get_link.content) 
        url = body.get('url')
        response = requests.put(url, headers={'Content-Type' : 'application/pdf'}, files={'file': file})
        self.__validate_response(response)
        return JobCreated(jobid=body.get('jobid'), url=url)
       
    def delete_job(self, jobid: str) -> True:
        """
        Delete job by jobid.
                               
        Args
        ----
        jobid -- Job id of the job to be deleted.

        Returns
        ----
        bool
        """
        body = {'jobid': jobid}
        response = requests.delete(self.url + '/mi', headers=self.headers, json=body)
        self.__validate_response(response)
        return True

    def get_job(self, jobid: str) -> Job:
        """
        Get job by job id.
                               
        Args
        ----
        jobid -- Job id of the job to get.

        Returns
        ----
        Job -- Dictionary {"filename": "str", "status: "str", "url": "str"}
        """
        response = requests.get(self.url + '/mi/', headers=self.headers, params={'jobid' : jobid})
        self.__validate_response(response)
        body = json.loads(response.content)
        job = Job(filename=body.get('filename'), status=body.get('status'))
        if body.get('status') == 'SUCCESS': # TODO: add test to check data when changing status is available
            job.update({'url' : body.get('url')}) # pragma: no cover
        return job

    def __validate_response(self, response: requests.Response):
        match response.status_code:
            case 401:
                raise Exception('The current token has expired. Update it.') # pragma: no cover
            case 404:
                raise Exception('Bad request.')
            case 500:
                raise Exception('An error ocurred, try again later.') # pragma: no cover