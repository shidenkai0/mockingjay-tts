FROM runpod/pytorch:2.1.1-py3.10-cuda12.1.1-devel-ubuntu22.04

SHELL ["/bin/bash", "-c"]

WORKDIR /

# Install Python dependencies (Worker Template)
COPY requirements.txt /requirements.txt
RUN pip install --upgrade pip && \
    pip install -r /requirements.txt && \
    rm /requirements.txt

ADD src /src

RUN python src/load_model.py

CMD [ "python", "-u", "/src/handler.py" ]
