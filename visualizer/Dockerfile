ARG UBUNTU_IMAGE_VERSION
FROM ubuntu:${UBUNTU_IMAGE_VERSION}

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
ADD requirements.txt .
RUN pip3 install -r requirements.txt

RUN apt-get install -y python3-tk

RUN adduser --quiet --disabled-password ieiuser

RUN touch visualize.log && \
    chown ieiuser:ieiuser visualize.log &&  \
    chmod 777 visualize.log

ADD source.sh .
RUN ./source.sh
ADD visualize.py .

ENTRYPOINT ["python3.6", "visualize.py"]
