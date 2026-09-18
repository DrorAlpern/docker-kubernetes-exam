# Crypto Price Tracker

This is the Docker and Kubernetes exam application from the course starter
repository, branch `workshop/k8s-docker-exam`, under `exam-code/docker`.
It is a separate exercise from the AWS inventory project, but both live on the
same Linux development machine.

The browser talks to the Flask frontend (`web`, port 5002). The frontend calls
the Flask backend (`backend-service`, port 5001). The backend fetches Bitcoin
and XRP prices from CoinGecko and writes each result to MySQL (`mysqldb`, port
3306). A successful response includes `"saved": true` for both coins.

## Run with Docker Compose

From this directory on the Linux machine:

```bash
cp .env.example .env
sudo docker compose up -d --build
sudo docker compose ps
curl -fsS http://127.0.0.1:5002/fetch_price
```

Open `http://127.0.0.1:5002` on the Linux machine and select **Fetch prices**.
From the Windows workstation, forward the private port with
`ssh -L 15002:127.0.0.1:5002 devops-lab`, then open
`http://127.0.0.1:15002`. The frontend is intentionally bound to localhost on
the Linux host. The backend and database are reachable only on the custom
Compose network. The `mysql-data` volume retains records when containers stop.

The exam's `123456` password is a local demonstration value in `.env.example`.
The working `.env` file is ignored by Git; use a different private value for
any non-lab environment. Stop Compose before running the Kubernetes lab on a
small machine: `sudo docker compose stop` keeps the database volume.

## Run on the local Kubernetes cluster

The commands below use the existing `devops-local` kind cluster on the same
Linux machine. They create only the `crypto-exam` namespace and its resources.
First build the two images with Compose as shown above, then stop Compose.

```bash
export KUBECONFIG="$HOME/.config/devops-kubernetes/kubeconfig"
export PATH="$HOME/devops-final-exam/.tools/bin:$PATH"
sudo "$HOME/devops-final-exam/.tools/bin/kind" load docker-image \
  --name devops-local \
  droralpern/crypto-frontend:1.0.0 droralpern/crypto-backend:1.0.0
kubectl apply -f k8s/namespace.yaml
kubectl -n crypto-exam create secret generic mysql-credentials \
  --from-env-file=.env --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -k k8s
kubectl -n crypto-exam rollout status deployment/mysqldb
kubectl -n crypto-exam rollout status deployment/backend-service
kubectl -n crypto-exam rollout status deployment/web
kubectl -n crypto-exam get pods
kubectl -n crypto-exam get svc
kubectl -n crypto-exam port-forward service/web 5002:5002
```

The frontend Service is a `LoadBalancer` as required by the exam. Kind has no
cloud load balancer, so its external IP remains pending; the localhost port
forward is used for the browser check. The backend and MySQL Services are
internal `ClusterIP` Services. MySQL stores its data on a 1 GiB persistent
volume claim.

The MySQL 5.7 startup wrapper lowers the open-file limit inherited from
kind/containerd before calling the image's original entrypoint. Without this
small adjustment, the local cluster exhausted MySQL's memory during its
configuration check. Docker Compose does not need the wrapper.

## Helm bonus

The optional chart is at [`helm/crypto-exam`](helm/crypto-exam/README.md). It
has configurable images, replica counts, ports, storage, and database Secret
references. Install it in a separate namespace so it does not overlap the
plain Kubernetes resources. The chart was installed locally, and its
frontend replica count was changed from two to one and restored to two.

## Evidence and limits

| File | What it shows |
| --- | --- |
| [`evidence/docker-frontend.png`](evidence/docker-frontend.png) | Live Docker browser result with two saved prices |
| [`evidence/kubernetes-frontend.png`](evidence/kubernetes-frontend.png) | Live Kubernetes browser result through a localhost port forward |
| [`evidence/kubernetes-status.png`](evidence/kubernetes-status.png) | Image rendered from the captured pod and Service command output |
| [`evidence/kubernetes-status.txt`](evidence/kubernetes-status.txt) | Original `kubectl` output, including the bound database volume |
| [`evidence/helm-status.txt`](evidence/helm-status.txt) | Helm release and workload status |

On 18 September 2026, Docker Compose returned Bitcoin and XRP with
`"saved": true`, and direct MySQL queries found both rows. The local Kubernetes
deployment had two ready frontend pods, two ready backend pods, one ready
MySQL pod, and the same successful database check. The Helm release also
passed a two-price and database check. These results verify the local lab;
they do not claim deployment to a separate course cluster. The optional Istio
Ingress task has not been implemented or tested.

The course starter's API request used `xrp` as a CoinGecko ID, which returned
only Bitcoin during testing. The backend now requests `ripple` and labels it
XRP in the application. The frontend and backend also have small health
endpoints and bounded HTTP requests so failures are visible rather than
hanging indefinitely.
