class IpInfo:
    def __init__(self):
        self.ips = {}

    def add_ip(self, ip, port, username, password, ready, provider, provider_instance, proxy_id):
        if ip not in self.ips:
            self.ips[ip] = {}
        self.ips[ip]['port'] = port
        self.ips[ip]['username'] = username
        self.ips[ip]['password'] = password
        self.ips[ip]['ready'] = ready
        self.ips[ip]['provider'] = provider
        self.ips[ip]['provider_instance'] = provider_instance
        self.ips[ip]['id'] = proxy_id 