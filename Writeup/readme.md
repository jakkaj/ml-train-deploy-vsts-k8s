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
- The deployment to include the scoring site
    - Model training code and scoring site deployed as a unit

### Containers
- All components of system must operate inside Docker containers

- DevOps concepts:
    - Enables blue/green deployments
    - Promotions between environments achieved by the VSTS release mechanism
    - Enable CI/CD scenarios
    - Automated from end-to-end
    - Can be run on a cron job daily and remain immutable
        - Builds/Deployments do not overwrite each other

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

## The Solution - immutable deployments

Each deployment in the system is immutable. It contains all the important code, configuration and settings. Importantly it contains both the model training code and the scoring code. 

It's important to note that the type of model we're deploying needs to be updated regularly with the latest data. This deployment system is not for data scientist / engineer inner loop iterative development... e.g. modify code, run, get score, improve code etc. This model is for production operationalisation of a model -> training -> scoring pipeline.
 This pipeline is not just for CI/CD but also for usage with a cron job - repeating each day as new data is made available from the ETL process. 

### Model training job

The model training process runs as a Kubernetes job. It takes a range of environment variables pass in via VSTS -> Helm Chart -> Kubernetes environment variable -> container -> Python script. These variables are things like source data location, target data location, access keys etc. 

The model will produce the trained model and other outputs and save them to a shared location based on the values passed in via the environment variables. 

In our system the path was based on the VSTS build number. 

### Scoring site

The other portion of the system is the scoring site which exposes an API endpoint that can be used to pass in data and return a scoring result. 

Again, this site takes environment variables including the shared model output path. 

### Why deploy them like this

There are a range of reasons. When the scoring site is coupled to a model such as this forming a coupled, immutable deployment you get a range of things that would normally be reserved for regular software deployments. 

- Have a number of model/scoring pairs deployed at a time
- Ability for [blue/green](https://martinfowler.com/bliki/BlueGreenDeployment.html) deployments
- Traffic splits, A/B testing
- Roll forward and back deployments
    - Including re-build and re-deploy after time (years later)
- CI/CD deployments, including developer test areas and similar concepts
- Unit and integration testing across the entire deployment
- Simplified model to scoring api syncronisation (they often have coupled dependencies)
- Code and model provenance
    - Model and scoring site are linked to the people, pull requests, stores, tests and tasks that went in to making the deployment
- Probably other cool stuff :)

## Ability to Cron the build 

*Why not just store all the configs in source control?*

In our system there is a nightly ETL process that exports data from the production system ready for training with the model. 

This systems allows a cron job to be configured to kick off new builds daily. The system can then use release management to migrate traffic to the newly built model once it's passed any testing or other validation work. 

Parameterising via the build and applying those parameters to build artifacts allows for this daily build scenario. 

It also allows for the CI/CD scenario. 

## Synchonisation 

The model could take some time to compute so during deployment there needs to be a synconisation step before the scoring pods come up to allow traffic to be directed to them. 

Synchronisation is achieved by using a Kubernetes [init container](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/) which holds off the initilisation process until the model is read for use. More on this below. 

The next section will guide you through how to stand up a similar system. 

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

# Training and Deploying Model

## The Model Training Job

Our statement at the beginning of the project was to set up a machine learning delivery capability via DevOps based practices. 

The practical aim of the project is to build *a* model through training and delivering to a scoring system - the model itself is not all that important... i.e. this process could be used with any training system based around any technology (thank you containers!). 

