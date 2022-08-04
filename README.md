# Scribe MI

##### Python library to manage MI files in Scribe's platform

---

This library allows the management of MI (Monitoring Information) in a simple way.

You first need a Scribe account and an id token. The account can be requested at contact[atsign]scribelabs[dotsign]ai, and the id token can be generated by the user.

One way to generate the id token is through [ScribeAuth](https://github.com/ScribeLabsAI/scribeAuth) library. The function _get_tokens_ will return a Dictionary with three different tokens and it is necessary to extract the correct one to make it work (id token).

It is important to use the function _update_id_token_ before calling any other method of this library to avoid exceptions. If the id token has expired, it will be necessary to update it again.

---

This library requires a version of Python 3 that supports typings.

### Installation

```bash
pip install ScribeMi
```

### 1. Update id token to gain access

```python
from ScribeMi import MI
mi = MI('url', 'api_key')
mi.update_id_token('idtoken')
```

### 2. List uploaded archives

```python
from ScribeMi import MI
mi = MI('url', 'api_key')
archives = mi.list_archives()
```

### 3. Upload archive with file path

```python
from ScribeMi import MI
mi = MI('url', 'api_key')
archive_name = mi.upload_archive('filename')
```

### 4. Upload archive with file in memory

```python
from ScribeMi import MI
mi = MI('url', 'api_key')
archive_name = mi.upload_archive(open('file', 'rb'))
```

### 5. Delete archive by filename

```python
from ScribeMi import MI
mi = MI('url', 'api_key')
deleted = mi.delete_archive('filename')
```

### 6. Get job by jobid

```python
from ScribeMi import MI
mi = MI('url', 'api_key')
job = mi.get_job('jobid')
```

### 7. Upload job with file path

```python
from ScribeMi import MI
mi = MI('url', 'api_key')
job_created = mi.create_job('jobid')
```

### 8. Upload job with file in memory

```python
from ScribeMi import MI
mi = MI('url', 'api_key')
job_created = mi.create_job(open('file', 'rb'))
```

### 9. Delete job by jobid

```python
from ScribeMi import MI
mi = MI('url', 'api_key')
deleted = mi.delete_job('jobid')
```

---

To flag an issue, open a ticket on [Github](https://github.com/scribelabsai/ScribeMi/issues).
