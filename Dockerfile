FROM vmware/photon2:20180424

RUN tdnf install -y python3-3.6.5-1.ph2 python3-pip-3.6.5-1.ph2 gzip tar && pip3 install --upgrade pip setuptools

ARG IMAGE_TEMPLATE=/image-template
ARG FUNCTION_TEMPLATE=/function-template
ARG SERVERS=1
ARG FUNKY_VERSION

LABEL io.dispatchframework.imageTemplate="${IMAGE_TEMPLATE}" \
      io.dispatchframework.functionTemplate="${FUNCTION_TEMPLATE}"

COPY image-template ${IMAGE_TEMPLATE}/
COPY function-template ${FUNCTION_TEMPLATE}/

COPY validator /validator/

COPY function-server /function-server/
RUN pip install -r /function-server/requirements.txt

## Set WORKDIR, PORT and SERVER_CMD, expose $PORT, cd to $WORKDIR

ENV WORKDIR=/function PORT=8080 SERVERS=${SERVERS} TIMEOUT=300

EXPOSE ${PORT}
WORKDIR ${WORKDIR}

RUN curl -L https://github.com/dispatchframework/funky/releases/download/${FUNKY_VERSION}/funky${FUNKY_VERSION}.linux-amd64.tgz -o funky${FUNKY_VERSION}.linux-amd64.tgz
RUN tar -xzf funky${FUNKY_VERSION}.linux-amd64.tgz

CMD SERVER_CMD="python3 /function-server/main.py $(cat /tmp/handler)" ./funky
