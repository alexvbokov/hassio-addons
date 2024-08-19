ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

RUN apk add --no-cache python3
RUN apk add --no-cache py-pip
RUN pip install --break-system-packages requests 
WORKDIR /data

# Copy data for add-on
COPY run.sh /
COPY narodmon.py /
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
