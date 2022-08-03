ARG PYTHON_VERSION=${PYTHON_VERSION}
FROM python:${PYTHON_VERSION}
ENV PYTHONUNBUFFERED 1

#RUN mkdir /code
WORKDIR /code
#ENV WORKDIR /code

COPY ./requirements.txt ./

RUN python -m pip install --upgrade pip -i https://pypi.mirrors.ustc.edu.cn/simple/
# pip source
# https://pypi.python.org/simple/
# https://pypi.mirrors.ustc.edu.cn/simple/
# https://pypi.tuna.tsinghua.edu.cn/simple/
RUN pip install -r requirements.txt -i https://pypi.mirrors.ustc.edu.cn/simple/

# install nft.storage
#RUN pip install git+https://github.com/nftstorage/python-client.git

COPY ./ ./

RUN chmod +x checkdbconnection.py
RUN chmod +x startserver.sh
RUN chmod +x runtest.sh

#COPY ./supervisord.conf /etc/supervisor/