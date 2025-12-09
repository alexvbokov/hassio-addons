ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

RUN apk add --no-cache python3
RUN apk add --no-cache py-pip
RUN pip install --break-system-packages requests pillow numpy
WORKDIR /data

# Copy data for add-on
COPY run.sh /
COPY camera_light_sensor.py /
COPY config.json /
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
