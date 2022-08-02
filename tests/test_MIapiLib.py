from fileinput import filename
from MIapiLib import MI
import unittest
import os
from dotenv import load_dotenv
from scribeauth import ScribeAuth
import time
load_dotenv()

client_id: str = os.environ.get("CLIENT_ID")
username: str = os.environ.get("USER")
password: str = os.environ.get("PASSWORD")
access = ScribeAuth(client_id)
id_token: str = access.get_tokens(username=os.environ.get("USER"), password=os.environ.get("PASSWORD")).get('idToken') # TODO: id_token, but it needs to be fixed in the other library first
url: str = os.environ.get("URL")
api_key: str = os.environ.get("API_KEY")
archive_path = 'tests/example.zip'

mi = MI(url, api_key)
mi.update_id_token(id_token)

class TestMIapiLibArchives(unittest.TestCase):

    def test_upload_archive_filename_1(self):
        clear_archives(mi)
        mi.upload_archive(archive_path)
        assert_file_amount_uploaded(self, mi, 1)
        clear_archives(mi)

    def test_upload_archive_filename_2(self):
        clear_archives(mi)
        filenames = []
        filenames.append(mi.upload_archive(archive_path))
        time.sleep(1)
        filenames.append(mi.upload_archive(archive_path))
        time.sleep(1)
        assert_file_amount_uploaded(self, mi, 2)
        clear_archives(mi)

    def test_upload_archive_file_content_1(self):
        clear_archives(mi)
        mi.upload_archive(open(archive_path, 'rb'))
        assert_file_amount_uploaded(self, mi, 1)
        clear_archives(mi)

    def test_upload_archive_file_content_2(self):
        clear_archives(mi)
        filenames = []
        filenames.append(mi.upload_archive(open(archive_path, 'rb')))
        time.sleep(1)
        filenames.append(mi.upload_archive(open(archive_path, 'rb')))
        time.sleep(1)
        assert_file_amount_uploaded(self, mi, 2)
        clear_archives(mi)


def assert_file_amount_uploaded(self, mi, amount):
    self.assertEquals(amount, len(mi.list_archives()))
        
def clear_archives(mi):
    archives = mi.list_archives()
    for a in archives:
        mi.delete_archive(a.get('name'))