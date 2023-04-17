FROM nginx:latest
RUN apt-get update && apt-get install -y --no-install-recommends linklint curl
# Our ngxinx config overrides the default listening port.
ARG NGINX_PORT=81
ENV NGINX_PORT=${NGINX_PORT}
EXPOSE ${NGINX_PORT}
