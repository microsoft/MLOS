# Basic Dockerfile for testing the SSH service.
FROM debian:latest

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        openssh-server openssh-client \
        sudo
ARG PORT=2254
EXPOSE ${PORT}
RUN echo "Port ${PORT}" > /etc/ssh/sshd_config.d/local.conf \
    && echo "PermitRootLogin prohibit-password" >> /etc/ssh/sshd_config.d/local.conf \
    && ssh-keygen -t rsa -N '' -f /root/.ssh/id_rsa \
    && cat /root/.ssh/id_rsa.pub > /root/.ssh/authorized_keys

ENV TIMEOUT=180
# NOTE: The "-n" is important in the call to "wait" so that an exit failure can be detected.
CMD ["/bin/bash", "-eux", "-c", "trap : TERM INT; service ssh start && sleep ${TIMEOUT:-180} & wait -n"]
