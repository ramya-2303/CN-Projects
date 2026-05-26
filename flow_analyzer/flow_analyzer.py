from pox.core import core
import pox.openflow.libopenflow_01 as of

log = core.getLogger()

def _handle_ConnectionUp(event):
    log.info("Switch %s connected", event.dpid)

    msg = of.ofp_stats_request(body=of.ofp_flow_stats_request())
    event.connection.send(msg)

def _handle_FlowStatsReceived(event):
    log.info("\n===== FLOW TABLE =====")

    for stat in event.stats:
        if stat.packet_count > 0:
            status = "ACTIVE"
        else:
            status = "UNUSED"

        log.info("Rule: %s | Packets: %s", status, stat.packet_count)

def launch():
    core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
    core.openflow.addListenerByName("FlowStatsReceived", _handle_FlowStatsReceived)