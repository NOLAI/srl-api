FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y cron curl
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt
RUN python -m spacy download en_core_web_md
RUN python -m spacy download nl_core_news_md
COPY crontab /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab && crontab /etc/cron.d/crontab
COPY entrypoint.sh entrypoint.sh
RUN chmod +x entrypoint.sh
COPY app /app/app
EXPOSE 88
ENTRYPOINT ["bash", "entrypoint.sh"]
