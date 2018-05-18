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



### Building the Model Container
With VSTS it's super easy to build and deploy containers to Kubernetes. [This article](http://jessicadeen.com/tech/microsoft/how-to-deploy-to-kubernetes-using-helm-and-vsts/) by Jessica Deen gives a great overview of the process. We'll not repeat those steps here.

We'll be doing similar steps, with the addition that we'll be creating and updating a Helm package as part of the build that will result in a build artefact. 

### Parameteriseing the Deployment 

The model takes a range of parameters - things like where to source the training data from as well as where to save the output. All these parameters are "baked in" to the output build - keeping in line with the immutable deployment requirement. 

The values are placed in to the Helm Chart's values.yaml file. It is possible to pass in values to Helm Charts during publication using `--set` but that would mean an outside config requirement during publication. 

### Variable Groups

The values are passed in to the build using [Variable Groups](https://docs.microsoft.com/en-us/vsts/build-release/concepts/library/variable-groups?view=vsts). These allow you to create centrally managed variables for builds across your VSTS collection. These variables can be adjusted at build time. This allows users of the system to fire off parameterised builds without having to know "how" to build and deploy an instance of the system to the cluster. 

### Processing the variables

The end artefact of this first stage of the build is a Helm Chart. This chart contains all the environment variables the app needs to operate. It's all baked in to the chart so it can be re-deployed at a later time, and later on operations can go back and see what parameters were used when the system was deployed.  

The template Helm Chart (under Source\training\helm\traininjob) looks like this:

```yaml
replicaCount: 1

image:
  repository: jakkaj/sampletrainer
  tag: dev
  pullPolicy: IfNotPresent

outputs:
  modelfolder: /mnt/azure/
  mountpath: /mnt/azure

build:
  number: 13
```

We need a way to modify that to add in some build environemnt variables, including the values that were passed in to the build via VSTS variables. 

### Yaml Writer

To update and existing yaml file or to create a new one from VSTS build arguments you can use the VSTS. Deploy the extension by following the instructions [here](https://github.com/jakkaj/yamlw_vststask). 

Add the YamlWriter as a new build task. 

File: `Source/training/helm/trainingjob/values.yaml`. 

Our Parameters look as following - although yours will differ!

```image.repository='janisonhackregistry.azurecr.io/$(Build.Repository.Name)',image.tag='$(Build.BuildNumber)',outputs.modelfolder='/mnt/azure/$(Build.BuildNumber)',env.BLOB_STORAGE_ACCOUNT='$(BLOB_STORAGE_ACCOUNT)',env.BLOB_STORAGE_KEY='$(BLOB_STORAGE_KEY)', env.BLOB_STORAGE_CONTAINER='$(BLOB_STORAGE_CONTAINER)',env.BLOB_STORAGE_CSV_FOLDER='$(BLOB_STORAGE_CSV_FOLDER)',env.TENANTID='$(TENANTID)'```

This tool will open `values.yaml` and add/update values according to the parameters passed in. 

The output looks something like this

```
2018-05-18T03:41:45.6562552Z ##[section]Starting: YamlWriter 
2018-05-18T03:41:45.6632990Z ==============================================================================
2018-05-18T03:41:45.6645860Z Task         : Yaml Writer
2018-05-18T03:41:45.6659314Z Description  : Feed in parameters to write out yaml to new or existing files
2018-05-18T03:41:45.6674165Z Version      : 0.18.0
2018-05-18T03:41:45.6688693Z Author       : Jordan Knight
2018-05-18T03:41:45.6704359Z Help         : Pass through build params and other interesting things by using a comma separated list of name value pairs. Supports deep creation - e.g. something.somethingelse=10,something.somethingelseagain='hi'. New files will be created, and existing files updated. 
2018-05-18T03:41:45.6721664Z ==============================================================================
2018-05-18T03:41:46.0603680Z File: /opt/vsts/work/1/s/Source/training/helm/trainingjob/values.yaml (exists: true)
2018-05-18T03:41:46.0622913Z Settings: image.repository='<youwish>/Documentation',image.tag='115',outputs.modelfolder='/mnt/azure/115',env.BLOB_STORAGE_ACCOUNT='<youwish>',env.BLOB_STORAGE_KEY='<youwish>', env.BLOB_STORAGE_CONTAINER='<youwish>',env.BLOB_STORAGE_CSV_FOLDER='"2018\/05\/08"',env.TENANTID='<youwish>'
2018-05-18T03:41:46.0640773Z Dry run: false
2018-05-18T03:41:46.0709407Z Writing file: /opt/vsts/work/1/s/Source/training/helm/trainingjob/values.yaml
2018-05-18T03:41:46.0726587Z Result:
2018-05-18T03:41:46.0746248Z  replicaCount: 1
2018-05-18T03:41:46.0759265Z image:
2018-05-18T03:41:46.0771294Z   repository: <youwish>/Documentation
2018-05-18T03:41:46.0785611Z   tag: '115'
2018-05-18T03:41:46.0801686Z   pullPolicy: IfNotPresent   
2018-05-18T03:41:46.0829768Z     
2018-05-18T03:41:46.0877844Z outputs:
2018-05-18T03:41:46.0889861Z   modelfolder: /mnt/azure/115
2018-05-18T03:41:46.0902953Z   mountpath: /mnt/azure
2018-05-18T03:41:46.0915630Z build:
2018-05-18T03:41:46.0927381Z   number: 13
2018-05-18T03:41:46.0939422Z env:
2018-05-18T03:41:46.0950803Z   BLOB_STORAGE_ACCOUNT: <youwish>
2018-05-18T03:41:46.0965333Z   BLOB_STORAGE_KEY: >-
2018-05-18T03:41:46.0978866Z     <youwish>
2018-05-18T03:41:46.0990595Z   BLOB_STORAGE_CONTAINER: <youwish>
2018-05-18T03:41:46.1004951Z   BLOB_STORAGE_CSV_FOLDER: '"2018/05/08"'
2018-05-18T03:41:46.1019701Z   TENANTID: <youwish>
2018-05-18T03:41:46.1028046Z 
2018-05-18T03:41:46.1054089Z ##[section]Finishing: YamlWriter 

```

This process loaded the `values.yaml` file, modified and saved it back. Then the build process then archites the Helm Chart directory and saves it as a build artefact. 

- Create a Archive task and set Root folder to `Source/training/helm/trainingjob` the archive type to tar and gz and archive output `$(Build.ArtifactStagingDirectory)/$(Build.BuildId).tar.gz`
- Create a Publish Artifact task to prep the chart for release  (Path to publish: `$(Build.ArtifactStagingDirectory)/$(Build.BuildId).tar.gz`).

## Prep The Cluster

The cluster will need some preparation before the workloads can run - in this case there needs to be a shared location to save the trained models to. 

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

## Test the Helm Chart

Before we automate the Helm Chart deployment it's a good idea to try it out. Next step is to pull the chart and manually deploy it to do the cluster. 

Navgiate to the compelted build in VSTS and download the Helm Chat artifact. Extract zip, and the Helm Chart will be the tar.gz inside. 

### The Model



## Scoring build and deployment 

## Intelligent routing



# Links

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