FROM python:3.10
WORKDIR /app
ENV LC_ALL=C.UTF-8
RUN pip install pipenv && pipenv --python 3.10
COPY Pipfile /app/
COPY .env /app/
RUN pipenv install
COPY slack_translator_bot/ /app/slack_translator_bot/
CMD ["pipenv", "run", "start"]