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
    - Clearly defined

- Service mesh
    - Deployment versioning to allow for Istio control
    - Can support intelligent routing
    - A/B splits
    - % based splits
    - Other intelligent traffic scrutiny / routing

# Getting Started

Before you start you'll need the following things installed / setup.

- A [Visual Studio Team Services](https://www.visualstudio.com/team-services/) instance. You can set one up as a free trial, or if you have an MSDN subscription you may have some licenses available.
- A [Kubernetes](https://kubernetes.io/) cluster. We used the [acs-engine yeoman generator](https://github.com/jakkaj/generator-acsengine) to set one up in Azure. 
    - Make sure you set up Kubernetes v1.9 or better so the automatic sidecar injection works with [Istio](https://istio.io/docs/setup/kubernetes/quick-start.html) (more on that later!)
- [Docker](https://docs.docker.com/install/)
- [Visual Studio Code](https://code.visualstudio.com/)


## The Model Training Job

Our statement at the beginning of the project was to set up a machine learning delivery capability via DevOps based practices. 

The practical aim of the project is to build *a* model through training and delivering to a scoring system - the model itself is not all that important... i.e. this process could be used with any training system based around any technology (thank you containers!). 

### Inputs
The model is a collaborative filtering model to assist with recommendations. It takes data that has been extracted from the production databases. The ETL is orchestrated by [Azure Data Factory](https://azure.microsoft.com/en-us/services/data-factory/) and saves data to an [Azure Blob Storage](https://azure.microsoft.com/en-gb/services/storage/blobs/) account in CSV format under a convention based folder structure. This section is out of scope for this document. 

### Parameters
The model takes a series of parameters for the source data location as well as the output location. These parameters are passed in to the model by the build as environment variables to the Kubernetes job. The model output location is based on the build number of the VSTS build. The other parameters are generated and passed in as build variables.

### The Model



## Scoring build and deployment 

## Intelligent routing



#Links

## Microsoft Stuff
- [Visual Studio Team Services](https://www.visualstudio.com/team-services/)
- [Azure Data Factory](https://azure.microsoft.com/en-us/services/data-factory/)
- [Azure Blob Storage](https://azure.microsoft.com/en-gb/services/storage/blobs/)
- [Visual Studio Code](https://code.visualstudio.com/)
## Kubernetes Stuff
- [Kubernetes](https://kubernetes.io/)
- [Istio](https://istio.io/docs/setup/kubernetes/quick-start.html)
- [Docker](https://docs.docker.com/install/)