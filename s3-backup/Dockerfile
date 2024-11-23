ARG BUILD_FROM
FROM ${BUILD_FROM}

COPY run.sh /
RUN chmod a+x /run.sh

# add aws-cli and deps
RUN apk add -v --update --no-cache \
        python3 \
        py3-pip \
        groff \
        less \
        jq
RUN pip3 install --no-cache-dir awscli
RUN aws --version   # Just to make sure its installed alright
    
#CMD [ "/run.sh" ]  
# Specify the default command to run the Flask app
CMD ["python3", "/app/app.py"]
