# ServiceX DataStream
Event Data Streaming Service for ServiceX. This service accepts flattened
N-tuples ans streams them out for analysis using Kafka.

# Installation
The Datastream Service runs inside a Kubernetes cluster.
## Install Kafka 
```bash
$ helm repo add incubator http://storage.googleapis.com/kubernetes-charts-incubator
$ kubectl create ns kafka
$ helm install --name my-kafka --namespace kafka incubator/kafka
```

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

