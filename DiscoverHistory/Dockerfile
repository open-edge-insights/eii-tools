# Dockerfile for FactoryControlApp
ARG EIS_VERSION
FROM ia_eisbase:${EIS_VERSION} as eisbase
LABEL description="DiscoverHistory image"

FROM ia_common:${EIS_VERSION} as common

FROM eisbase

ARG HOST_TIME_ZONE=""

ARG DEBIAN_FRONTEND=noninteractive
RUN echo "$HOST_TIME_ZONE">/etc/timezone
RUN cat /etc/timezone
RUN apt-get update && \
    apt-get install -y tzdata && \
    ln -sf /usr/share/zoneinfo/${HOST_TIME_ZONE} /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata

COPY --from=common ${GO_WORK_DIR}/common/libs ${PY_WORK_DIR}/libs
COPY --from=common ${GO_WORK_DIR}/common/util ${PY_WORK_DIR}/util
COPY --from=common ${GO_WORK_DIR}/common/cmake ${PY_WORK_DIR}/common/cmake
COPY --from=common /usr/local/lib /usr/local/lib
COPY --from=common /usr/local/lib/python3.6/dist-packages/ /usr/local/lib/python3.6/dist-packages/

COPY requirements.txt .
RUN pip3 install -r requirements.txt
RUN apt-get install -y python3.6-tk

ENV PYTHONPATH ${PYTHONPATH}:.:../../
COPY ./ ./DiscoverHistory
WORKDIR ./DiscoverHistory/src


ENTRYPOINT [ "python3.6", "main.py" ]
