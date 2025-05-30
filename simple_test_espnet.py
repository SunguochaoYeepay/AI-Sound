import socket

def test_espnet_port():
    """简单测试ESPnet端口连接"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('127.0.0.1', 9001))
        sock.close()
        
        if result == 0:
            print("✅ ESPnet端口9001可连接")
            return True
        else:
            print("❌ ESPnet端口9001无法连接")
            return False
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🔍 ESPnet端口连接测试")
    test_espnet_port()