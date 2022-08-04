from scribemi import MI
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
id_token: str = access.get_tokens(username=os.environ.get("USER"), password=os.environ.get("PASSWORD")).get('id_token')
url: str = os.environ.get("URL")
api_key: str = os.environ.get("API_KEY")
archive_path = 'tests/example.zip'
file_name = 'example.pdf'
file_path = 'tests/' + file_name

mi = MI(url, api_key)
mi.update_id_token(id_token)
jobid_list = []

class TestScribeMiArchives(unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        clear_archives(mi)

    def test_upload_archive_filename_1(self):
        mi.upload_archive(archive_path)
        self.assertEqual(1, len(mi.list_archives()))

    def test_upload_archive_filename_2(self):
        mi.upload_archive(archive_path)
        time.sleep(1)
        with open(archive_path, 'rb') as f:
                mi.upload_archive(f)
        time.sleep(1)
        self.assertEqual(2, len(mi.list_archives()))

    def test_upload_archive_filecontent_1(self):
        with open(archive_path, 'rb') as f:
                mi.upload_archive(f)
        self.assertEqual(1, len(mi.list_archives()))

    def test_upload_archive_filecontent_2(self):
        with open(archive_path, 'rb') as f:
                mi.upload_archive(f)
        time.sleep(1)
        with open(archive_path, 'rb') as f:
                mi.upload_archive(f)
        time.sleep(1)
        self.assertEqual(2, len(mi.list_archives()))

    def tearDown(self) -> None:
        super().tearDown()
        clear_archives(mi)


class TestScribeMiJob(unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        clear_jobs(mi)

    def test_create_job_filepath_format_and_name(self):
        job_created = mi.create_job(file_path, 'pdf', file_name)
        jobid_list.append(job_created.get('jobid'))
        time.sleep(1)
        job = mi.get_job(job_created.get('jobid'))
        self.assertEqual(file_name, job.get('filename'))
        self.assertEqual('PENDING', job.get('status'))

    def test_create_job_filepath_format_and_no_name(self):
        job_created = mi.create_job(file_path, 'pdf')
        jobid_list.append(job_created.get('jobid'))
        time.sleep(1)
        job = mi.get_job(job_created.get('jobid'))
        self.assertEqual('', job.get('filename'))
        self.assertEqual('PENDING', job.get('status'))

    def test_create_job_filecontent_format_and_name(self):
        with open(file_path, 'rb') as f:
            job_created = mi.create_job(f, 'pdf', file_name)
        jobid_list.append(job_created.get('jobid'))
        time.sleep(1)
        job = mi.get_job(job_created.get('jobid'))
        self.assertEqual(file_name, job.get('filename'))
        self.assertEqual('PENDING', job.get('status'))

    def test_create_job_filecontent_format_and_no_name(self):
        with open(file_path, 'rb') as f:
            job_created = mi.create_job(f, 'pdf')
        jobid_list.append(job_created.get('jobid'))
        time.sleep(1)
        job = mi.get_job(job_created.get('jobid'))
        self.assertEqual('', job.get('filename'))
        self.assertEqual('PENDING', job.get('status'))

    def test_create_job_filecontent_wrong_format(self):
        with self.assertRaises(Exception):
            with open(file_path, 'rb') as f:
                self.assertRaises(mi.create_job(f, 'pdff'))

    def test_get_job_non_existent(self):
        with self.assertRaises(Exception):
            self.assertRaises(mi.get_job('jobid_test'))
        
    def tearDown(self) -> None:
        super().tearDown()
        clear_jobs(mi)


def clear_archives(mi):
    archives = mi.list_archives()
    for a in archives:
        mi.delete_archive(a.get('name'))

def clear_jobs(mi):
    for j in jobid_list:
        mi.delete_job(j)