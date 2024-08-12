FROM ubuntu:22.04 as base

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt update && \
	apt install -y tzdata || true && apt install -y tzdata && \
	apt install -y python3 || true && apt install -y python3 && \
	apt install -y python3-pip || true && apt install -y python3-pip && \
	python3 -m pip install sqlalchemy pymysql requests bs4 cryptography && \
	python3 -m pip install sqlalchemy pymysql requests bs4 cryptography

CMD ["bash"]

#git clone git@github.com:KenMET/Python-Prj.git
#docker run -itd -v /data:/data --name ubuntu ubuntu:22.04 /usr/bin/init
#docker exec -it ubuntu /bin/bash
#docker stop ubuntu; docker rm ubuntu
#docker build -t spider:latest .

#nvidia-docker run -itd \
#    --name spider \
#    -e PUID=1000 \
#    -e PGID=1000 \
#    -e LANG=C.UTF-8 \
#    -e LC_ALL=C.UTF-8 \
#    -e PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
#    -e SANITY_ENABLE=TRUE \
#    -e CAT_FETCH_ENABLE=TRUE \
#    -e DOG_FETCH_ENABLE=TRUE \
#    -e HOSTNAME=192.168.10.228 \
#    -e PORT=8206 \
#    -e USERNAME=root \
#    -e PASSWORD=XXXXXXXXXXXXXXX \
#    -v /home/kanos/workspace/data/code/Python-Prj:/base \
#    --restart unless-stopped \
#    spider \
#    bash -c "service cron start;tail -f /dev/null"
