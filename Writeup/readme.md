# Machine Learning Training and Scoring Pipeline
*A devops based pipeline to train models and orchestrate them for scoring in a Kubernetes cluster*

This article describes how we built a pipeline to train and deliver a machine learning model and deliver it to production for scoring - using standard DevOps practices. 

The project is an automated build and release system based on [Visual Studio Team Services](https://www.visualstudio.com/team-services/). 

The main tenets were:

### The Model
- Model to be trained as a Kubernetes job (automatically by build process)
- Model to be saved to a pre-determined location for use by the scoring side
- Model to be managed as part of a build process
    - Linked back to PR, tasks, comments etc in VSTS
    - Must allow for model provenance
    - Can be kicked of automatically or manually by passing in required parameters

### Containers
- All components of system must operate inside Docker containers

- DevOps concepts:
    - Enables blue/green deployments
    - Promotions between environments achieved by the VSTS release mechanism
    - Enable CI/CD scenarios
    - Automated from end-to-end

- Immutable deployments
    - Deployments must be versioned
    - Immutable
    - Replicable (re-create later)
    - Clearly defined deployment boundary

- Service mesh
    - Deployment versioning to allow for Istio control
    - Can support intelligent routing
    - A/B splits
    - Traffic % based splits
    - Other intelligent traffic scrutiny / routing

# Getting Started

Before you start you'll need the following things installed / setup.

- A [Visual Studio Team Services](https://www.visualstudio.com/team-services/) instance. You can set one up as a free trial, or if you have an MSDN subscription you may have some licenses available.
- A [Kubernetes](https://kubernetes.io/) cluster. We used the [acs-engine yeoman generator](https://github.com/jakkaj/generator-acsengine) to set one up in Azure. 
    - Make sure you set up Kubernetes v1.9 or better so the automatic sidecar injection works with [Istio](https://istio.io/docs/setup/kubernetes/quick-start.html) (more on that later!)
- or... [Minikube](https://kubernetes.io/docs/getting-started-guides/minikube/) if you want to dev locally. There are other options like the latest edge version of Docker for Windows can set up a local cluster for you.
- [Docker](https://docs.docker.com/install/)
- [Visual Studio Code](https://code.visualstudio.com/)
- Azure stuff: an [Azure Container Registry](https://azure.microsoft.com/en-gb/services/container-registry/), [Azure Blob Storage](https://azure.microsoft.com/en-gb/services/storage/)


For new users (and for demos!) a graphical Kubernetes app can be helpful. [Kubernetic](https://kubernetic.com/) is one such app. Of interest is that the app refreshes immediately when the cluster state changes, unlike the web ui which needs to be refreshed manually. 

## The Model Training Job

Our statement at the beginning of the project was to set up a machine learning delivery capability via DevOps based practices. 

The practical aim of the project is to build *a* model through training and delivering to a scoring system - the model itself is not all that important... i.e. this process could be used with any training system based around any technology (thank you containers!). 

### Input Data
The model is a collaborative filtering model to assist with recommendations. It takes data that has been extracted from the production databases. The ETL is orchestrated by [Azure Data Factory](https://azure.microsoft.com/en-us/services/data-factory/) and saves data to an [Azure Blob Storage](https://azure.microsoft.com/en-gb/services/storage/blobs/) account in CSV format under a convention based folder structure. This section is out of scope for this document. 

The input locations are passed in to the containers as environment variables. 

### Parameters
The model training container takes a series of parameters for the source data location as well as the output location. These parameters are passed in to the model by the build as environment variables to the Kubernetes job. The model output location is based on the build number of the VSTS build. The other parameters are generated and passed in as build variables.

This parameterisation is used heavily in the system. To help make parameterisation simpler we've opted to use [Helm](https://github.com/kubernetes/helm) to make packages which form the system's deployments. The build system prepares the Helm Charts and deploys them to the cluster. 

### Set-up the Environment
Before the model can be trained the environment needs some set-up. In this system the model is output to an Azure File share - which is stored in blob storage. You'll need to create a PVC (PersistentVolumeClaim) as somewhere to save the model. 

The output path is taken in as an environment variable MODELFOLDER. This is passed through the helm chart to the kube yaml file which is applied to the cluster. This folder path is parameterised based on the build number, so each build will output to a different folder. 

By having these variables passed in as environment variables as opposed to something like config maps or similar the deployment is immutable, the settings are always locked once deployed. Importantly the deployment can be repeated later with the same settings from the same historical Git tag. 

#### Add the PVC

In Azure we add the PVC as an Azure File based PVC, which links to [Azure Files](https://docs.microsoft.com/en-us/azure/storage/files/storage-files-introduction) over the SMB protocol. This location is accessible outside the cluster and can be used between nodes. 

From the `Source\kube` subfolder run:

```
kubectl apply -f pvc_azure.yml
```

Or if you're running locally in something like Minikube run the following to set up a local PVC that will stand in for Azure Files during your development. 

```
kubectl apply -f pvc_minikube.yml
```

You can of course use any PVC type you'd like as long as they are accessible across nodes and pods. 

**Note:** This step was not performed as part of the build process. You could automate this, but in our case it was just as easy to apply it as it only has to be done once for the cluster (per namespace). 

### Building the Model Container
With VSTS it's super easy to build and deploy containers to Kubernetes. [This article](http://jessicadeen.com/tech/microsoft/how-to-deploy-to-kubernetes-using-helm-and-vsts/) by Jessica Deen gives a great overview of the process. We'll not repeat those steps here.

We'll be doing similar steps, with the addition that we'll be creating and updating a Helm package as part of the build that will result in a build artefact. 

### Parameteriseing the Deployment 





### The Model



## Scoring build and deployment 

## Intelligent routing



#Links

## Microsoft Stuff
- [Visual Studio Team Services](https://www.visualstudio.com/team-services/)
- [Azure Data Factory](https://azure.microsoft.com/en-us/services/data-factory/)
- [Azure Blob Storage](https://azure.microsoft.com/en-gb/services/storage/blobs/)
- [Azure Files](https://docs.microsoft.com/en-us/azure/storage/files/storage-files-introduction)
- [Visual Studio Code](https://code.visualstudio.com/)
## Kubernetes and Container Stuff
- [Kubernetes](https://kubernetes.io/)
- [Istio](https://istio.io/docs/setup/kubernetes/quick-start.html)
- [Docker](https://docs.docker.com/install/)
- [Minikube](https://kubernetes.io/docs/getting-started-guides/minikube/)