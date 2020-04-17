# Dockerfile for TimeSeriesProfiler
ARG EIS_VERSION
FROM ia_eisbase:${EIS_VERSION} as eisbase
LABEL description="TimeSeriesProfiler image"

FROM ia_common:${EIS_VERSION} as common

FROM eisbase

COPY --from=common ${GO_WORK_DIR}/common/libs ${PY_WORK_DIR}/libs
COPY --from=common ${GO_WORK_DIR}/common/util ${PY_WORK_DIR}/util
COPY --from=common ${GO_WORK_DIR}/common/cmake ${PY_WORK_DIR}/common/cmake
COPY --from=common /usr/local/lib /usr/local/lib
COPY --from=common /usr/local/lib/python3.6/dist-packages/ /usr/local/lib/python3.6/dist-packages/

ENV PYTHONPATH ${PYTHONPATH}:.:../../

#Removing build dependencies
RUN apt-get remove -y wget && \
    apt-get remove -y git && \
    apt-get remove curl && \
    apt-get autoremove -y

RUN mkdir /EIS/out/

COPY ./timeseries_profiler.py ./timeseries_profiler.py

ENTRYPOINT [ "python3.6", "timeseries_profiler.py" ]
