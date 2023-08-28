# Basic Dockerfile for testing the SSH service.
FROM debian:latest

ARG PORT=2222
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        openssh-server openssh-client
RUN echo "Port ${PORT}" > /etc/ssh/sshd_config.d/local.conf \
    && echo "PermitRootLogin prohibit-password" >> /etc/ssh/sshd_config.d/local.conf \
    && ssh-keygen -t rsa -N '' -f /root/.ssh/id_rsa \
    && cat /root/.ssh/id_rsa.pub > /root/.ssh/authorized_keys

ENV TIMEOUT=infinity
CMD ["/bin/bash", "-eux", "-c", "trap : TERM INT; service ssh start && sleep ${TIMEOUT} & wait"]
