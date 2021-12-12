.. _release_history:

Release and Version History
==============================================================================


5.1.0.2 (TODO)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

**Minor Improvements**

**Bugfixes**

**Miscellaneous**


5.1.0.1 (2021-12-12)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- Made decision of the API design. Make it stable and consistent to all attributes
- Add ``pynamodb_mate.EncryptedNumberAttribute``, ``pynamodb_mate.EncryptUnicodeAttribute``, ``pynamodb_mate.EncryptBinaryAttribute``, ``pynamodb_mate.EncryptedJsonAttribute``, ``pynamodb_mate.S3BackedBigBinaryAttribute``, ``pynamodb_mate.S3BackedBigTextAttribute``, ``pynamodb_mate.CompressedJSONAttribute``, ``pynamodb_mate.CompressedUnicodeAttribute``, ``pynamodb_mate.CompressedBinaryAttribute``.

**Minor Improvements**

- Improve documentations.

**Miscellaneous**

- It maintain the compatibility to major version of ``pynamodb`` library. For example ``pynamodb_mate>=5.0.0,<6.0.0`` is compatible to ``pynamodb>=5.0.0,<6.0.0``.
- Drop support for Python2.7 because ``pynamodb`` drops 2.7 support.


0.0.2 (2020-05-04)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- add ``EncryptUnicodeAttribute``, ``EncryptBinaryAttribute``, ``EncryptedNumberAttribute``, ````EncryptedJsonAttribute``. It can do client side encryption.

**Minor Improvements**

**Bugfixes**

**Miscellaneous**


0.0.1 (2019-06-17)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- First release