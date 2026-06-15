ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

RUN apk add --no-cache python3
RUN apk add --no-cache py-pip
RUN pip install --break-system-packages requests PySocks
WORKDIR /data

# Copy data for add-on
COPY run.sh /
COPY precipitation.py /
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
