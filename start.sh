#!/bin/bash

# 获取并进入脚本所在的目录，确保路径正确
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$DIR"

# 定义变量
APP_COMMAND="venv/bin/python app.py"
LOG_FILE="app.log"
PID_FILE="app.pid"

# 停止服务的函数
stop_server() {
    if [ -f "$PID_FILE" ]; then
        echo "正在根据 PID 文件停止服务 (PID: $(cat $PID_FILE))..."
        kill $(cat "$PID_FILE")
        rm "$PID_FILE"
    else
        echo "未找到 PID 文件，尝试通过进程名查找..."
    fi
    # 无论如何都尝试用 pkill 作为后备，以防 PID 文件丢失或进程脱离控制
    pkill -f "$APP_COMMAND"
    echo "停止操作完成。"
    sleep 1
}

# 后台启动服务的函数
start_background() {
    stop_server
    echo "正在后台启动服务..."
    # 使用 nohup 启动应用，并将标准输出和错误都重定向到日志文件
    nohup $APP_COMMAND > "$LOG_FILE" 2>&1 &
    # 获取最后一个后台进程的 PID 并写入文件
    echo $! > "$PID_FILE"
    echo "服务已在后台启动。PID: $(cat $PID_FILE)。日志文件: $LOG_FILE"
}

# 前台启动服务的函数
start_foreground() {
    stop_server
    echo "正在前台启动服务 (按 Ctrl+C 停止)..."
    # exec 会让 app.py 进程替换当前的 shell 进程
    # 这样可以更好地处理 Ctrl+C 等信号
    exec $APP_COMMAND
}

# --- 主逻辑 ---
# 检查传入的第一个参数
if [ "$1" == "log" ]; then
    start_foreground
elif [ "$1" == "restart" ]; then
    start_background
elif [ "$1" == "stop" ]; then
    stop_server
else
    # 默认行为（无参数）也是重启并在后台运行
    start_background
fi
