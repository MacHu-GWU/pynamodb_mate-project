.. _release_history:

Release and Version History
==============================================================================


Backlog
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

**Minor Improvements**

**Bugfixes**

**Miscellaneous**


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