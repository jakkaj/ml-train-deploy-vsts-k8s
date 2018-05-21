#!/bin/bash
while [ ! -f $MODELFOLDER/complete.txt ]; do
    echo "File not found!" $MODELFOLDER
    sleep 2
done
value=$(<$MODELFOLDER/complete.txt)
#echo "model_score $value" | curl --data-binary @- http://prometheus-pushgateway.prometheus.svc.cluster.local:9091/metrics/job/some_job
echo "File found"