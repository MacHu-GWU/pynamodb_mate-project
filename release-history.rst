.. _release_history:

Release and Version History
==============================================================================


Backlog
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- add ``clear_expired()`` method to DynamoDB cache backend.

**Minor Improvements**

**Bugfixes**

**Miscellaneous**


6.0.0.4 (2024-07-19)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Minor Improvements**

- Now most of :meth:`pynamodb_mate.patterns.large_attribute.impl.LargeAttributeMixin` methods allow to customize the ``s3_key_getter`` function. So that developer can customize how to convert a DynamoDB item into an S3 key for large attribute


6.0.0.3 (2024-06-06)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Bugfixes**

- Fix a bug that the :meth:`pynamodb_mate.patterns.status_tracker.impl.BaseStatusTracker.start` will faile when ``more_pending_status`` argument is an integer.


6.0.0.2 (2024-06-05)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Minor Improvements**

- Add ``s3_put_object_kwargs`` parameter to :meth:`pynamodb_mate.patterns.large_attribute.impl.LargeAttributeMixin.create_large_attribute_item` and :meth:`pynamodb_mate.patterns.large_attribute.impl.LargeAttributeMixin.update_large_attribute_item`. So that user can pass additional arguments to the S3 put object requests.
- Allow ``allowed_status`` parameter to :meth:`pynamodb_mate.patterns.status_tracker.impl.BaseStatusTracker.start`. Allow user to specify the allowed status other than "pending" / "failed".

**Bugfixes**

- Fix a bug that ``pynamodb_mate.patterns.large_attribute.impl.PutS3Response.clean_up_old_s3_object_when_update_dynamodb_item_succeeded()`` may fail when the old data model large attribute was None.
- Fix a bug that ``pynamodb_mate.patterns.large_attribute.impl.LargeAttributeMixin.create_large_attribute_item()`` use the hard code partition key attribute by mistake.


6.0.0.1 (2024-05-23)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**💥Breaking change**

- fully support pynamodb 6.X, drop compatible to pynamodb 5.X.
- rework the ``status_tracker`` pattern to ensure strong consistency in high concurrent workload. Due to the change that the ``Index.query`` is instance method from pynamodb 6.X, the old ``status_tracker`` implementation won't work in pynamodb 6.X. We have to completely remove the old implementation and re-implement the ``status_tracker`` pattern.

**Features and Improvements**

- fully support pynamodb 6.X, drop compatible to pynamodb 5.X.
- rework the ``status_tracker`` pattern to ensure strong consistency in high concurrent workload.

**Minor Improvements**

- update the ``status_tracker`` document.
- improve code coverage test.


5.5.1.1 (2024-05-22)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Background**

- The ``pynamodb`` implementation relies on some ``botocore`` private API. And one of the private API is changed from ``botocore`` 1.33.2 that breaks the ``pynamodb`` implementation. ``pynamodb`` 5.5.1 fixed the compatibility issue, so that ``pynamodb_mate`` also got upgraded to ``5.5.1.X``.

**Features and Improvements**

- add :mod:`pynamodb_mate.patterns.relationship` Pattern, allow you to manage mass amount entity and one-to-many, many-to-many relationship in DynamoDB using the ultimate data modeling strategy.
- add :mod:`pynamodb_mate.patterns.large_attribute` Pattern, it re-implements the ``pynamodb_mate.attributes.s3backed`` to provide better consistency model across DynamoDB and S3, and it also support updating multiple large attributes in one API. The old ``pynamodb_mate.attibutes.s3backed`` module is marked as deprecated, and it will be removed in 6.X version.
- rework the import structure of the library, now we recommend using ``import pynamodb_mate.api as pm`` instead of ``import pynamodb_mate as pm``. Old public API is still available in ``import pynamodb_mate as pm`` name space. And these API is scheduled to be deleted in 6.X version.

**Minor Improvements**

- Rework the unit test, now it uses both mock and real AWS DynamoDB table for testing.
- Rework the documentation site.

**Miscellaneous**

- add Python3.12 support.


5.3.4.9 (2023-05-15)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Bugfixes**

- fix a but that some usages of :meth:`~pynamodb_mate.patterns.status_tracker.impl.BaseStatusTracker.make_value` are missing the parameter job_id.

**Miscellaneous**

- add Python3.11 support.


5.3.4.8 (2023-02-03)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- :class:`~pynamodb_mate.patterns.status_tracker.impl.BaseStatusTracker` added ``create_time`` attribute.
- :class:`~pynamodb_mate.patterns.status_tracker.impl.StatusAndCreateTimeIndex` is renamed to :class:`~pynamodb_mate.patterns.status_tracker.impl.StatusAndUpdateTimeIndex`, and the index now uses ``update_time`` as the range key, and it now uses IncludeProjection.
- :meth:`pynamodb_mate.patterns.status_tracker.impl.BaseStatusTracker.query_by_status` add ``auto_refresh`` parameter.