### Input Data
The model in our scenario was a collaborative filtering model to assist with recommendations. It takes data that has been extracted from the production databases. The ETL is orchestrated by [Azure Data Factory](https://azure.microsoft.com/en-us/services/data-factory/) and saves data to an [Azure Blob Storage](https://azure.microsoft.com/en-gb/services/storage/blobs/) account in CSV format under a convention based folder structure. This section is out of scope for this document. 

The input locations are passed in to the containers as environment variables. 

The actual model type is not important - the model in this sample code simply has a delay of 15 seconds before writing out a sample model file. 

### Parameters
The model training container takes a series of parameters for the source data location as well as the output location. These parameters are passed in to the model by the build as environment variables to the Kubernetes job. The model output location is based on the build number of the VSTS build. The other parameters are generated and passed in as build variables.

This parameterisation is used heavily in the system. To help make parameterisation simpler we've opted to use [Helm Charts](https://github.com/kubernetes/helm) to make packages which form the system's deployments. The build system prepares the Helm Charts and deploys them to the cluster. 

### Set-up the Environment
Before the model can be trained the environment needs some set-up. In this system the model is output to an Azure File share - which is stored in blob storage. You'll need to create a PVC (PersistentVolumeClaim) as somewhere to save the model. 

The output path is taken in as an environment variable MODELFOLDER. This is passed through the helm chart to the kube yaml file which is applied to the cluster. This folder path is parameterised based on the build number, so each build will output to a different folder. 

By having these variables passed in as environment variables as opposed to something like config maps or similar the deployment is immutable, the settings are always locked once deployed. Importantly the deployment can be repeated later with the same settings from the same historical Git tag. 



## Building the Model Container
With VSTS it's super easy to build and deploy containers to Kubernetes. [This article](http://jessicadeen.com/tech/microsoft/how-to-deploy-to-kubernetes-using-helm-and-vsts/) by Jessica Deen gives a great overview of the process. We'll not repeat those steps here.

We'll be doing similar steps, with the addition that we'll be creating and updating a Helm package as part of the build that will result in a build artefact. 

**Note** Make sure to set your image name in both the build and push stages to `sampletrainer:$(Build.BuildNumber)`

### Parameteriseing the Deployment 

The model takes a range of parameters - things like where to source the training data from as well as where to save the output. All these parameters are "baked in" to the output build - keeping in line with the immutable deployment requirement. 

The values are placed in to the Helm Chart's values.yaml file. It is possible to pass in values to Helm Charts during publication using `--set` but that would mean an outside config requirement during publication. 

### Variable Groups

The values are passed in to the build using [Variable Groups](https://docs.microsoft.com/en-us/vsts/build-release/concepts/library/variable-groups?view=vsts). These allow you to create centrally managed variables for builds across your VSTS collection. These variables can be adjusted at build time. This allows users of the system to fire off parameterised builds without having to know "how" to build and deploy an instance of the system to the cluster. 

### Processing the variables

To help parameterise the deployment (with the environment variables) we're using [Helm Charts](https://github.com/kubernetes/helm). Helm Charts provide great flexability at multiple points along the development workflow. The large potion of the configuration can be performed as part of the template by the developer - then checked in to source control. This work is performed in the `templates` director. 

The only section the build needs to worry about is the `values.yaml` file which is passed in to Helm during deployment.  


The build will modify this `values.yaml` file and package it with the rest of the chart as a build artifact.  This chart contains all the environment variables the app needs to operate. It's all baked in to the chart artifact so it can be re-deployed at a later time, and later on operations can go back and see what parameters were used when the system was deployed.  

The template Helm Chart (under Source\helm\modelsystem) looks like this:

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

We need a way to modify that to add in some build environment variables, including the values that were passed in to the build via VSTS variables. 

### Yaml Writer

To update an existing yaml file or to create a new one from VSTS build arguments you can use the VSTS. Deploy the extension by following the instructions [here](https://marketplace.visualstudio.com/items?itemName=jakkaj.vsts-yaml-writer). Also check out the [YamlWriter GitHub Repository](https://github.com/jakkaj/yamlw_vststask).

In your build, add the YamlWriter as a new build task and set the following parameters: 

File: `Source/helm/modelsystem/values.yaml`. 

Our Parameters look as following - although yours will differ!

```
build.number='$(Build.BuildNumber)',scoringimage.repository='<your acr>/samplescorer',scoringimage.tag='$(Build.BuildNumber)',image.repository='<your acr>/sampletrainer',image.tag='$(Build.BuildNumber)',outputs.modelfolder='/mnt/azure/$(Build.BuildNumber)'
```

Make sure you replace `<your acr>` with your real registry names. 

This task will open `values.yaml` and add/update values according to the parameters passed in. 

When running the build the output will look something like this

```
2018-05-18T03:41:45.6562552Z ##[section]Starting: YamlWriter 
2018-05-18T03:41:45.6632990Z ==============================================================================
2018-05-18T03:41:45.6645860Z Task         : Yaml Writer
2018-05-18T03:41:45.6659314Z Description  : Feed in parameters to write out yaml to new or existing files
2018-05-18T03:41:45.6674165Z Version      : 0.18.0
2018-05-18T03:41:45.6688693Z Author       : Jordan Knight
2018-05-18T03:41:45.6704359Z Help         : Pass through build params and other interesting things by using a comma separated list of name value pairs. Supports deep creation - e.g. something.somethingelse=10,something.somethingelseagain='hi'. New files will be created, and existing files updated. 
2018-05-18T03:41:45.6721664Z ==============================================================================
2018-05-18T03:41:46.0603680Z File: /opt/vsts/work/1/s/Source/helm/modelsystem/values.yaml (exists: true)
2018-05-18T03:41:46.0622913Z Settings: image.repository='<youwish>/Documentation',image.tag='115',outputs.modelfolder='/mnt/azure/115',env.BLOB_STORAGE_ACCOUNT='<youwish>',env.BLOB_STORAGE_KEY='<youwish>', env.BLOB_STORAGE_CONTAINER='<youwish>',env.BLOB_STORAGE_CSV_FOLDER='"2018\/05\/08"',env.TENANTID='<youwish>'
2018-05-18T03:41:46.0640773Z Dry run: false
2018-05-18T03:41:46.0709407Z Writing file: /opt/vsts/work/1/s/Source/helm/modelsystem/values.yaml
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

This process loaded the `values.yaml` file, modified and saved it back. Then the build process then archives the Helm Chart directory and saves it as a build artefact. 

- Create a Archive task and set Root folder to `Source/helm/modelsystem` the archive type to tar and gz and archive output `$(Build.ArtifactStagingDirectory)/$(Build.BuildId).tar.gz`
- Create a Publish Artifact task to prep the chart for release  (Path to publish: `$(Build.ArtifactStagingDirectory)/$(Build.BuildId).tar.gz`).

The next step is to test the Helm Chart works before setting up the scoring side of the build. 

# Running the Training Job in Kubernetes

## Prep The Cluster

The cluster will need some preparation before the workloads can run - in this case there needs to be a shared location to save the trained models to. 

### Add the Persistent Volume Claim (PVC)

In Azure we add the PVC as an Azure File based PVC, which links to [Azure Files](https://docs.microsoft.com/en-us/azure/storage/files/storage-files-introduction) over the SMB protocol. This location is accessible outside the cluster and can be used between nodes. 

From the `Source\kube` sub-folder run:

```
kubectl apply -f pvc_azure.yml
```

Or if you're running locally in something like Minikube run the following to set up a local PVC that will act as a stand in for Azure Files during your development. 

```
kubectl apply -f pvc_minikube.yml
```

You can of course use any PVC type you'd like as long as they are accessible across nodes and pods. 

**Note:** This step was not performed as part of the build process. You could automate this, but in our case it was just as easy to apply it as it only has to be done once for the cluster (per namespace). 

## Test the Helm Chart

Before we automate the Helm Chart deployment it's a good idea to try it out. Next step is to pull the chart and manually deploy it to do the cluster. 

Navigate to the completed build in VSTS and download the Helm Chat artifact. Extract zip, and the Helm Chart will be the tar.gz inside. 

### Install Helm 

This article will not full go over Helm, Helm Charts and other set-up requirements. Suffice it to say you need the Helm CLI client installed on your machine and Tiller installed in the cluster. 

Check out the [Helm Installation Instructions](https://docs.helm.sh/using_helm/) to get started. 

### Download the Helm Chart locally

In VSTS, grab the asset .zip file from the latest successful build. Expand it (and expand the internal Helm Chart so you can see it). 

If you open the chart folder, check out `values.yaml` you should see the updated parameters including the correct build number and container names. 

In this case to test you can change the image name to `jakkaj/sampletrainer` and the tag to `dev`.

Switch to the Helm Chart location and run:

```
helm install . 
kubectl get jobs
kubectl describe job <jobname>
```
Look for things like:

    Pods Statuses:  0 Running / 1 Succeeded / 0 Failed`

and

    Type    Reason            Age   From            Message
    ----    ------            ----  ----            -------
    Normal  SuccessfulCreate  2m    job-controller  Created pod: modelsystem-122-stnmn

That means the job is running!

The next stage is to prepare the scoring side of the site. 

# Building and Deploying the Scoring Site/API

The scoring site and the model are paired from build through to deployment and operation - the model is trained by the job at the same time as the scoring site is deployed. A scoring site always has the same training model underneath. Only when the model is ready (trained, which can take quite some time) will the scoring site pods be initialised and ready to take requests. 

Scoring sites never use any other model, and as such we can use concepts like blue/green deployments, traffic splits and other intelligent routing capabilities in the cluster. We can manage endpoints as if they represent a single model version - meaning we can roll forward and back just by changing the labels that the in cluster routers look for. 

It's all very flexible. 

## Build the Scoring Container

Add container build and push steps like before for `Source/scoring/site/Dockerfile`.

For this sample call the container `samplescorer:$(Build.BuildNumber)`.  

## Wait for Training to Complete    

As this process is an immutable atomic operation that includes the actual training of the model as well as the scoring site deployment - the scoring site will most likely be deployed long before the trained model is ready. This means we should hold off access to the scoring site until it's to serve with the new model. 

To achieve this we used the Kubernetes [Init Containers](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/) feature. These containers run and the other regular pods will not come up until the init pods successfully exit. If they do not succeed or timeout, the pod may be killed. 

### The "Waiter" Container

Under `Source\scoring\init` there is a bash script and Docker file that will build a container that will "wait" for `$MODELFOLDER/complete.txt` to be written. Model folder is passed in from the cluster via environment variables from the Helm Chart as before. Because the paths are the same from model to scoring side and the data location is shared via a cluster PVC a basic file watcher can do the job here.

Once the file is found, the script exist with code 0. 

**Note:** There is a line in the script that has been commented out for next time - it's a way to log the trained model score to prometheus... that's a story for another day.

### Making the Scoring Pod Wait

Running the init container is achieved by adding an `initContainers` section to the pod spec for the deployment in the Helm Chart. This can be seen in `Source\helm\modelsystem\templates\scoring_deployment.yaml`

```yaml
initContainers:
      - name: waiter-container
        image: jakkaj/modelwaiter:dev
        ...
```

With this in place, the scoring pod will wait until the file (complete.txt) is found in the correct path (as supplied by the `MODELFOLDER` environment variable). 

Run the build and download the Helm Chart and test it locally again. Remember to replace the image names with jakkaj/sampletrainer and jakkaj/samplescorer and the tag settings to dev. 

# Deployment



# Links

## Microsoft Stuff
- [Visual Studio Team Services](https://www.visualstudio.com/team-services/)
- [Azure Data Factory](https://azure.microsoft.com/en-us/services/data-factory/)
- [Azure Blob Storage](https://azure.microsoft.com/en-gb/services/storage/blobs/)
- [Azure Files](https://docs.microsoft.com/en-us/azure/storage/files/storage-files-introduction)
- [Visual Studio Code](https://code.visualstudio.com/)
- [YamlWriter VSTS Extension](https://marketplace.visualstudio.com/items?itemName=jakkaj.vsts-yaml-writer)
    - [YamlWriter GitHub Repository](https://github.com/jakkaj/yamlw_vststask)
## Kubernetes and Container Stuff
- [Kubernetes](https://kubernetes.io/)
- [Istio](https://istio.io/docs/setup/kubernetes/quick-start.html)
- [Docker](https://docs.docker.com/install/)
- [Minikube](https://kubernetes.io/docs/getting-started-guides/minikube/)
- [Init Containers](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/)
- [Helm Installation Instructions](https://docs.helm.sh/using_helm/)