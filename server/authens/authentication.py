from rest_framework.authentication import TokenAuthentication


class BaseTokenAuthentication(TokenAuthentication):
    keyword = 'Bearer'
