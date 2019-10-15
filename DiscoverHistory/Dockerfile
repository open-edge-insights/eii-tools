# Dockerfile for FactoryControlApp
ARG EIS_VERSION
FROM ia_eisbase:${EIS_VERSION} as eisbase
LABEL description="DiscoverHistory image"

FROM ia_common:${EIS_VERSION} as common

FROM eisbase

ARG HOST_TIME_ZONE=""

COPY --from=common /libs ${PY_WORK_DIR}/libs
COPY --from=common /util ${PY_WORK_DIR}/util

ARG DEBIAN_FRONTEND=noninteractive
RUN echo "$HOST_TIME_ZONE">/etc/timezone
RUN cat /etc/timezone
RUN apt-get update && \
    apt-get install -y tzdata && \
    ln -sf /usr/share/zoneinfo/${HOST_TIME_ZONE} /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata


COPY requirements.txt .
RUN pip3 install -r requirements.txt
RUN apt-get install -y python3.6-tk
RUN cd ./libs/EISMessageBus && \
    rm -rf build deps && \
    mkdir build && \
    cd build && \
    cmake -DWITH_PYTHON=ON .. && \
    make && \
    make install
ENV PYTHONPATH ${PYTHONPATH}:.:../../
COPY ./ ./DiscoverHistory
WORKDIR ./DiscoverHistory/src


ENTRYPOINT [ "python3.6", "main.py" ]
