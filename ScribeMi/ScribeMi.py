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
    def __init__(self, api_key: str, url: str = 'https://nizwzbutlf.execute-api.eu-west-2.amazonaws.com/prod/'):
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
        -------
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
        -------
        bool
        """
        response = requests.delete(self.url + '/archive', headers=self.headers, json={'key': filename})
        self.__validate_response(response)
        return True

    def upload_archive(self, file_or_filename: Union[str, BytesIO, BinaryIO]) -> str:
        """
        Upload archive by filepath or file loaded in memory.
                               
        Args
        ----
        file_or_filename -- Filepath of the file or file present in memory ready to be uploaded.

        Returns
        -------
        str -- The name of the uploaded file
        """
        response_get_link = requests.get(self.url + '/archive', headers=self.headers)
        self.__validate_response(response_get_link)
        url = json.loads(response_get_link.content)
        if isinstance(file_or_filename, str):
            with open(file_or_filename, 'rb') as f:
                return self.__send_archive(f, url)
        else:
            return self.__send_archive(file_or_filename, url)

    def create_job(self, company_name, file_or_filename: Union[str, BytesIO, BinaryIO], filetype, filename: Optional[str] = None) -> JobCreated:
        """
        Create and upload job.
                               
        Args
        ----
        file_or_filename -- Filepath of the file or file present in a var in memory ready to be uploaded.

        Returns
        -------
        JobCreated -- Dictionary {"jobid": "str", "url": "str"}
        """
        filetype_list = ['pdf', 'xlsx', 'xls', 'xlsm', 'doc', 'docx', 'ppt', 'pptx']
        if filetype not in filetype_list:
            raise InvalidFiletypeException("Invalid filetype. Accepted values: 'pdf', 'xlsx', 'xls', 'xlsm', 'doc', 'docx', 'ppt', 'pptx'.")
        if isinstance(file_or_filename, str):
            with open(file_or_filename, 'rb') as f:
                return self.__send_file(company_name, f, filename, filetype)
        else:
            return self.__send_file(company_name, file_or_filename, filename, filetype)
       
    def delete_job(self, jobid: str) -> True:
        """
        Delete job by jobid.
                               
        Args
        ----
        jobid -- Job id of the job to be deleted.

        Returns
        -------
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
        -------
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
        if response.status_code == 401:
            raise UnauthenticatedException('The current token is wrong or has expired. Update it.')
        elif response.status_code == 404:
            raise TaskNotFoundException('Task Not Found.')
        elif response.status_code >= 500:
            raise Exception('An error ocurred, try again later.') # pragma: no cover

    def __send_file(self, company_name, file, filename, filetype):
        headers = self.headers.copy()
        headers.update({'Content-Type' : 'application/json'})
        body = {'filetype': filetype, 'companyname': company_name}
        if filename is not None:
            body.update({'filename': filename})
        response_get_link = requests.post(self.url + '/mi', headers=headers, json=body)
        self.__validate_response(response_get_link)
        body = json.loads(response_get_link.content) 
        url = body.get('url')
        response = requests.put(url, headers={'Content-Type' : 'application/pdf'}, files={'file': file}, json={'companyname': company_name})
        self.__validate_response(response)
        return JobCreated(jobid=body.get('jobid'), url=url)

    def __send_archive(self, file, url):
        response = requests.put(url, headers={'Content-Type' : 'application/zip'}, files={'file': file})
        self.__validate_response(response)
        return url.split('?')[0].split('/')[-1].replace('%3A', ':')
