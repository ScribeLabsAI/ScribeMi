import requests
import json
from io import BytesIO
from typing import BinaryIO, Optional
from typing import Union

class MI:
    def __init__(self, id_token: str, url: str, apiKey: str):
        self.url = url
        self.headers = {'Authorization' : id_token, 'x-api-key' : apiKey}

    def update_idtoken(self, id_token: str) -> None:
        self.headers.update({'Authorization' : id_token})

    def list_archives(self) -> requests.Response:
        return requests.get(self.url + '/archives', headers=self.headers)

    def delete_archive(self, filename: str) -> requests.Response:
        return requests.delete(self.url + '/archive', headers=self.headers, json={'key': filename})

    def generate_upload_link(self, file_or_filename: Union[str, BytesIO, BinaryIO]) -> requests.Response:
        url = self.__get_url_generate_upload_link()
        if isinstance(file_or_filename, str):
            file = open(file_or_filename, 'rb')
        else:
            file = file_or_filename
        return requests.put(url, headers={'Content-Type' : 'application/zip'}, files={'file': file})

    def submit_MI(self, file_or_filename: Union[str, BytesIO, BinaryIO], filetype, filename: Optional[str] = None) -> requests.Response:
        filetype_list = ['pdf', 'xlsx', 'xls', 'xlsm', 'doc', 'docx', 'ppt', 'pptx']
        if filetype not in filetype_list:
            raise Exception("Invalid filetype. Accepted values: 'pdf', 'xlsx', 'xls', 'xlsm', 'doc', 'docx', 'ppt', 'pptx'.")
        if isinstance(file_or_filename, str):
            file = open(file_or_filename, 'rb')
        else:
            file = file_or_filename
        headers = self.headers.copy()
        headers.update({'Content-Type' : 'application/json'})
        if filename is None:
            body = {'filetype': filetype}
        else:
            body = {'filename': filename, 'filetype': filetype}
        url = self.__get_url_submit_MI(headers, body)
        return requests.put(url, headers={'Content-Type' : 'application/pdf'}, files={'file': file})
       
    def delete_MI(self, jobid: str) -> requests.Response:
        body = {'jobid': jobid}
        return requests.delete(self.url + '/mi', headers=self.headers, json=body)

# TODO: CONTINUE WITH THIS: API yet not ready
    # def get_MI(self, jobid: str) -> requests.Response:
    #     request = requests.get(self.url + '/mi/' + jobid, headers=self.headers)
    #     return request

    def __get_url_generate_upload_link(self) -> str:
        request = requests.get(self.url + '/archive', headers=self.headers)
        if request.status_code == 401:
            raise Exception('The current token has expired. Update it.')
        else:
            return json.loads(request.content)

    def __get_url_submit_MI(self, headers, body) -> str:
        request = requests.post(self.url + '/mi', headers=headers, json=body)
        if request.status_code == 401:
            raise Exception('The current token has expired. Update it.')
        else:
            return json.loads(request.content).get('url')
