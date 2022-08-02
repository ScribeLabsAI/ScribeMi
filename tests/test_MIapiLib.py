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
file_name = 'example.pdf'
file_path = 'tests/' + file_name

mi = MI(url, api_key)
mi.update_id_token(id_token)

class TestMIapiLibArchives(unittest.TestCase):

    def test_upload_archive_filename_1(self):
        clear_archives(mi)
        mi.upload_archive(archive_path)
        self.assertEquals(1, len(mi.list_archives()))
        clear_archives(mi)

    def test_upload_archive_filename_2(self):
        clear_archives(mi)
        mi.upload_archive(archive_path)
        time.sleep(1)
        mi.upload_archive(archive_path)
        time.sleep(1)
        self.assertEquals(2, len(mi.list_archives()))
        clear_archives(mi)

    def test_upload_archive_filecontent_1(self):
        clear_archives(mi)
        mi.upload_archive(open(archive_path, 'rb'))
        self.assertEquals(1, len(mi.list_archives()))
        clear_archives(mi)

    def test_upload_archive_filecontent_2(self):
        clear_archives(mi)
        mi.upload_archive(open(archive_path, 'rb'))
        time.sleep(1)
        mi.upload_archive(open(archive_path, 'rb'))
        time.sleep(1)
        self.assertEquals(2, len(mi.list_archives()))
        clear_archives(mi)


class TestMIapiLibJob(unittest.TestCase):
    def test_create_job_filepath_format_and_name(self):
        job_created = mi.create_job(file_path, 'pdf', file_name)
        time.sleep(1)
        job = mi.get_job(job_created.get('jobid'))
        self.assertEquals(file_name, job.get('filename'))
        self.assertEquals('PENDING', job.get('status'))

    def test_create_job_filepath_format_and_no_name(self):
        job_created = mi.create_job(file_path, 'pdf')
        time.sleep(1)
        job = mi.get_job(job_created.get('jobid'))
        self.assertEquals('', job.get('filename'))
        self.assertEquals('PENDING', job.get('status'))

    def test_create_job_filecontent_format_and_name(self):
        job_created = mi.create_job(open(file_path, 'rb'), 'pdf', file_name)
        time.sleep(1)
        job = mi.get_job(job_created.get('jobid'))
        self.assertEquals(file_name, job.get('filename'))
        self.assertEquals('PENDING', job.get('status'))

    def test_create_job_filecontent_format_and_no_name(self):
        job_created = mi.create_job(open(file_path, 'rb'), 'pdf')
        time.sleep(1)
        job = mi.get_job(job_created.get('jobid'))
        self.assertEquals('', job.get('filename'))
        self.assertEquals('PENDING', job.get('status'))

    def test_create_job_filecontent_wrong_format(self):
        with self.assertRaises(Exception):
            self.assertRaises(mi.create_job(open(file_path, 'rb'), 'pdff'))
        
        
def clear_archives(mi):
    archives = mi.list_archives()
    for a in archives:
        mi.delete_archive(a.get('name'))