# 导入 Web3 库
from web3 import Web3
from eth_account import Account
import time
import sys
import os
import random  # 引入随机模块
from eth_utils import remove_0x_prefix, to_hex

# 数据桥接配置
from data_bridge import data_bridge
from keys_and_addresses import private_keys, labels  # 不再读取 my_addresses
from network_config import networks

# 文本居中函数
def center_text(text):
    terminal_width = os.get_terminal_size().columns
    lines = text.splitlines()
    centered_lines = [line.center(terminal_width) for line in lines]
    return "\n".join(centered_lines)

# 清理终端函数
def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

description = """
自动桥接机器人  https://bridge.t1rn.io/
操你麻痹Rambeboy,偷私钥🐶
"""

# 每个链的颜色和符号
chain_symbols = {
    'Arbitrum Sepolia': '\033[34m',  # 蓝色
    'Blast Sepolia': '\033[91m',     # 红色    
    'Optimism Sepolia': '\033[95m',  # 紫色
    'Base Sepolia': '\033[92m',      # 绿色
}

# 颜色定义
green_color = '\033[92m'
reset_color = '\033[0m'
menu_color = '\033[95m'  # 菜单文本颜色

# 每个网络的区块浏览器URL
explorer_urls = {
    'Arbitrum Sepolia': 'https://sepolia.arbiscan.io/tx/', 
    'Blast Sepolia': 'https://testnet.blastscan.io/tx/',
    'Optimism Sepolia': 'https://sepolia-optimism.etherscan.io/tx/',
    'Base Sepolia': 'https://sepolia.basescan.org/tx/',
    'BRN': 'https://brn.explorer.caldera.xyz/tx/'
}

# 获取BRN余额的函数
def get_brn_balance(web3, my_address):
    balance = web3.eth.get_balance(my_address)
    return web3.from_wei(balance, 'ether')

# 检查链的余额函数
def check_balance(web3, my_address):
    balance = web3.eth.get_balance(my_address)
    return web3.from_wei(balance, 'ether')

# 添加新的辅助函数
def customize_bridge_data(original_data: str, new_address: str) -> str:
    """
    自定义桥接数据,将固定地址替换为发送者地址
    
    Args:
        original_data: 原始的桥接数据
        new_address: 新的目标地址(发送者地址)
    
    Returns:
        str: 修改后的桥接数据
    """
    # 移除0x前缀
    new_address = remove_0x_prefix(new_address).lower()
    
    # 原始固定地址
    fixed_address = "4f00235633a506b206d96128d9dedb3b55d11001"
    
    # 替换地址
    return original_data.lower().replace(fixed_address, new_address)

# 创建和发送交易的函数
def send_bridge_transaction(web3, account, my_address, data, network_name):
    try:
        # 使用发送者地址自定义桥接数据
        customized_data = customize_bridge_data(data, my_address)
        
        nonce = web3.eth.get_transaction_count(my_address, 'pending')
        value_in_ether = 0.4
        value_in_wei = web3.to_wei(value_in_ether, 'ether')

        gas_estimate = web3.eth.estimate_gas({
            'to': networks[network_name]['contract_address'],
            'from': my_address,
            'data': customized_data,  # 使用自定义的数据
            'value': value_in_wei
        })
        gas_limit = gas_estimate + 50000

        base_fee = web3.eth.get_block('latest')['baseFeePerGas']
        priority_fee = web3.to_wei(5, 'gwei')
        max_fee = base_fee + priority_fee

        transaction = {
            'nonce': nonce,
            'to': networks[network_name]['contract_address'],
            'value': value_in_wei,
            'gas': gas_limit,
            'maxFeePerGas': max_fee,
            'maxPriorityFeePerGas': priority_fee,
            'chainId': networks[network_name]['chain_id'],
            'data': customized_data  # 使用自定义的数据
        }

        signed_txn = web3.eth.account.sign_transaction(transaction, account.key)
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        # 获取最新余额和显示交易信息的代码保持不变
        balance = web3.eth.get_balance(my_address)
        formatted_balance = web3.from_wei(balance, 'ether')
        explorer_link = f"{explorer_urls[network_name]}{web3.to_hex(tx_hash)}"

        print(f"{green_color}📤 发送地址: {account.address}")
        print(f"⛽ 使用Gas: {tx_receipt['gasUsed']}")
        print(f"🗳️  区块号: {tx_receipt['blockNumber']}")
        print(f"💰 ETH余额: {formatted_balance} ETH")
        brn_balance = get_brn_balance(Web3(Web3.HTTPProvider('https://brn.rpc.caldera.xyz/http')), my_address)
        print(f"🔵 BRN余额: {brn_balance} BRN")
        print(f"🔗 区块浏览器链接: {explorer_link}{reset_color}")

        return web3.to_hex(tx_hash), value_in_ether

    except Exception as e:
        error_msg = str(e)
        if "insufficient funds" in error_msg.lower():
            print(f"{chain_symbols[network_name]}{network_name} 账户余额不足{reset_color}")
            return "insufficient_funds", None
        else:
            print(f"交易失败: {e}")
            return None, None

