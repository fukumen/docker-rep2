# mitmproxy

HTTPのリクエストをproxy経由でデバッグするときのメモ。

結論：mitmproxyが便利です。

## CLI

ssl_verify_peerを「しない」に設定して以下のように起動するとuse_httpsが「する」でも解析できる。

```
docker run --rm -it \
  -p 8080:8080 \
  -v $(pwd):/data \
  -w /data \
  mitmproxy/mitmproxy:latest \
  /usr/local/bin/mitmproxy --mode regular -p 8080
```

## WEB

以下のように起動するとURLが表示されるのでそのURLをブラウザで開く。

```
docker run --rm -it \
  -p 8080:8080 \
  -p 8081:8081 \
  -v $(pwd):/data \
  -w /data \
  mitmproxy/mitmproxy:latest \
  /usr/local/bin/mitmweb --mode regular -p 8080 \
    --web-host 0.0.0.0
```

## TLS1

TLS1しかサポートしていないような古いクライアントを接続するにはmitmproxyの7.0.4がTLS1接続出来る最終のようなのでそれを使う。

```
docker run --rm -it \
  -p 8080:8080 \
  -v $(pwd):/data \
  -w /data \
  mitmproxy/mitmproxy:7.0.4 \
  /usr/local/bin/mitmproxy --mode regular -p 8080 \
    --set tls_version_client_min=TLS1
```
