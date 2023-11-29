from scribemi.ScribeMi import MI, UnauthenticatedException
import unittest
import os
from dotenv import load_dotenv

load_dotenv(override=True)

"""
Mandatory env vars to set:

URL, API_KEY, CLIENT_ID, USER, PASSWORD, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN, REGION_NAME
"""

env = {
    "API_URL": os.environ["API_URL"],
    "IDENTITY_POOL_ID": os.environ["IDENTITY_POOL_ID"],
    "USER_POOL_ID": os.environ["USER_POOL_ID"],
    "CLIENT_ID": os.environ["CLIENT_ID"],
    "REGION": os.environ["REGION"],
}

username_and_password = {
    "username": os.environ["USERNAME"],
    "password": os.environ["PASSWORD"],
}


class TestScribeMiAuth(unittest.TestCase):
    def test_fetch_credentials_with_username_and_password(self):
        client = MI(env)
        client.authenticate(username_and_password)

    def test_fetch_credentials_with_refresh_token(self):
        client = MI(env)
        client.authenticate(username_and_password)
        tokens = client.tokens
        if tokens != None:
            refresh_token = tokens.get("refresh_token")
            if refresh_token != None:
                client.authenticate({"refresh_token": refresh_token})
            else:
                assert False
        else:
            assert False

    def test_reauthenticate(self):
        client = MI(env)
        client.authenticate(username_and_password)
        client.reauthenticate()

    def test_authenticated_api_call(self):
        client = MI(env)
        client.authenticate(username_and_password)
        client.list_tasks()

    def test_throws_if_not_authenticated(self):
        client = MI(env)
        try:
            client.list_tasks()
            assert False
        except UnauthenticatedException:
            assert True


class TestScribeMiErrorHandling(unittest.TestCase):
    def test_throws_on_error_response(self):
        client = MI(env)
        client.authenticate(username_and_password)
        try:
            client.get_task("invalidJobid")
            assert False
        except:
            assert True


class TestScribeMiEndpoints(unittest.TestCase):
    def test_endpoints(self):
        client = MI(env)
        client.authenticate(username_and_password)

        jobid = client.submit_task(
            "tests/companies_house_document.pdf",
            {"filetype": "pdf"},
        )

        client.list_tasks()

        if jobid == None:
            assert False

        task = client.get_task(jobid)

        try:
            client.fetch_model(task)
            assert False
        except Exception:
            # Error because task has not been processed
            assert True

        try:
            client.consolidate_tasks([task])
            assert False
        except Exception:
            # Error because the model is not ready
            assert True

        client.delete_task(task)
