FROM python:3.7-slim
COPY requirements.txt /
COPY publisher.py /
RUN pip3 install -r requirements.txt
CMD ["python", "publisher.py"]
