FROM python:3.10

ENV APP_HOME /app
WORKDIR $APP_HOME

COPY . .

RUN pip install -r requirements.txt

EXPOSE 8000

CMD alembic upgrade head && python3 main.py
