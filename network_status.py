# Modified version: Use /sys/class/net for reliable interface listing, no parsing issues
# Original base: https://github.com/JeremyRuhland/klipper_network_status
import os, subprocess, logging

class network_status:
    def __init__(self, config):
        self.interval = config.getint('interval', 60, minval=10)
        self.ethip = "N/A"
        self.wifiip = "N/A"
        self.wifissid = "N/A"
        self.mdns = "N/A"
        self.last_eventtime = 0

    def _get_interfaces(self):
        """Get list of non-lo interfaces from /sys/class/net"""
        try:
            interfaces = [iface for iface in os.listdir('/sys/class/net') if iface != 'lo']
            return interfaces
        except Exception as e:
            logging.error(f"Failed to get interfaces from /sys: {e}")
            return []

    def _is_wifi(self, iface):
        """Check if interface is WiFi"""
        try:
            subprocess.check_output(['iw', 'dev', iface, 'info'], timeout=2)
            return True
        except Exception:
            return False

    def _get_ip(self, iface):
        """Get IPv4 IP for interface"""
        try:
            output = subprocess.check_output(['ip', 'addr', 'show', 'dev', iface], timeout=2).decode('utf-8')
            for line in output.splitlines():
                if 'inet ' in line and 'inet6' not in line:
                    return line.strip().split('inet ')[1].split('/')[0]
            return "N/A"
        except Exception as e:
            logging.error(f"Failed to get IP for {iface}: {e}")
            return "N/A"
    def _get_ssid(self, iface):
        """Get WiFi SSID using iw dev <iface> link (more universal than iwgetid)"""
        try:
            output = subprocess.check_output(['iw', 'dev', iface, 'link'], timeout=2).decode('utf-8')
            for line in output.splitlines():
                if 'SSID:' in line:
                    return line.split('SSID:')[1].strip()
            return "N/A"
        except Exception as e:
           logging.error(f"Failed to get SSID for {iface}: {e}")
           return "N/A"



    def get_status(self, eventtime):
        if eventtime - self.last_eventtime > self.interval:
            self.last_eventtime = eventtime
            logging.info("network_status get_status %d" % eventtime)

            interfaces = self._get_interfaces()
            eth_found = False
            wifi_found = False

            for iface in interfaces:
                ip = self._get_ip(iface)
                if ip != "N/A":
                    if self._is_wifi(iface):
                        if not wifi_found:
                            self.wifiip = ip
                            self.wifissid = self._get_ssid(iface)
                            wifi_found = True
                    else:
                        if not eth_found:
                            self.ethip = ip
                            eth_found = True

            # If no specific found, set to N/A
            if not eth_found:
                self.ethip = "N/A"
            if not wifi_found:
                self.wifiip = "N/A"
                self.wifissid = "N/A"

            try:
                hostname = subprocess.check_output(['hostname'], timeout=2).decode('utf-8').strip()
                self.mdns = hostname + '.local'
            except Exception as e:
                logging.error(f"Failed to get hostname: {e}")
                self.mdns = "N/A"

        return {'ethip': self.ethip,
                'wifiip': self.wifiip,
                'wifissid': self.wifissid,
                'mdns': self.mdns}

def load_config(config):
    return network_status(config)
