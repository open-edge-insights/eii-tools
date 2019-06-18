FROM python:3.7-slim
ADD requirements.txt /
ADD publisher.py /
RUN pip3 install -r requirements.txt
CMD ["python", "publisher.py"]
