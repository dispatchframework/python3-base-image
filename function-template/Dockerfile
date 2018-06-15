ARG IMAGE
FROM ${IMAGE}

ARG HANDLER
ENV HANDLER=$HANDLER

WORKDIR ${WORKDIR}

COPY . .

# Create handler file if passed in otherwise assume default handler
RUN echo -n ${HANDLER} > /tmp/handler
RUN if [ -z "${HANDLER}" ]; then \
    ([ $(ls *.py | wc -l) -eq "1" ] || (echo "Exactly 1 source file needed when HANDLER is empty" >&2 && exit 1)) && \
    filename=$(ls *.py) && \
    filename="${filename%.*}" && \
    { echo -n $filename; echo -n ".handle"; } > /tmp/handler; fi

# Validate function file and given handler
WORKDIR /

RUN python3 -m validator.validator ${WORKDIR} $(cat /tmp/handler) || (echo "Invalid function file or handler" >&2 && exit 1)

WORKDIR ${WORKDIR}