# 在特定网络上处理交易的函数
def process_network_transactions(network_name, bridges, chain_data, successful_txs):
    web3 = Web3(Web3.HTTPProvider(chain_data['rpc_url']))
    
    if not web3.is_connected():
        print(f"无法连接到 {network_name}")
        return successful_txs
    
    print(f"成功连接到 {network_name}")

    for bridge in bridges:
        for i, private_key in enumerate(private_keys):
            try:
                account = Account.from_key(private_key)
                my_address = account.address

                data = data_bridge.get(bridge)
                if not data:
                    print(f"桥接 {bridge} 数据不可用!")
                    continue

                result = send_bridge_transaction(web3, account, my_address, data, network_name)
                if result[0] == "insufficient_funds":  # 处理余额不足的情况
                    return "insufficient_funds"
                elif result[0]:  # 如果交易成功
                    tx_hash, value_sent = result
                    successful_txs += 1
                    
                    if value_sent is not None:
                        print(f"{chain_symbols[network_name]}🚀 成功交易总数: {successful_txs} | {labels[i]} | 桥接: {bridge} | 桥接金额: {value_sent:.5f} ETH ✅{reset_color}\n")
                    else:
                        print(f"{chain_symbols[network_name]}🚀 成功交易总数: {successful_txs} | {labels[i]} | 桥接: {bridge} ✅{reset_color}\n")

                    print(f"{'='*150}\n")
                else:
                    time.sleep(1)
                    print(f"地址 {my_address} 交易失败,尝试下一个地址")
                    continue

            except Exception as e:
                time.sleep(1)
                print(f"处理地址 {my_address} 时发生错误: {e}")
                continue

    return successful_txs

# 显示链选择菜单的函数
def display_menu():
    print(f"{menu_color}选择要运行交易的链:{reset_color}")
    print(" ")
    print(f"{chain_symbols['Arbitrum Sepolia']}1. Arbitrum Sepolia <-> Blast Sepolia{reset_color}")
    print(f"{chain_symbols['Blast Sepolia']}2. Blast Sepolia <-> Base Sepolia{reset_color}")
    print(f"{chain_symbols['Optimism Sepolia']}3. Optimism Sepolia -> Blast Sepolia{reset_color}")
    print(f"{chain_symbols['Blast Sepolia']}4. Blast Sepolia -> Optimism Sepolia{reset_color}")
    print(f"{chain_symbols['Optimism Sepolia']}5. Optimism Sepolia <-> Base Sepolia{reset_color}")
    print(f"{menu_color}按 'q' 退出程序{reset_color}")
    print(" ")
    choice = input("输入选择 (1-5): ")
    return choice

