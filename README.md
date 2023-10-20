# Scribe Private Information (MI) SDK

A Python library designed to facilitate accessing Scribe's Private Information (MI) API.

This library requires a version of Python 3 that supports typings.

## Installation

```bash
pip install ScribeMi
```

## Usage

### Construct client

The constructor expects an environment object:

```
env = {
  API_URL: 'API_URL',
  IDENTITY_POOL_ID: 'IDENTITY_POOL_ID',
  USER_POOL_ID: 'USER_POOL_ID',
  CLIENT_ID: 'CLIENT_ID',
  REGION: 'REGION',
};
```

The `API_URL` is `"mi.scribelabs.ai/v1"`.

The `REGION` is `"eu-west-2"`.

Contact Scribe to obtain other details required for authentication.

```python
from ScribeMi import MI

client = MI({
    'API_URL': 'mi.scribelabs.ai/v1',
    'REGION': 'eu-west-2',
    'IDENTITY_POOL_ID': 'Contact Scribe for authentication details',
    'USER_POOL_ID': 'Contact Scribe for authentication details',
    'CLIENT_ID': 'Contact Scribe for authentication details',
})
```

### Authenticate

Authentication is handled by [Scribe's Auth library](https://github.com/ScribeLabsAI/ScribeAuth/blob/master/README.md), without the need for you to call that library directly.

```python
# Authenticate with username / password
client.authenticate({ 'username': 'myUsername', 'password': 'myPassword' })

# OR with refresh token
client.authenticate({ 'refresh_token': 'myRefreshToken' })
```

The MI client will try to automatically re-authenticate with your refresh token, if you try to make an API call after credentials have expired.

### Submit a document for processing

```python
jobid = client.submit_task('path/to/file.pdf', {
    'filetype': 'pdf',
    'filename': 'example-co-2023-q1.pdf',
    'companyname': 'Example Co Ltd'
})
```

The `filetype` parameter is required: it should match the file's extension / MIME type.

Other parameters are optional:

- `filename` is recommended: it should be the name of the uploaded file. It appears in API responses and the web UI.
- `companyname` can optionally be included for company Financials data: it should be the legal name of the company this document describes, so that documents relating to the same company can be collated.

The returned `jobid` can be used to find information about the task status via `getTask`, or via the web UI.

### View tasks

Fetch details of an individual task:

```python
task = client.get_task(jobid)
print(task.status)
```

Or list all tasks:

```python
tasks = client.list_tasks()
```

### Export output models

After documents have been processed by Scribe, the task status (which can be seen via `get_task` / `list_tasks`) is `"SUCCESS"`. At this point, you can export the model:

```python
task = client.get_task(jobid)

# Use fetchModel
model = fetchModel(task)

# Alternatively, fetch the model directly from its URL
return task.modelUrl
```

In either case, note that the model is accessed via a pre-signed URL, which is only valid for a limited time after calling `get_task` / `list_tasks`.

#### Collate fund data

When using Scribe to process fund data, multiple models can be consolidated for export in a single file:

```python
tasks = client.list_tasks()
tasks_to_collate = [task for task in tasks if task['originalFilename'].startswith('Fund_1')]

collated_model = client.consolidate_tasks(tasks_to_collate)
```

### Delete tasks / cancel processing

```python
task = client.get_task(jobid)

client.delete_task(task)
```

Deletion is irreversible.

After a successful deletion, the file, any output model, and any other file derived from the input are deleted permanently from Scribe's servers.

## See also

Documentation for the underlying REST API may also be useful, although we recommend accessing the API via this library or our Node SDK.

- [REST API documentation](https://scribelabs.ai/docs/docs-mi)

- [Node SDK](https://github.com/ScribeLabsAI/ScribeMiNode)
