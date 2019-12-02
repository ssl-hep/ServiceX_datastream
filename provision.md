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
% export KUBECONFIG=~/.kube/kafka
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

We've set up some useful values for a serviceX kafka in 
[values.yaml](https://github.com/ssl-hep/ServiceX_datastream/blob/master/values.yaml).

It establishes the size for the broker logs persistent volumes, and instructs
helm to set the cluster up for remote access. Use the `external.domain` property
to specify the domain name that this cluster will be known bu. Pay careful attention to the
`advertised.listeners` settings. This provides a pattern for the DNS A records
that will need to be created for outsiders to access the cluster.

We install the helm chart into the _kafka_ namespace, using the 
custom values:
```bash
% helm repo add incubator http://storage.googleapis.com/kubernetes-charts-incubator
% helm install --name servicex-kafka -f values.yaml --namespace kafka incubator/kafka
```
## Create DNS A Records for the Brokers
After the helm chart is installed, it will print out some notes. The last part
of these notes contain the external host names expected for each of the brokers.
These will need to be mapped to the appropriate load balancers.

It will take a few minutes for GKE to provision the external IP addresses for 
the load balancers. You can view the assignments with:
```bash
% kubectl get service -n kafka
```

When the `EXTERNAL-IP` values for the load balancers goes from `<pending>` to IP
addresses, you can create matching A records for the external names.

For example
```
servicex-kafka-0.slateci.net   35.225.182.253   
servicex-kafka-1.slateci.net   35.222.121.193   
servicex-kafka-2.slateci.net   35.226.0.2
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
% kubectl -n kafka exec testclient -- /opt/kafka/bin/kafka-topics.sh \
    --zookeeper servicex-kafka-zookeeper \
    --topic servicex --create \
    --partitions 100 --replication-factor 1 \
    --config compression.type=lz4
```

See how many messages are in a topic
```bash
% /kafka-run-class.sh kafka.tools.GetOffsetShell --broker-list servicex-kafka-0.slateci.net:19092 --topic servicex
```

See where the consumer offset is currently for each topic:
```bash
% ./kafka-consumer-groups.sh --bootstrap-server servicex-kafka-0.slateci.net:19092 --group hist --describe
```

Reset consumer group
```bash
% ./kafka-consumer-groups.sh --bootstrap-server servicex-kafka-0.slateci.net:19092 --group hist --topic hists --reset-offsets --to-earliest --execute
```
## Deploying the Management Console
We use the Yahoo Kafka Manager to explore what is going on inside the kafka
cluster.

It can easily be deployed with:
```bash
% helm install stable/kafka-manager --name kafka-manager --namespace kafka -f kafka-manager-values.yaml
```

It uses basic auth:
* Username: admin
* Password: servicex


The serviceX cluster doesn't get added correctly to the managed lists so you 
have to go in via the ui, select _Add Cluster_ from the _Cluster_ drop
down.

The zookeeper hosts should be set to `servicex-kafka-zookeeper:2181` - you may
also need to select the option for _Poll consumer information_

## Deleting Kafka Deployment
It's easy to delete the helm deployment and free up the resources
```bash
% helm delete --purge servicex-kafka
```

