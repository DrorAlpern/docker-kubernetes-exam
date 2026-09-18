# Docker and Kubernetes Exam

This branch contains my Docker and Kubernetes exam work, based on the course
starter branch `workshop/k8s-docker-exam`.

The solution, run instructions, and test evidence are in
[`exam-code/docker`](exam-code/docker/README.md). The application fetches
Bitcoin and XRP prices through a Flask frontend and backend, then stores them
in MySQL. It runs with Docker Compose or Kubernetes; an optional Helm chart is
included.

The documented checks were performed on my local Linux lab. No deployment to
a separate course cluster is claimed.
