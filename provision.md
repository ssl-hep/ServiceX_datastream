# Provisioning a Kafka Cluster for ServiceX

This document outlines the steps to deploy and use kafka in our GKE cluster.

## Create a Kubernetes Cluster
This step is optional and is only needed if there is not an existing kubernetes
cluster that you are deploying to

```bash
 gcloud container clusters create "kafka" \
--zone "us-central1-a" \
--username "admin" \
--machine-type "n1-standard-4" \
--image-type "UBUNTU" \
--disk-type "pd-ssd" \
--disk-size "100" \
--num-nodes "3" \
--enable-cloud-logging \
--enable-cloud-monitoring \
--network "default" \
--addons HorizontalPodAutoscaling,HttpLoadBalancing,KubernetesDashboard
```

You will need to get the credentials to the kubernetes cluster to be able to 
use `kubectl`

```bash
% export KUBECONFIG = ~/.kube/kafka
% gcloud container clusters get-credentials kafka --zone us-central1-a
```

## Install Kafka Helm Chart
We will use the [official kafka helm chart](https://github.com/helm/charts/tree/master/incubator/kafka)
to deploy kafka.

First we need to create an RBAC role for the helm _tiller_ service using a 
simple yaml file from this repo:
```bash
% kubectl create -f kube/rbac-tiller.yaml
```

Then we initialize the helm service:
```bash
% helm init --service-account tiller --history-max 200
```

Finally we install the helm chart into the _kafka_ namespace, using the 
custom values created here:
```bash
% helm repo add incubator http://storage.googleapis.com/kubernetes-charts-incubator
% helm install --name servicex-kafka -f values.yaml --namespace kafka incubator/kafka
```

## Create a Topic from Command Line
Ordinarily the transformer or API gateway will create the Kafka topic
based on the dataset token. For testing you may want to create one 
manually. We'll install a little pod with the Java command line tools and
run the command.

```bash
% kubectl create -n kafka -f kube/testclient.yaml
```

You can run commands with:
```bash
% kubectl -n kafka exec -it testclient bash
```

Create a serviceX topic with 100 partitions and replication factor of one as:
```bash
% kubectl -n kafka exec testclient -- /opt/kafka/bin/kafka-topics.sh --zookeeper servicex-kafka-zookeeper --topic servicex --create --partitions 100 --replication-factor 1
```


## Install an Internal Toolkit for Working with Kafka
We have a simple pod that can be deployed into the cluster that has the useful
[kafkacat](https://github.com/edenhill/kafkacat/blob/master/README.md)
command line tool.

```bash
% kubectl create -n kafka -f kube/kafkacat.yaml
```

You can run commands with:
```bash
% kubectl -n kafka exec -it kafkacat bash
```

You can list topics with a command inside this pod like:
```bash
% kafkacat -b servicex-kafka -L
```

You can use kafkacat in consumer mode to see messages being written to the
topic with:
```bash
% kafkacat -b servicex-kafka -t servicex -C
```

