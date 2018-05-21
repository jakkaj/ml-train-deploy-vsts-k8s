FROM ubuntu:16.04
RUN apt-get update
RUN apt-get install curl -y
ADD ./waiter.sh ./

CMD ["bash", "waiter.sh"]
