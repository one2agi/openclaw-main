#!/bin/bash
# 启动可见 Chromium 浏览器（连接 Windows VcXsrv）
export DISPLAY=172.20.112.1:0
CHROME=/tmp/chrome-extract/opt/google/chrome/chrome
$CHROME --new-window "$@" --no-sandbox --disable-gpu --disable-software-rasterizer
