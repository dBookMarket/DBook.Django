import os.path
import os
import nft_storage
from nft_storage.api import nft_storage_api
import requests
from requests_toolbelt import MultipartEncoder


class NFTStorageHandler(object):
    base_api = 'https://api.nft.storage'

    def __init__(self):
        self.access_token = os.getenv('NFT_STORAGE_ACCESS_TOKEN')
        self.configuration = nft_storage.Configuration()

    def store(self, file_path: str):
        self.configuration.__setattr__('access_token', self.access_token)
        with nft_storage.ApiClient(self.configuration) as api_client:
            api = nft_storage_api.NFTStorageAPI(api_client)

            try:
                body = open(file_path, 'rb')
                # https://github.com/nftstorage/python-client/issues/1
                response = api.store(body, _check_return_type=False)
            except nft_storage.ApiException as e:
                print(f'Exception when calling NFTStorageAPI->store: {e}')
                raise

            if not response['ok']:
                raise RuntimeError('Upload file to nft storage fail')
            return response['value']['cid']

    def bulk_upload(self, dir_path: str, retry: int = 3) -> str:
        """
        :param dir_path: str, file directory
        :param retry: int, the number of retry to upload FOR TIMEOUT ERROR
        :return:
        """
        print(f'Running bulk_upload, dir_path: {dir_path}, retry: {3 - retry}')
        if not os.path.isdir(dir_path):
            raise ValueError('dir_path must be a directory path')

        try:
            fields = []
            for root, dirs, files in os.walk(dir_path):
                for file_name in sorted(files):
                    f_path = os.path.join(root, file_name)
                    fields.append(('file', (file_name, open(f_path, 'rb'), 'application/octet-stream')))
            # the limit of upload size 100MB
            me = MultipartEncoder(fields=fields)
            headers = {
                'Content-Type': me.content_type,
                'authorization': f"Bearer {self.access_token}"
            }
            print(f'Ready to upload, request body size: {me.len}')
            res = requests.post(f'{self.base_api}/upload', data=me, headers=headers)
        except Exception as e:
            print(f'Exception when calling NFTStorageAPI->bulk_upload: {e}')
            raise

        data = res.json()
        if not data['ok']:
            print(f"Error Response when calling NFTStorageAPI->bulk_upload -> {data['error']}")
            # if 524 time out, then retry
            # code is Error means response status is 500
            if data['error'].get('code') == 'Error' and data['error'].get('message', '').find('524') != -1:
                if retry > 0:
                    self.bulk_upload(dir_path, retry - 1)
            raise RuntimeError(data['error'].get('message', ''))
        return data['value']['cid']

    def check(self, cid: str):
        with nft_storage.ApiClient(self.configuration) as api_client:
            api = nft_storage_api.NFTStorageAPI(api_client)

            try:
                response = api.check(cid)
            except nft_storage.ApiException as e:
                print(f'Exception when calling NFTStorageAPI->check: {e}')
                raise

            if not response['ok']:
                raise RuntimeError('Check file from nft storage fail')
            return response['value']

    def delete(self, cid: str):
        self.configuration.__setattr__('access_token', self.access_token)
        with nft_storage.ApiClient(self.configuration) as api_client:
            api = nft_storage_api.NFTStorageAPI(api_client)

            try:
                response = api.delete(cid)
            except nft_storage.ApiException as e:
                print(f'Exception when calling NFTStorageAPI->delete: {e}')
                raise

            if not response['ok']:
                raise RuntimeError('Delete file from nft storage fail')

    @staticmethod
    def get_nft_url(cid: str):
        """
        the url of token level, which means a token is a file
        :param cid: str
        :return:
        """
        return f'https://{cid}.ipfs.nftstorage.link'

    @classmethod
    def get_file_url(cls, cid: str, file_name: str):
        """
        the url of file level, which means there is a lot of files in this token
        :param cid: str
        :param file_name: str
        :return:
        """
        nft_url = cls.get_nft_url(cid)
        return f'{nft_url}/{file_name}'

    def retrieve(self, cid: str):
        headers = {
            'authorization': f"Bearer {self.access_token}"
        }

        try:
            response = requests.get(f'{self.base_api}/{cid}', headers=headers)
        except Exception as e:
            print(f'Exception when calling NFTStorageAPI->retrieve: {e}')
            raise

        data = response.json()
        if not data['ok']:
            raise RuntimeError(data['error']['message'])
        return data['value']
