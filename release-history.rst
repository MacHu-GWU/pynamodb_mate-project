.. _release_history:

Release and Version History
==============================================================================


Backlog
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- add automatically rollback if one of the DynamoDB write or S3 write failed.
- add an option to delete the S3 object as well when the DynamoDB item is deleted.
- add lazy load option for S3BackedAttribute.
- add ``clear_expired()`` method to DynamoDB cache backend.

**Minor Improvements**

**Bugfixes**

**Miscellaneous**


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

**Bugfixes**

**Miscellaneous**


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