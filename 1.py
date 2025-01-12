from web3 import Web3
from network_config import networks  # 导入网络配置

# 连接到 RPC
rpc_url = "https://brn.rpc.caldera.xyz/http"
web3 = Web3(Web3.HTTPProvider(rpc_url))

# 检查 RPC 连接是否正常
if not web3.is_connected():
    print("无法连接到 RPC，请检查网络或 RPC 地址。")
    exit()

# 从 addr.txt 中读取地址
addr_file = "addr.txt"
try:
    with open(addr_file, "r") as file:
        addresses = [line.strip() for line in file if line.strip()]
except FileNotFoundError:
    print(f"文件 {addr_file} 不存在，请确保该文件在当前目录下。")
    exit()

# 存储转换后的地址
converted_addresses = []
has_address_converted = False  # 添加标志位追踪是否有地址被转换

# 查询 BRN 余额的部分添加总和统计
total_brn_balance = 0  # 添加 BRN 总余额统计

# 查询每个地址的余额
for address in addresses:
    # 自动将非 checksum 地址转换为 checksum 格式
    if not web3.is_checksum_address(address):
        print(f"非 EIP-55 校验地址：{address}，尝试自动转换为 checksum 地址...")
        try:
            converted_address = web3.to_checksum_address(address)
            print(f"转换后的 checksum 地址：{converted_address}")
            has_address_converted = True  # 标记有地址被转换
            address = converted_address
        except Exception as e:
            print(f"无法转换地址：{address}，错误：{e}")
            continue

    # 添加到转换后的地址列表
    converted_addresses.append(address)

    # 查询余额
    try:
        balance = web3.eth.get_balance(address)
        balance_in_brn = web3.from_wei(balance, 'ether')
        total_brn_balance += balance_in_brn  # 累加 BRN 余额
        print(f"地址：{address}，余额：{balance_in_brn} BRN")
    except Exception as e:
        print(f"查询地址 {address} 的余额时出错：{e}")

# 只有在有地址被转换的情况下才回写文件
if has_address_converted:
    try:
        with open(addr_file, "w") as file:
            for addr in converted_addresses:
                file.write(f"{addr}\n")
        print(f"检测到地址格式更新，已将转换后的地址保存到 {addr_file}")
    except Exception as e:
        print(f"回写文件时出错：{e}")
else:
    print("所有地址格式均正确，无需更新文件")

print(f"\n💫 BRN 网络总余额: {total_brn_balance:.6f} BRN")  # 打印 BRN 总余额

def check_all_balances(addresses):
    """检查所有地址在各个网络的余额并返回结果"""
    network_emojis = {
        'Arbitrum': '🟣',  # 简化网络名称
        'Blast': '💥',
        'Optimism': '🔴',
        'Base': '🔷'
    }
    
    # 存储所有查询结果
    results = {addr: {} for addr in addresses}
    
    print("\n📊 各网络余额查询结果:")
    
    for network_name, network_data in networks.items():
        # 简化显示的网络名称
        display_name = network_name.replace(' Sepolia', '')
        print(f"\n{network_emojis[display_name]} {display_name}:")
        
        web3 = Web3(Web3.HTTPProvider(network_data['rpc_url']))
        if not web3.is_connected():
            print(f"❌ 无法连接到 {display_name}")
            continue
            
        for address in addresses:
            try:
                balance = web3.eth.get_balance(address)
                balance_eth = web3.from_wei(balance, 'ether')
                print(f"    {address} => {balance_eth:.6f} ETH")  # 增加缩进
                results[address][display_name] = balance_eth
            except Exception as e:
                print(f"    {address} => 查询失败: {e}")  # 增加缩进
                results[address][display_name] = None
    
    return results, network_emojis

def print_balance_summary(results, network_emojis):
    """使用缓存的结果打印余额汇总"""
    print("\n💰 地址余额汇总:")
    
    # 计算每个地址的总余额
    address_totals = {}
    network_totals = {network: 0 for network in network_emojis.keys()}  # 添加网络总额统计
    
    for address, balances in results.items():
        total = sum(bal for bal in balances.values() if bal is not None)
        address_totals[address] = total
        # 累加每个网络的总额
        for network, balance in balances.items():
            if balance is not None:
                network_totals[network] += balance
    
    # 计算所有网络的总和
    grand_total = sum(network_totals.values())
    
    # 打印每个地址的汇总
    sorted_addresses = sorted(address_totals.items(), key=lambda x: x[1], reverse=True)
    for address, total in sorted_addresses:
        print(f"\n👛 地址: {address}")
        for network, balance in results[address].items():
            emoji = network_emojis[network]
            if balance is not None:
                print(f"    {emoji} {network:<8} {balance:.6f} ETH")
            else:
                print(f"    {emoji} {network:<8} ❌ 查询失败")
        print(f"    💎 总余额:    {total:.6f} ETH")
    
    # 打印网络总额统计
    print("\n🌐 网络总额统计:")
    for network, total in network_totals.items():
        emoji = network_emojis[network]
        print(f"    {emoji} {network:<8} {total:.6f} ETH")
    
    # 打印总计
    print(f"\n🏆 所有网络总计: {grand_total:.6f} ETH")

# 修改主程序调用
print("\n开始查询所有地址在各网络的余额...")
balance_results, network_emojis = check_all_balances(converted_addresses)

print("\n正在生成余额汇总报告...")
print_balance_summary(balance_results, network_emojis)

