
#This image has been pushed to Docker Hub as jakkaj/sampletrainer
FROM python:3.5.5-alpine3.4
RUN pip install -U python-dotenv
ADD train.py ./
#Uncomment this to configure the required environment variable for output paths
#ENV MODELFOLDER=/tmp
CMD ["python", "train.py"]