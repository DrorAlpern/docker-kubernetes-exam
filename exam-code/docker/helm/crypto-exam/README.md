# Crypto Exam Helm Chart

This optional chart deploys the cryptocurrency price application as three Kubernetes services: `web`, `backend-service`, and `mysqldb`. The default configuration runs two frontend pods, two backend pods, and one MySQL pod with a 1 GiB persistent volume claim.

The chart expects a Secret named `mysql-credentials` with a `MYSQL_ROOT_PASSWORD` key in the target namespace. From the `exam-code/docker` directory, create it from an ignored `.env` file before installation:

```bash
cp .env.example .env
kubectl create namespace crypto-helm --dry-run=client -o yaml | kubectl apply -f -
kubectl -n crypto-helm create secret generic mysql-credentials \
  --from-env-file=.env --dry-run=client -o yaml | kubectl apply -f -
helm upgrade --install crypto-exam ./helm/crypto-exam \
  --namespace crypto-helm --wait
```

Change replica counts, image tags, service types and ports, storage size, or Secret references in `values.yaml` or with `--set`. The default frontend Service is a `LoadBalancer`; on a local cluster, use a supported load-balancer integration or access it with `kubectl -n crypto-helm port-forward service/web 5002:5002`. The separate namespace keeps this optional release independent from the plain Kubernetes manifests.

```bash
kubectl -n crypto-helm get deployments,pods,services,pvc
kubectl -n crypto-helm port-forward service/web 5002:5002
```

Visit `http://localhost:5002` after all pods are ready. The frontend calls `backend-service` inside the cluster, and the backend connects to `mysqldb` using the existing Secret.

The MySQL container lowers its inherited open-file limit before running the official entrypoint. This is needed in the local kind/containerd lab because the unusually high inherited limit makes MySQL 5.7 exhaust its memory during startup.
