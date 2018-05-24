# Model Pipeline Release

*Please read [the first section](readme.md) of this article before continuing here.*

The build is working. It's:

- Building the training and scoring docker images
- Pushing those images to a container registry
- Replace values in the Helm Chart (using Yaml Writer VSTS task)
- Tar the chart and save it as a build artefact. 