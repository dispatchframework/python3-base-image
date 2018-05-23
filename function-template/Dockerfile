ARG IMAGE
FROM ${IMAGE}

ARG HANDLER
ENV HANDLER=$HANDLER

WORKDIR ${WORKDIR}

COPY . .

# Create handler file if passed in otherwise assume default handler
RUN echo -n ${HANDLER} > /tmp/handler
RUN [ -z "${HANDLER}" ] && \
    [ $(ls *.py | wc -l) -eq "1" ] && \
    filename=$(ls *.py) && \
    filename="${filename%.*}" && \
    { echo -n $filename; echo -n ".handle"; } > /tmp/handler || :
