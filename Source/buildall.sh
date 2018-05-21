#build the containers locally
docker build -t jakkaj/sampletrainer:dev ./training/src -f ./training/src/Dockerfile
docker build -t jakkaj/samplescorer:dev ./scoring/site -f ./scoring/site/Dockerfile