ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

RUN apk add --no-cache tzdata jq openssh sshpass
# RUN apk add --no-cache python3
# RUN apk add --no-cache py-pip
# RUN pip install requests 
WORKDIR /data

# Copy data for add-on
COPY run.sh /
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
