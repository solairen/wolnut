import logging
from wakeonlan import send_magic_packet

logger = logging.getLogger("wolnut")


def send_wol_packet(mac_address: str, broadcast_ip: str = "255.255.255.255") -> bool:
    try:
        logger.info("Sending WOL packet to %s", mac_address)
        send_magic_packet(mac_address, ip_address=broadcast_ip)
        return True
    except Exception as e:
        logger.error("Failed to send WOL packet to %s: %s", mac_address, e)
        return False
