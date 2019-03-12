FROM python:3.7-alpine3.8 as build
MAINTAINER David Chidell (dchidell@cisco.com)
COPY requirements.txt .
RUN pip install --install-option="--prefix=/install" -r requirements.txt

FROM build
COPY --from=build /install /usr/local
COPY *.py ./
COPY main.html ./
ENTRYPOINT ["gunicorn"]
CMD ["app:app","-b",":8080","-w","8"]
