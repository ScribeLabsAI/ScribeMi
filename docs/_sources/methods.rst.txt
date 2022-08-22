Methods
=======

1. Update id token to gain access
---------------------------------

.. code:: python

   from ScribeMi import MI
   mi = MI('api_key', 'url')
   mi.update_id_token('idtoken')

2. List uploaded archives
-------------------------

.. code:: python

   from ScribeMi import MI
   mi = MI('api_key', 'url')
   archives = mi.list_archives()

3. Upload archive with file path
--------------------------------

.. code:: python

   from ScribeMi import MI
   mi = MI('api_key', 'url')
   archive_name = mi.upload_archive('file_name')

4. Upload archive with file in memory
-------------------------------------

.. code:: python

   from ScribeMi import MI
   mi = MI('api_key', 'url')
   with open('file_name', 'rb') as f:
   	archive_name = mi.upload_archive(f)

5. Delete archive by file_name
------------------------------

.. code:: python

   from ScribeMi import MI
   mi = MI('api_key', 'url')
   deleted = mi.delete_archive('file_name')

6. Get job by jobid
-------------------

.. code:: python

   from ScribeMi import MI
   mi = MI('api_key', 'url')
   job = mi.get_job('jobid')

7. Upload job with file path (*file_name* is optional)
------------------------------------------------------

.. code:: python

   from ScribeMi import MI
   mi = MI('api_key', 'url')
   job_created = mi.create_job('company_name', 'file_path', 'filetype', 'file_name')

8. Upload job with file in memory (*file_name* is optional)
-----------------------------------------------------------

.. code:: python

   from ScribeMi import MI
   mi = MI('api_key', 'url')
   with open('file_path', 'rb') as f:
   	job_created = mi.create_job('company_name', f, 'filetype', 'file_name')

9. Delete job by jobid
----------------------

.. code:: python

   from ScribeMi import MI
   mi = MI('api_key', 'url')
   deleted = mi.delete_job('jobid')