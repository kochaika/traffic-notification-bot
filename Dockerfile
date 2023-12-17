FROM python:3.9
LABEL authors="Konstantin.Chaika"

RUN apt-get update  \
    && apt-get install cron vim -y  \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install virtualenv
RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH"

COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

COPY run.sh /run.sh

RUN crontab -l -u root | { cat; echo "0 9 * * * /bin/bash /run.sh"; } | crontab -u root -

COPY main.py main.py

ENTRYPOINT ["cron", "-f"]