s

in istio

deploy a sample helm a couple of times, increment the build number and mout path in the values.yaml each time. 

istioctl gateway.yaml
istioctl virtual-service.yaml


kubectl get svc istio-ingressgateway -n istio-system