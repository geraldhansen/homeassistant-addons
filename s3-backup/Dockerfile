ARG BUILD_FROM
FROM $BUILD_FROM

RUN apk add --no-cache python3 py3-pip && \
    python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir flask boto3 requests

COPY rootfs /
RUN chmod a+x /run.sh

CMD ["/run.sh"]
