FROM ubuntu:22.04 as base

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV TZ=Asia/Shanghai

RUN apt update && \
	apt install -y tzdata || true && apt install -y tzdata && \
	apt install -y python3 || true && apt install -y python3 && \
	apt install -y python3-pip || true && apt install -y python3-pip && \
	python3 -m pip install sqlalchemy pymysql requests bs4
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

CMD ["bash"]

#git clone git@github.com:KenMET/Python-Prj.git
#docker run -itd -v /data:/data --name ubuntu ubuntu:22.04 /usr/bin/init
#docker exec -it ubuntu /bin/bash
#docker stop ubuntu; docker rm ubuntu
#docker build -t spider:latest .
