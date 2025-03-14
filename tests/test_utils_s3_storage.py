"""
# test_utils_s3_storage

@author: Jason Zhu
@email: jzhu@infoblox.com
@created: 2017-02-05

"""
from __future__ import absolute_import
from mock import MagicMock, patch

from watchmen.utils import s3_storage

import unittest


class TestS3Storage(unittest.TestCase):
    """
    TestS3Storage includes all unit tests for utils.s3_storage module
    """

    def setUp(self):
        """
        setup test
        """
        self.bucket = "s3-bucket"
        self.s3_storage = s3_storage.S3Storage(self.bucket)
        self.s3_resource = self.s3_storage.resource
        self.s3_client = self.s3_storage.client

        self.doFunc = lambda x, **kwargs: MagicMock()()
        pass

    def tearDown(self):
        """
        tear down each test
        """
        print("\ndone: " + self.id())

    @classmethod
    def tearDownClass(cls):
        """
        tear down class
        """
        print("\ndone.")

    @patch('watchmen.utils.s3_storage.s3')
    def test_create(self, mock_s3):
        """
        test utils.s3_storage.S3Storage interfaces - create method
        """
        self.s3_storage.create('s3/key/path', 'contents')
        mock_s3.create_key.assert_called_with(
            'contents', 's3/key/path', bucket=self.bucket, client=self.s3_client)

    @patch('watchmen.utils.s3_storage.s3')
    def test_delete(self, mock_s3):
        """
        test utils.s3_storage.S3Storage interfaces - delete method
        """
        self.s3_storage.delete('s3/key/path')
        mock_s3.delete_key.assert_called_with(
            's3/key/path', bucket=self.bucket, client=self.s3_client)

    @patch('watchmen.utils.s3_storage.s3')
    def test_exists(self, mock_s3):
        """
        test utils.s3_storage.S3Storage interfaces - exists method
        """
        self.s3_storage.exists('s3/key/path')
        mock_s3.check_key.assert_called_with(
            's3/key/path', bucket=self.bucket, client=self.s3_client)

    @patch('watchmen.utils.s3_storage.s3')
    def test_get_content(self, mock_s3):
        """
        test utils.s3_storage.S3Storage interfaces - get_content method
        """
        self.s3_storage.get_content('s3/key/path')
        mock_s3.get_content.assert_called_with(
            's3/key/path', bucket=self.bucket, client=self.s3_client)

    @patch('watchmen.utils.s3_storage.s3')
    def test_get_json_data(self, mock_s3):
        """
        test utils.s3_storage.S3Storage interfaces - get_json_data method
        """
        self.s3_storage.get_json_data('s3/key/path')
        mock_s3.get_json_data.assert_called_with(
            's3/key/path', bucket=self.bucket, client=self.s3_client)

    @patch('watchmen.utils.s3_storage.s3')
    def test_get_last_modified(self, mock_s3):
        """
        test utils.s3_storage.S3Storage interfaces - get_last_modified method
        """
        self.s3_storage.get_last_modified('s3/key/path')
        mock_s3.get_key.assert_called_with(
            's3/key/path', bucket=self.bucket, client=self.s3_client)

    @patch('watchmen.utils.s3_storage.s3')
    def test_get_parquet_content(self, mock_s3):
        """
        test utils.s3_storage.S3Storage interfaces - get_parquet_content method
        """
        self.s3_storage.get_parquet_content('s3/key/path')
        mock_s3.get_parquet_data.assert_called_with(
            's3/key/path', bucket=self.bucket, client=self.s3_client)

    @patch('watchmen.utils.s3_storage.s3')
    def test_move(self, mock_s3):
        """
        test utils.s3_storage.S3Storage interfaces - exists method
        """
        self.s3_storage.move('s3/key/source_path', 's3/key/target_path')
        mock_s3.mv_key.assert_called_with(
            's3/key/source_path', 's3/key/target_path',
            bucket=self.bucket, client=self.s3_resource)

    @patch('watchmen.utils.s3_storage.s3')
    def test_process(self, mock_s3):
        """
        test utils.s3_storage.S3Storage interfaces - process method
        """
        kwargs = {
            'bucket': self.bucket,
            'counter': 0,
            'key': 's2/key/path',
            'domains': 0,
        }
        self.s3_storage.process(self.doFunc, 's3/key/prefix/', **kwargs)
        mock_s3.process_keys.assert_called_with(
            self.doFunc, prefix='s3/key/prefix/', client=self.s3_client, **kwargs)

    @patch('watchmen.utils.s3_storage.s3')
    def test_save(self, mock_s3):
        """
        test utils.s3_storage.S3Storage interfaces - save method
        """
        self.s3_storage.save('s3/key/path', 'contents')
        mock_s3.copy_contents_to_bucket.assert_called_with(
            'contents', 's3/key/path', bucket=self.bucket, client=self.s3_client)
