ARG UBUNTU_IMAGE_VERSION
FROM ubuntu:18.04

ARG HOST_TIME_ZONE=""

WORKDIR /iei

# Setting timezone inside the container
RUN echo "$HOST_TIME_ZONE" >/etc/timezone
RUN cat /etc/timezone
RUN apt-get update
RUN apt-get install -y tzdata && \
    ln -sf /usr/share/zoneinfo/${HOST_TIME_ZONE} /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata

# Installing dependencies
RUN apt-get install -y libmbedtls-dev \
                       build-essential \
                       pkg-config \
                       wget \
                       libsm6 libxext6 libxrender-dev

RUN apt-get install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update
RUN apt-get install -y python3.6 python3.6-dev wget

# Needed for only ubuntu 18.04
RUN apt-get install -y python3-distutils

RUN wget https://bootstrap.pypa.io/get-pip.py && \
    python3.6 get-pip.py
ADD tools/visualizer/requirements.txt .
RUN pip3 install -r requirements.txt

RUN apt-get install -y python3-tk

RUN adduser --quiet --disabled-password ieiuser

RUN touch visualize.log && \
    chown ieiuser:ieiuser visualize.log &&  \
    chmod 777 visualize.log

RUN apt-get -y install git
ENV PY_ETCD3_VERSION cdc4c48bde88a795230a02aa574df84ed9ccfa52
RUN git clone https://github.com/kragniz/python-etcd3 && \
    cd python-etcd3 && \
    git checkout ${PY_ETCD3_VERSION} && \
    python3.6 setup.py install && \
    cd .. && \
    rm -rf python-etcd3

ADD libs ./libs
ENV PYTHONPATH /iei
ADD tools/visualizer/source.sh .
RUN ./source.sh
ADD tools/visualizer/visualize.py .

ENTRYPOINT ["python3.6", "visualize.py"]
