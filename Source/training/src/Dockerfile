#this is a 1.5 GB image - sorry :)
FROM continuumio/anaconda3
RUN pip install -U python-dotenv
ADD train.py ./
#Uncomment this to configure the required environment variable for output paths
#ENV MODELFOLDER=/tmp
CMD ["python", "train.py"]