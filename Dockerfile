
FROM python:3.12

RUN apt-get update && apt-get install -y gcc
RUN python -m pip install --upgrade pip

WORKDIR /app

COPY ./lecture_2 ./lecture_2
COPY ./lecture_3/requirements.txt ./

RUN pip install -r requirements.txt

CMD ["fastapi", "run", "./lecture_2/hw/shop_api/main.py"]
