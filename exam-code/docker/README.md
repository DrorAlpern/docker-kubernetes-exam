# Crypto Price Tracker

The course's Flask frontend calls a Flask backend, which fetches Bitcoin and
XRP prices and saves them in MySQL. The application returns `saved: true` for
each successful database write.

Source: the course starter's `workshop/k8s-docker-exam` branch. The backend uses
CoinGecko's `ripple` ID for XRP; the original `xrp` ID did not return that price.

## Docker Compose

Requirements: Docker Engine with Compose and internet access. From this folder:

```bash
cp .env.example .env
docker compose up -d --build
docker compose ps
curl -fsS http://127.0.0.1:5002/fetch_price
```

Use sudo for Docker commands if required by the host. Open
**http://127.0.0.1:5002** and select **Fetch prices**. Both coins should show
`Saved to database: true`.

The services are `web` on port 5002, `backend-service` on port 5001, and
`mysqldb` on port 3306. They share the `crypto-net` network. Only the frontend
port is published, on localhost. For a remote Linux host, use:

```bash
ssh -N -L 5002:127.0.0.1:5002 user@linux-host
```

The database is `mysql:5.7` with database name `crypto_db`, as specified in the
exam. The example password is the course's local-lab value, `123456`. The working
`.env` file is ignored by Git. The database volume keeps records between runs.
`docker compose stop` stops the application without deleting that volume.

## Kubernetes

Requirements: a working Kubernetes cluster, kubectl, and access to Docker Hub.
The images `droralpern/crypto-frontend:1.0.0` and
`droralpern/crypto-backend:1.0.0` are already published.

If using kind and no cluster exists, create one with
`kind create cluster --name crypto-exam`. Confirm the intended context with
`kubectl config current-context` before applying the files.

```bash
kubectl apply -f k8s/namespace.yaml
kubectl -n crypto-exam create secret generic mysql-credentials \
  --from-env-file=.env --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -k k8s
kubectl -n crypto-exam rollout status deployment/mysqldb
kubectl -n crypto-exam rollout status deployment/backend-service
kubectl -n crypto-exam rollout status deployment/web
kubectl -n crypto-exam get pods,svc
kubectl -n crypto-exam port-forward service/web 5002:5002
```

Open the same browser address. The frontend and backend each have two replicas.
The frontend Service is `LoadBalancer`; backend and MySQL are `ClusterIP`.
On kind, the external address stays pending, so the browser check uses the
port forward. MySQL has a 1 GiB PVC. Its startup wrapper lowers the inherited
open-file limit to prevent excessive memory use in kind.

## Evidence and bonus

The [evidence folder](evidence/README.md) contains the Docker and Kubernetes
browser results and captured workload status from 18 September 2026. Both
prices were fetched and confirmed in MySQL.

The [Helm chart](helm/crypto-exam/README.md) implements the optional Helm task
and was tested locally. The optional Istio task is not implemented.
