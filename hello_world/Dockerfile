ARG BUILD_FROM
FROM $BUILD_FROM

# Copy data for add-on
COPY run.sh /
RUN chmod a+x /run.sh

RUN apk add -v --update --no-cache \
        python3 \
        py3-pip \
        groff \
        less \
        jq
RUN echo ${BUILD_FROM} > /tmp/build_from


CMD [ "/run.sh" ]