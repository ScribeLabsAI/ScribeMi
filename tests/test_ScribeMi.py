from ScribeMi import MI
import unittest
import os
from dotenv import load_dotenv
from scribeauth import ScribeAuth
import time
import boto3
from jwt import JWT
load_dotenv()

client_id: str = os.environ.get("CLIENT_ID")
username: str = os.environ.get("USER")
password: str = os.environ.get("PASSWORD")
access = ScribeAuth(client_id)
id_token: str = access.get_tokens(username=os.environ.get("USER"), password=os.environ.get("PASSWORD")).get('id_token')
url: str = os.environ.get("URL")
api_key: str = os.environ.get("API_KEY")
archive_path = 'tests/companies_house_document.zip'
file_name = 'companies_house_document.pdf'
file_path = 'tests/' + file_name
company_name='Company Name'
mi = MI(api_key, url)
mi.update_id_token(id_token)
jobid_list = []

class TestScribeMiArchives(unittest.TestCase):

    @classmethod
    def setUpClass(self) -> None:
        clear_archives(mi)

    def test_upload_archive_filename_1(self):
        archive_name = mi.upload_archive(archive_path)
        archives_list_names = [a.get('name') for a in mi.list_archives()]
        self.assertTrue(archive_name in archives_list_names)

    def test_upload_archive_filename_2(self):
        archive_name = mi.upload_archive(archive_path)
        time.sleep(1)
        with open(archive_path, 'rb') as f:
            archive_name2 = mi.upload_archive(f)
        time.sleep(1)
        archives_list_names = [a.get('name') for a in mi.list_archives()]
        self.assertTrue(archive_name in archives_list_names)
        self.assertTrue(archive_name2 in archives_list_names)

    def test_upload_archive_filecontent_1(self):
        with open(archive_path, 'rb') as f:
            archive_name = mi.upload_archive(f)
        archives_list_names = [a.get('name') for a in mi.list_archives()]
        self.assertTrue(archive_name in archives_list_names)

    def test_upload_archive_filecontent_2(self):
        with open(archive_path, 'rb') as f:
                archive_name = mi.upload_archive(f)
        time.sleep(1)
        with open(archive_path, 'rb') as f:
                archive_name2 = mi.upload_archive(f)
        time.sleep(1)
        archives_list_names = [a.get('name') for a in mi.list_archives()]
        self.assertTrue(archive_name in archives_list_names)
        self.assertTrue(archive_name2 in archives_list_names)

    @classmethod
    def tearDownClass(self) -> None:
        clear_archives(mi)


class TestScribeMiJob(unittest.TestCase):

    @classmethod
    def setUpClass(self) -> None:
        clear_jobs(mi)

    def test_create_job_filepath_format_and_name(self):
        job_created = mi.create_job(company_name, file_path, 'pdf', file_name)
        jobid_list.append(job_created.get('jobid'))
        time.sleep(1)
        job = mi.get_job(job_created.get('jobid'))
        self.assertEqual(file_name, job.get('filename'))
        self.assertEqual('PENDING', job.get('status'))
        self.assertEqual(None, job.get('url'))

    def test_create_job_filepath_format_and_no_name(self):
        job_created = mi.create_job(company_name, file_path, 'pdf')
        jobid_list.append(job_created.get('jobid'))
        time.sleep(1)
        job = mi.get_job(job_created.get('jobid'))
        self.assertEqual('', job.get('filename'))
        self.assertEqual('PENDING', job.get('status'))
        self.assertEqual(None, job.get('url'))

    def test_create_job_filecontent_format_and_name(self):
        with open(file_path, 'rb') as f:
            job_created = mi.create_job(company_name, f, 'pdf', file_name)
        jobid_list.append(job_created.get('jobid'))
        time.sleep(1)
        job = mi.get_job(job_created.get('jobid'))
        self.assertEqual(file_name, job.get('filename'))
        self.assertEqual('PENDING', job.get('status'))
        self.assertEqual(None, job.get('url'))

    def test_create_job_filecontent_format_and_no_name(self):
        with open(file_path, 'rb') as f:
            job_created = mi.create_job(company_name, f, 'pdf')
        jobid_list.append(job_created.get('jobid'))
        time.sleep(1)
        job = mi.get_job(job_created.get('jobid'))
        self.assertEqual('', job.get('filename'))
        self.assertEqual('PENDING', job.get('status'))
        self.assertEqual(None, job.get('url'))

    def test_create_job_filecontent_wrong_format(self):
        with self.assertRaises(Exception):
            with open(file_path, 'rb') as f:
                self.assertRaises(mi.create_job(company_name, f, 'pdff'))

    def test_get_job_non_existent(self):
        with self.assertRaises(Exception):
            self.assertRaises(mi.get_job('jobid_test'))

    @classmethod   
    def tearDownClass(self) -> None:
        clear_jobs(mi)
        clear_db_table()


def clear_archives(mi: MI):
    archives = mi.list_archives()
    for a in archives:
        mi.delete_archive(a.get('name'))

def clear_jobs(mi: MI):
    for j in jobid_list:
        mi.delete_job(j)

def clear_db_table():
    jwt = JWT()
    userid = jwt.decode(message=id_token, algorithms=['RS256'], do_verify=False).get('sub')
    clientDynamoDB = boto3.client('dynamodb', region_name='eu-west-2')
    all_jobid = clientDynamoDB.scan(TableName='tasks', ScanFilter={
        'userid':{
            'AttributeValueList':[{'S':str(userid)}],
            'ComparisonOperator':'EQ'
        }
    }).get('Items')
    for j in all_jobid:
        clientDynamoDB.delete_item(
            TableName='tasks',
            Key={'jobid':{'S':str(j.get('jobid').get('S'))}}
    )