#!/bin/bash

# 脚本保存路径
SCRIPT_PATH="$HOME/t3rn-bot.sh"

# 定义文件名称
PYTHON_FILE="keys_and_addresses.py"
DATA_BRIDGE_FILE="data_bridge.py"
BOT_FILE="bot.py"
VENV_DIR="t3rn-env"  # 虚拟环境目录

# 主菜单函数
function main_menu() {
    while true; do
        clear
        echo "脚本由大赌社区哈哈哈哈编写，推特 @ferdie_jhovie，免费开源，请勿相信收费"
        echo "如有问题，可联系推特，仅此只有一个号"
        echo "================================================================"
        echo "退出脚本，请按键盘 ctrl + C 退出即可"
        echo "请选择要执行的操作:"
        echo "1. 执行t3rn跨链脚本"
        echo "2. 退出"
        
        read -p "请输入选项 (1/2): " option
        case $option in
            1)
                execute_cross_chain_script
                ;;
            2)
                echo "退出脚本。"
                exit 0
                ;;
            *)
                echo "无效选项，请重新选择。"
                sleep 2
                ;;
        esac
    done
}

# 执行跨链脚本
function execute_cross_chain_script() {
    # 检查是否为root用户
    if [ "$EUID" -ne 0 ]; then 
        echo "请使用 sudo 运行此脚本"
        exit 1
    fi

    # 检查是否安装了 python3-pip 和 python3-venv
    if ! command -v pip3 &> /dev/null; then
        echo "pip 未安装，正在安装 python3-pip..."
        sudo apt update
        sudo apt install -y python3-pip
    fi

    if ! command -v python3 -m venv &> /dev/null; then
        echo "python3-venv 未安装，正在安装 python3-venv..."
        sudo apt update
        sudo apt install -y python3-venv
    fi

    # 创建虚拟环境并激活
    echo "正在创建虚拟环境..."

    source "$VENV_DIR/bin/activate"

    # 升级 pip
    echo "正在升级 pip..."
    pip install --upgrade pip

    # 安装依赖
    echo "正在安装依赖 web3 和 colorama..."
    pip install web3 colorama



    # 提醒用户运行 bot.py
    echo "配置完成，正在通过 screen 运行 bot.py..."

    # 使用 screen 后台运行 bot.py
#    screen -dmS t3rn-bot python3 $BOT_FILE

    # 输出信息
    echo "bot.py 已在后台运行，您可以通过 'screen -r t3rn-bot' 查看运行日志。"

    # 提示用户按任意键返回主菜单
    read -n 1 -s -r -p "按任意键返回主菜单..."
}

# 启动主菜单
main_menu
