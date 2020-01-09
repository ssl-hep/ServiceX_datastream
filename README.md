# ServiceX DataStream
Event Data Streaming Service for ServiceX. This service accepts flattened
N-tuples ans streams them out for analysis using Kafka.

# Installation
The Datastream Service runs inside a Kubernetes cluster.
## Install Kafka 
### When tiller is available
```bash
$ helm repo add incubator http://storage.googleapis.com/kubernetes-charts-incubator
$ kubectl create ns kafka
$ helm install --name my-kafka --namespace kafka incubator/kafka
$ helm install --name my-kafka --namespace kafka stable/kafka-manager
```
### When tiller is not available
This may happen if you do not have full access to the Kubernetes cluster, these can be run locally, with access to start Kubernetes services and pods. You should have the values.yaml from this repository to alter the default values to ones better suited to running Kafka for servicex.
```bash
$ helm repo add incubator http://storage.googleapis.com/kubernetes-charts-incubator
$ helm fetch --untar --untardir <LOCATION OF CHARTS> incubator/kafka
$ helm fetch --untar --untardir <LOCATION OF CHARTS> stable/kafka-manager
$ cp values.yaml <LOCATION OF CHARTS>/kafka
$ helm template --name <RELEASE PREFIX> --output-dir <LOCATION FOR MANIFEST> <LOCATION OF CHARTS>
$ kubectl -n <KUBERNETES NAMESPACE> apply --recursive -f <LOCATION FOR MANIFEST>
```
## Allow remote access to Kafka
The values.yaml file is set to allow remote access to Kafka. To make this happen smoothly you want to check a few things, and make the following changes to values.yaml.
* Line 36: Change the domain to your domain
* Line 46: Change the domain to your domain

You will also want to set up DNS to the IPs that get assigned to the <RELEASE PREFIX>-#-external services.
The number in the service name will match up to the ${KAFKA_BROKER_ID} on line 46. Set up your DNS names for individual external IPs following the pattern on line 46. Without any changes from the version here: kafka#.domain
For ease of access you may want to set up a DNS round robin as well. kafka.domain will allow you to specify kafka.domain:19092 as your broker from kafka command line, rather than specifying a specific external service. Unfortunately if an external service fails you will still need to modify your list of advertised listeners, or else kafka won't find a broker and will error out.

Also note that by default Kafka has no authentication set up. This means that anyone with your broker names can read and write to/from the Kafka instance. This will be addressed here at a later time.

## Create a namespace
We will put all of our applicaton pods in the `servicex` namespace.

```bash
% kubectl create namespace servicex
```

## Set up a shared volume for Event Data
Create a persistent volume claim called `servicex-pvc`. We create this with
```bash
% kubectl -n servicex create -f kube/pvc.yml
```

To make it easier to work with this persistent volume, we will create a busybox
pod with the volume mounted.
```bash
% kubectl -n servicex create -f busybox.yml
```

When the pod is ready, you can create a shell with 
```bash
% kubectl exec -it -n servicex busybox sh
```
you can see the mount under `/servicex`

You can copy a sample xAOD Root file into the shared volume using this pod with
```bash
% kubectl cp AOD.11182705._000001.pool.root.1 servicex/busybox:servicex/AOD.11182705._000001.pool.root.1
```

# Run the Transformer on the Data
We use a containerized transformer from 
[ServiceX_transformer](https://github.com/ssl-hep/ServiceX_transformer) to 
read the xAOD File and reduce it to flattened n-tuples.

```bash
% kubectl -n servicex create -f transform_job.yml
``` 

When this job complets, there will be two files in the shared volume:
- flat_file.root: Flattened n-tuple root file
- xaodBranches.txt: Dump of all of the branch names from the original file
 
# Acknowledgements

This project is supported by National Science Foundation under Cooperative 
Agreement OAC-1836650. Any opinions, findings, conclusions or recommendations
expressed in this material are those of the authors and do not necessarily 
reflect the views of the National Science Foundation.