def main(current_network, alternate_network):
    while True:  # 外层无限循环
        try:
            print("\033[92m" + center_text(description) + "\033[0m")
            print("\n\n")

            successful_txs = 0
            insufficient_funds_count = 0  # 记录余额不足的链数

            while True:  # 内层业务循环
                try:
                    # 检查网络连接
                    web3 = Web3(Web3.HTTPProvider(networks[current_network]['rpc_url']))
                    retry_count = 0
                    while not web3.is_connected() and retry_count < 10:
                        print(f"无法连接到 {current_network}，第 {retry_count + 1} 次重试...")
                        time.sleep(0.1)  # 仅等待0.1秒
                        web3 = Web3(Web3.HTTPProvider(networks[current_network]['rpc_url']))
                        retry_count += 1
                    
                    if not web3.is_connected():
                        print(f"无法连接到 {current_network}，切换到备用网络")
                        current_network, alternate_network = alternate_network, current_network
                        continue

                    #print(f"成功连接到 {current_network}")
                    
                    my_address = Account.from_key(private_keys[0]).address
                    balance = check_balance(web3, my_address)

                    # 如果余额不足 0.41 ETH，切换到另一个链
                    if balance < 0.41:
                        print(f"{chain_symbols[current_network]}{current_network}余额不足 0.41 ETH，切换到 {alternate_network}{reset_color}")
                        current_network, alternate_network = alternate_network, current_network

                    # 处理当前链的交易
                    bridge_key = f"{current_network} - {alternate_network}"
                    result = process_network_transactions(
                        current_network, 
                        [bridge_key],
                        networks[current_network], 
                        successful_txs
                    )
                    
                    # 如果返回的是元组,说明是正常的交易结果
                    if isinstance(result, tuple):
                        successful_txs = result[0]
                        insufficient_funds_count = 0  # 重置计数器
                    # 如果返回的是字符串"insufficient_funds",说明当前链余额不足
                    elif result == "insufficient_funds":
                        insufficient_funds_count += 1
                        if insufficient_funds_count >= 2:  # 两条链都没钱了
                            print("两条链都余额不足,等待30秒后重试...")
                            time.sleep(30)
                            insufficient_funds_count = 0  # 重置计数器
                        
                    # 切换到另一条链
                    current_network, alternate_network = alternate_network, current_network

                except Exception as e:
                    print(f"内层循环发生错误: {str(e)}")
                    time.sleep(0.1)
                    continue

        except KeyboardInterrupt:
            print("\n程序被用户中断")
            sys.exit(0)
        except Exception as e:
            print(f"外层循环发生错误: {str(e)}")
            time.sleep(0.1)
            continue

def check_all_balances():
    clear_terminal()
    print(f"{menu_color}=== 查询所有链上余额 ==={reset_color}\n")
    
    # 创建BRN的Web3实例
    brn_web3 = Web3(Web3.HTTPProvider('https://brn.rpc.caldera.xyz/http'))
    
    # 简化网络名称
    network_display_names = {
        'Arbitrum Sepolia': 'Arbitrum',
        'Blast Sepolia': 'Blast',
        'Optimism Sepolia': 'Optimism',
        'Base Sepolia': 'Base'
    }
    
    for i, private_key in enumerate(private_keys):
        account = Account.from_key(private_key)
        address = account.address
        print(f"\n{menu_color}=== 地址 {labels[i]} ==={reset_color}")
        print(f"钱包地址: {address}")
        
        # 查询BRN余额
        brn_balance = get_brn_balance(brn_web3, address)
        print(f"BRN\t\t{brn_balance:.2f} BRN")
        
        # 查询各链ETH余额
        for network_name, network_data in networks.items():
            try:
                web3 = Web3(Web3.HTTPProvider(network_data['rpc_url']))
                display_name = network_display_names[network_name]
                if web3.is_connected():
                    balance = check_balance(web3, address)
                    print(f"{chain_symbols[network_name]}{display_name:<12}{balance:.6f} ETH{reset_color}")
                else:
                    print(f"{chain_symbols[network_name]}{display_name:<12}连接失败{reset_color}")
            except Exception as e:
                print(f"{chain_symbols[network_name]}{display_name:<12}查询出错{reset_color}")
        
        print(f"{menu_color}{'='*50}{reset_color}")
    
    print("\n按任意键返回主菜单...")
    
    # 跨平台按键检测
    try:
        import msvcrt  # Windows
        msvcrt.getch()
    except ImportError:
        try:
            import tty, termios  # Unix
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except:
            input()  # 如果上述方法都失败，回退到input()

if __name__ == "__main__":
    while True:  # 最外层的程序重启循环
        try:
            choice = display_menu()
            
            if choice.lower() == 'q':
                print("退出程序...")
                sys.exit(0)
                
            if choice == '1':
                current_network = 'Arbitrum Sepolia'
                alternate_network = 'Blast Sepolia'
            elif choice == '2':
                current_network = 'Blast Sepolia'
                alternate_network = 'Base Sepolia'
            elif choice == '3':
                current_network = 'Blast Sepolia'
                alternate_network = 'Optimism Sepolia'
            elif choice == '4':
                current_network = 'Blast Sepolia'
                alternate_network = 'Optimism Sepolia'
            elif choice == '5':
                current_network = 'Optimism Sepolia'
                alternate_network = 'Base Sepolia'
            else:
                print("无效选择，请重试")
                continue

            main(current_network, alternate_network)
            
        except Exception as e:
            print(f"程序异常退出: {str(e)}")
            time.sleep(0.1)  # 仅等待0.1秒

