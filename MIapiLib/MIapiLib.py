import os
import requests
from dotenv import load_dotenv

load_dotenv()

class MI:
    def __init__(self, environment: str, id_token: str):
        self.headers = {'Authorization' : id_token}
        if environment.upper() == 'DEV':
            self.url = os.environ.get("DEV_URL")
            self.headers.update({'x-api-key' : os.environ.get("DEV_API_KEY")})
        elif environment.upper() == 'PROD':
            self.url = os.environ.get("PROD_URL")
            self.headers.update({'x-api-key' : os.environ.get("PROD_API_KEY")})
        else:
            raise Exception("Invalid environment. Use \'DEV\' or \'PROD\' instead")

    def listArchives(self) -> requests.Response:
        return requests.get(self.url + '/archives', headers=self.headers)

    def deleteArchive(self, filename: str) -> requests.Response:
        return requests.delete(self.url + '/archive', headers=self.headers, json={'key': filename})


# TODO: MAKE IT ACCEPT A CONTENT FILE OR A FILENAME
    def generateUploadLink(self, file) -> requests.Response:
        url = requests.get(self.url + '/archive', headers=self.headers).text[1:][:-1]
        # TODO: ADD FILE OR FILENAME
        return requests.put(url, headers={'Content-Type' : 'application/zip'}, files={'file': open(file, 'rb')})


id_token = ''
mi = MI('dev', id_token)
# -------------------------------------------------------------------
archives = mi.listArchives()
print(archives.text)
print(archives.status_code)
# -------------------------------------------------------------------
# deleteRequest = mi.deleteArchive('name.zip')
# print(deleteRequest.headers)
# print(deleteRequest.text)
# print(deleteRequest.status_code)
# -------------------------------------------------------------------
# file = 'path'
# linkToUpload = mi.generateUploadLink(file)
# print(linkToUpload.headers)
# print(linkToUpload.text)
# print(linkToUpload.status_code)