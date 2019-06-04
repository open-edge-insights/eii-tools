FROM jfloff/alpine-python:3.4-slim
ADD requirements.txt /
ADD publisher.py /
RUN /entrypoint.sh
CMD ["python", "publisher.py"]
