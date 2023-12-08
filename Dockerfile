FROM python:3.10
WORKDIR /app
ENV LC_ALL=C.UTF-8
COPY . .
RUN pwd && pip install pipenv && pipenv --python 3.10 && pipenv install
CMD ["pipenv", "run", "start"]