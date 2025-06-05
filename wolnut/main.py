import time
import logging
from wolnut.config import load_config
from wolnut.state import ClientStateTracker
from wolnut.monitor import get_ups_status, is_client_online
from wolnut.wol import send_wol_packet

logger = logging.getLogger("wolnut")


def main():
    config = load_config()
    logger.info("WOLNUT started. Monitoring UPS: %s", config.nut.ups)
    logger.debug(config.nut.ups)

    on_battery = False
    recorded_down_clients = set()
    battery_percent = 100
    restoration_event = False

    state_tracker = ClientStateTracker(config.clients)
    if state_tracker.was_ups_on_battery():
        logger.info("WOLNUT is resuming from a UPS battery event")
        restoration_event = True
        state_tracker.reset()

    while True:
        ups_status = get_ups_status(config.nut.ups)
        battery_percent = int(ups_status.get("battery.charge", 100))
        # OL = On Line, OB = On Battery
        power_status = ups_status.get("ups.status", "OL")

        logger.debug("UPS power status: %s, Battery: %s%%",
                     power_status, battery_percent)

        # Check each client
        for client in config.clients:
            online = is_client_online(client.host)
            state_tracker.update(client.name, online)

        # Power Loss Event
        if "OB" in power_status and not on_battery:
            state_tracker.mark_all_online_clients()
            state_tracker.set_ups_on_battery(True, battery_percent)
            on_battery = True
            # recorded_down_clients.clear() <----- why is this here???
            logger.warning("UPS switched to battery power.")

        # Power Restoration Event
        elif "OL" in power_status and on_battery and battery_percent >= config.wake_on.min_battery_percent:
            restoration_event = True
            logger.info("Power restored and battery >= %s%%. Preparing to send WOL...",
                        config.wake_on.min_battery_percent)

            for client in config.clients:
                if not state_tracker.was_online_before_shutdown(client.name):
                    logger.info(
                        "Skipping WOL for %s: was not online before power loss", client.name)
                    continue

                if not state_tracker.is_online(client.name):
                    if send_wol_packet(client.mac):
                        state_tracker.mark_wol_sent(client.name)

            on_battery = False
            recorded_down_clients.clear()
            state_tracker.reset()
            state_tracker.set_ups_on_battery(False)

        if not on_battery:
            time.sleep(config.poll_interval)
        else:
            time.sleep(2)


main()
