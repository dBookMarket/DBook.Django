ARG PYTHON_VERSION=${PYTHON_VERSION}
FROM python:${PYTHON_VERSION}
ENV PYTHONUNBUFFERED 1

WORKDIR /code

RUN apt-get update
RUN apt-get install -y wkhtmltopdf

# add fonts
RUN apt-get install -y fontconfig

# Google fonts
RUN wget https://github.com/google/fonts/archive/main.tar.gz -O gf.tar.gz
RUN tar -xf gf.tar.gz
RUN mkdir -p /usr/share/fonts/truetype/google-fonts
RUN find $PWD/fonts-main/ -name "*.ttf" -exec install -m644 {} /usr/share/fonts/truetype/google-fonts/ \; || return 1
RUN rm -f gf.tar.gz
RUN fc-cache -f && rm -rf /var/cache/*

RUN python -m pip install --upgrade pip -i https://pypi.mirrors.ustc.edu.cn/simple/

COPY ./requirements.txt ./
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

# daphne sock dirctory
RUN mkdir tmp
#COPY ./supervisord.conf /etc/supervisor/