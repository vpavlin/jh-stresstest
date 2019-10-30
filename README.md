# jh-stresstest

This repository contains a basic Python script and Kubernetes manifests to automatically test JupyterHub deployment on OpenShift using Selenium.

It is mainly used to test JupyterHub in https://opendatahub.io, but can be probably reused elsewhere with minor tweaks.

## Flow

1. Login to JupyterHub as Admin
2. Create a new user
3. Impersonate that user
4. Configure spawner and spawn a server
5. Execute notebook(s)
6. Kill the server
7. Remove the user

## Deployment

```
oc apply -f openshift/jhstress.bc.yaml
```

When the build is done, deploy the Job. You will need to configure `JH_URL`, `JH_LOGIN_USER` and `JH_LOGIN_PASS`. You can also change `parallelism` and `completions` to set how many parallel users you want.

```
oc apply -f openshift/jhstress.job.yaml
```
