FROM alpine:3.20

RUN apk add --no-cache \
    rclone \
    python3 \
    py3-pip \
    py3-flask \
    py3-requests

COPY wrapper/ /app/
WORKDIR /app

VOLUME ["/logs"]
EXPOSE 8080

# Start rclone RC daemon and Flask wrapper
ENTRYPOINT ["sh", "-c", "rclone rcd --rc-addr=127.0.0.1:5572 --rc-no-auth --log-file=/logs/rclone-daemon.log --log-level=INFO & sleep 1 && python3 app.py"]
