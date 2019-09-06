FROM python:3.7-slim
COPY requirements.txt /
COPY publisher.py /
COPY demo_datafile.csv /
RUN pip3 install -r requirements.txt

ENTRYPOINT ["python", "publisher.py"]
