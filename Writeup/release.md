# Model Pipeline Release

*Please read [the first section](readme.md) of this article before continuing here.*

The build is working. It's:

- Building the training and scoring docker images
- Pushing those images to a container registry
- Replace values in the Helm Chart (using Yaml Writer VSTS task)
- Tar the chart and save it as a build artefact. 


The release will be in two phases. The first phase will deploy to the cluster. This deployment will be standalone - it will not replace other deployments in the cluster.

The second phase will update the cluster routing to point to the new scoring endpoint. This way any deployment in the cluster can be promoted to be the main/production endpoint. Or canary, or what ever else.  

Now the release needs to push the chart to the cluster. This process involves:

- Grab the build artefact
- Install Helm
- Configure the cluster config and authentication
- Install the Helm Chart


