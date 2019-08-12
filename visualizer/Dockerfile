# Dockerfile for Visualizer
ARG IEI_VERSION
FROM ia_pybase:$IEI_VERSION
LABEL description="Visualizer image"

ARG HOST_TIME_ZONE=""

WORKDIR /IEI

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
                       libsm6 libxext6 libxrender-dev

RUN wget https://bootstrap.pypa.io/get-pip.py && \
    python3.6 get-pip.py
ADD tools/visualizer/requirements.txt .
RUN pip3 install -r requirements.txt

RUN apt-get install -y python3.6-tk

ARG IEI_USER_NAME
RUN adduser --quiet --disabled-password ${IEI_USER_NAME}

RUN touch visualize.log && \
    chown ${IEI_USER_NAME}:${IEI_USER_NAME} visualize.log &&  \
    chmod 777 visualize.log

RUN apt-get -y install git
ENV PY_ETCD3_VERSION cdc4c48bde88a795230a02aa574df84ed9ccfa52
RUN git clone https://github.com/kragniz/python-etcd3 && \
    cd python-etcd3 && \
    git checkout ${PY_ETCD3_VERSION} && \
    python3.6 setup.py install && \
    cd .. && \
    rm -rf python-etcd3

ENV PYTHONPATH /IEI/
ENV LD_LIBRARY_PATH /usr/local/lib
ADD libs/ ./libs
ADD tools/visualizer/visualize.py .

ENTRYPOINT ["python3.6", "visualize.py"]
