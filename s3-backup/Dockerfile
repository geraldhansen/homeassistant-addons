ARG BUILD_FROM
FROM ${BUILD_FROM}

COPY run.sh /
#RUN chmod a+x /run.sh

# add aws-cli and deps
RUN apk add -v --update --no-cache \
        python3 \
        py3-pip \
        groff \
        less \
        jq \
        && pip3 install flask gunicorn
RUN pip3 install --no-cache-dir awscli
RUN aws --version   # Just to make sure its installed alright

# Copy the Flask app into the container
COPY s3-backup /s3-backup

EXPOSE 8099
#CMD ["gunicorn", "--bind", "0.0.0.0:8099", "s3-backup.s3-backup:app"]

CMD [ "/run.sh" ]  
# Specify the default command to run the Flask app
#CMD ["python3", "/app/app.py"]