**Minor Improvements**

- :meth:`pynamodb_mate.patterns.status_tracker.impl.BaseStatusTracker.query_by_status` now take both status enum or status enum value.


5.3.4.7 (2023-02-01)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- :class:`~pynamodb_mate.patterns.status_tracker.impl.BaseStatusTracker` added ``create_time`` attribute.
- :class:`~pynamodb_mate.patterns.status_tracker.impl.StatusAndTaskIdIndex` is renamed to :class:`~pynamodb_mate.patterns.status_tracker.impl.StatusAndCreateTimeIndex`, and the index now uses ``create_time`` as the range key, and it now uses AllProjection.
- :meth:`pynamodb_mate.patterns.status_tracker.impl.BaseStatusTracker.query_by_status` add ``older_task_first`` parameter.

**Minor Improvements**

- improve logging in :meth:`pynamodb_mate.patterns.status_tracker.impl.BaseStatusTracker.start`.


5.3.4.6 (2023-01-16)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- Use iterproxy for Model query and scan, enable type hint in result iterator.
- Use iterproxy for Model query and scan, enable type hint in result iterator.

**Miscellaneous**

- use ``moto`` for unit test


5.3.4.5 (2022-01-02)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- add :mod:`pynamodb_mate.patterns.cache` Pattern. Commonly used when you want to use DynamoDB as a cache.

**Miscellaneous**

- improve the document for S3BackedAttribute, EncryptedAttribute and CompressedAttribute.
- refactor the S3BackedAttribute, EncryptedAttribute and CompressedAttribute to make it easier to customize.


5.3.4.4 (2022-01-02)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- allow user to define a custom ``__post_init__`` method in the DynamoDB ORM model.
- allow user to define a ``pre_start_hook`` and ``post_start_hook`` in the ``status_tracker`` pattern.

**Miscellaneous**

- update the requirements file to ensure the compatible version of the ``pynamodb`` library.


5.3.4.3 (2022-01-02)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Minor Improvements**

- :mod:`pynamodb_mate.patterns.status_tracker` Pattern:
    - the status_tracker pattern doesn't require the status index name to be ``status_and_task_id_index`` anymore. it will automatically discover that.
    - add debug information when you start a job.
    - add example jupyter notebook.


5.3.4.2 (2022-01-01)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- add :mod:`pynamodb_mate.patterns.status_tracker` Pattern. Commonly used when you want to track status of your task in DynamoDB.

**Minor Improvements**

- move unit test to GitHub Action.


5.3.4.1 (2022-12-26)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- add more pynamodb API to top module level
- add :meth:`pynamodb_mate.models.Model.get_one_of_none` method
- add :meth:`pynamodb_mate.models.Model.delete_if_exists` method

**Breaking change**

- ``EncryptUnicodeAttribute`` -> ``EncryptedUnicodeAttribute``
- ``EncryptBinaryAttribute`` -> ``EncryptedBinaryAttribute``

**Miscellaneous**

- ``pycryptodome`` is only required when you are trying to use encrypted attribute. You can install via ``pip install pynamodb_mate[encrypt]``


5.2.1.1 (2022-08-12)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- add Console URL api


5.1.0.1 (2021-12-12)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- Made decision of the API design. Make it stable and consistent to all attributes
- Add ``pynamodb_mate.EncryptedNumberAttribute``, ``pynamodb_mate.EncryptUnicodeAttribute``, ``pynamodb_mate.EncryptBinaryAttribute``, ``pynamodb_mate.EncryptedJsonAttribute``, ``pynamodb_mate.S3BackedBigBinaryAttribute``, ``pynamodb_mate.S3BackedBigTextAttribute``, ``pynamodb_mate.CompressedJSONAttribute``, ``pynamodb_mate.CompressedUnicodeAttribute``, ``pynamodb_mate.CompressedBinaryAttribute`` to public API

**Minor Improvements**

- Improve documentations.

**Miscellaneous**

- It maintain the compatibility to major version of ``pynamodb`` library. For example ``pynamodb_mate>=5.0.0,<6.0.0`` is compatible to ``pynamodb>=5.0.0,<6.0.0``.
- Drop support for Python2.7 because ``pynamodb`` drops 2.7 support.


0.0.2 (2020-05-04)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- add ``EncryptUnicodeAttribute``, ``EncryptBinaryAttribute``, ``EncryptedNumberAttribute``, ````EncryptedJsonAttribute``. It can do client side encryption.


0.0.1 (2019-06-17)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- First release