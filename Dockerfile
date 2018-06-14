FROM vmware/photon2:20180424

RUN tdnf install -y python3-3.6.5-1.ph2 python3-pip-3.6.5-1.ph2 && pip3 install --upgrade pip setuptools

ARG IMAGE_TEMPLATE=/image-template
ARG FUNCTION_TEMPLATE=/function-template

LABEL io.dispatchframework.imageTemplate="${IMAGE_TEMPLATE}" \
      io.dispatchframework.functionTemplate="${FUNCTION_TEMPLATE}"

COPY image-template ${IMAGE_TEMPLATE}/
COPY function-template ${FUNCTION_TEMPLATE}/

COPY validator /validator/

COPY function-server /function-server/
RUN pip install -r /function-server/requirements.txt

## Set WORKDIR and PORT, expose $PORT, cd to $WORKDIR

ENV WORKDIR=/function PORT=8080

EXPOSE ${PORT}
WORKDIR ${WORKDIR}

# OpenFaaS readiness check depends on this file
RUN touch /tmp/.lock

CMD python3 /function-server/main.py $(cat /tmp/handler)
