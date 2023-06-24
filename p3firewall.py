from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.lib.util import dpidToStr
from pox.lib.addresses import EthAddr
from collections import namedtuple
import os
''' New imports here ... '''
import csv
import argparse
from pox.lib.packet.ethernet import ethernet, ETHER_BROADCAST
from pox.lib.addresses import IPAddr
import pox.lib.packet as pkt
from pox.lib.packet.arp import arp
from pox.lib.packet.ipv4 import ipv4
from pox.lib.packet.icmp import icmp

log = core.getLogger()
priority = 50000

l2config = "l2firewall.config"
l3config = "l3firewall.config"


class Firewall (EventMixin):

	def __init__ (self,l2config,l3config):
		self.listenTo(core.openflow)
		#self.disbaled_MAC_pair = [] # Shore a tuple of MAC pair which will be installed into the flow table of each switch.

        	self.SpoofingTable = dict ()    # Corrispondence of MAC addresses with IPs and ports
        	self.BlockedTable = dict ()     # Table of blocked attacks

		'''
		Read the CSV file
		'''
		if l2config == "":
			l2config="l2firewall.config"
			
		if l3config == "":
			l3config="l3firewall.config" 
		with open(l2config, 'rb') as rules:
			csvreader = csv.DictReader(rules) # Map into a dictionary
			for line in csvreader:
				# Read MAC address. Convert string to Ethernet address using the EthAddr() function.
		                if line['mac_0'] != 'any':
				   	mac_0 = EthAddr(line['mac_0'])
		                else:
		                    	mac_0 = None

		                if line['mac_1'] != 'any':
					mac_1 = EthAddr(line['mac_1'])
		                else:
					mac_1 = None
					# Append to the array storing all MAC pair.
					self.disbaled_MAC_pair.append((mac_0,mac_1))

		with open(l3config) as csvfile:
			log.debug("Reading log file !")
			self.rules = csv.DictReader(csvfile)
			for row in self.rules:
				log.debug("Saving individual rule parameters in rule dict !")
				prio = row['priority']
				s_mac = row['src_mac']
				d_mac = row['dst_mac']
				s_ip = row['src_ip']
				d_ip = row['dst_ip']
				s_port = row['src_port']
				d_port = row['dst_port']
				nw_proto = row['nw_proto']
				print "src_ip, dst_ip, src_port, dst_port", s_ip,d_ip,s_port,d_port
		                # Add to firewall rules in memory
				log.debug("Keep firewall rules in memory")
		                if s_mac != "any" and d_mac == "any" and s_ip == "any" and d_ip != "any" and s_port == "any" and d_port == "any" and nw_proto == "any":
		                    self.SpoofingTable [s_mac] = [s_ip, d_ip, 'any']
		                if s_mac == "any" and d_mac == "any" and s_ip != "any" and d_ip != "any" and s_port == "any" and d_port == "any" and nw_proto == "any":
		                    self.SpoofingTable [s_mac] = [s_ip, d_ip, 'any']
		                # Install OVS flow
		                #self.installFlow(event, prio, s_mac, d_mac, s_ip, d_ip, s_port, d_port, nw_proto)

		log.debug("Enabling Firewall Module")

	def replyToARP(self, packet, match, event):
		r = arp()
		r.opcode = arp.REPLY
		r.hwdst = match.dl_src
		r.protosrc = match.nw_dst
		r.protodst = match.nw_src
		r.hwsrc = match.dl_dst
		e = ethernet(type=packet.ARP_TYPE, src = r.hwsrc, dst=r.hwdst)
		e.set_payload(r)
		msg = of.ofp_packet_out()
		msg.data = e.pack()
		msg.actions.append(of.ofp_action_output(port=of.OFPP_IN_PORT))
		msg.in_port = event.port
		event.connection.send(msg)

	def allowOther(self, event, action=None):
                log.debug ("Execute allowOther")
		msg = of.ofp_flow_mod()
		match = of.ofp_match()
		#action = of.ofp_action_output(port = of.OFPP_NORMAL)
		msg.actions.append(action)
		event.connection.send(msg)

	def installFlow(self, event, offset, srcmac, dstmac, srcip, dstip, sport, dport, nwproto):
                log.debug ("Execute installFlow")
		msg = of.ofp_flow_mod()
		match = of.ofp_match()
		if(srcip != None):
			match.nw_src = IPAddr(srcip)
		if(dstip != None):
			match.nw_dst = IPAddr(dstip)	
                if(nwproto):
                        match.nw_proto = int(nwproto)
		match.dl_src = srcmac
		match.dl_dst = dstmac
		match.tp_src = sport
		match.tp_dst = dport
		match.dl_type = pkt.ethernet.IP_TYPE
		msg.match = match
		msg.hard_timeout = 0
		msg.idle_timeout = 200
                #msg.actions.append(None)
                if priority + offset <= 65535:
                    msg.priority = priority + offset		
                else:
                    msg.priority = 65535

		event.connection.send(msg)

	def replyToIP(self, packet, match, event):
                log.debug ("Execute replyToIP")
		srcmac = str(match.dl_src)
		dstmac = str(match.dl_src)
		sport = str(match.tp_src)
		dport = str(match.tp_dst)
		nwproto = str(match.nw_proto)

                with open(l3config) as csvfile:
                    log.debug("Reading log file !")
                    self.rules = csv.DictReader(csvfile)
                    for row in self.rules:
                        prio = row['priority']
                        srcmac = row['src_mac']
                        dstmac = row['dst_mac']
                        s_ip = row['src_ip']
                        d_ip = row['dst_ip']
                        s_port = row['src_port']
                        d_port = row['dst_port']
                        nw_proto = row['nw_proto']
                        
                        log.debug("You are in original code block ...")
                        srcmac1 = EthAddr(srcmac) if srcmac != 'any' else None
                        dstmac1 = EthAddr(dstmac) if dstmac != 'any' else None
                        s_ip1 = s_ip if s_ip != 'any' else None
                        d_ip1 = d_ip if d_ip != 'any' else None
                        s_port1 = int(s_port) if s_port != 'any' else None
                        d_port1 = int(d_port) if d_port != 'any' else None
                        prio1 = int(prio) if prio != None else priority
                        if nw_proto == "tcp":
                            nw_proto1 = pkt.ipv4.TCP_PROTOCOL
                        elif nw_proto == "icmp":
                            nw_proto1 = pkt.ipv4.ICMP_PROTOCOL
                            s_port1 = None
                            d_port1 = None
                        elif nw_proto == "udp":
                            nw_proto1 = pkt.ipv4.UDP_PROTOCOL
                        else:
                            nw_proto1 = None
                            #log.debug("PROTOCOL field is mandatory, Choose between ICMP, TCP, UDP")
                        print (prio1, srcmac1, dstmac1, s_ip1, d_ip1, s_port1, d_port1, nw_proto1)
                        self.installFlow(event, prio1, srcmac1, dstmac1, s_ip1, d_ip1, s_port1, d_port1, nw_proto1)

                #self.allowOther(event)

	def _handle_ConnectionUp (self, event):
		''' Add your logic here ... '''

		'''
		Iterate through the disbaled_MAC_pair array, and for each
		pair we install a rule in each OpenFlow switch
		'''
		self.connection = event.connection

		#for (source, destination) in self.disbaled_MAC_pair:

                for spoofmac, spoofvalues in self.SpoofingTable.items():

                        srcmac = spoofmac
                        srcip = spoofvalues[0]
                        dstip = spoofvalues[1]
                        log.debug ('Loading blocked flows: srcmac=%s, srcip=%s, dstip=%s' %
                                (str(srcmac), str(srcip), str(dstip)))
			#print source,destination
			message = of.ofp_flow_mod()     # OpenFlow massage. Instructs a switch to install a flow
			match = of.ofp_match()          # Create a match
                        if srcmac == 'any':
                            match.dl_src = None         # Source MAC
                        else:
                            match.dl_src = srcmac       # Source MAC
                        if srcip == 'any':
                            match.nw_src = None         # Source IP address
                        else:
                            match.nw_src = IPAddr(srcip)    # Source IP address
                        if dstip == 'any':
                            match.nw_dst = None         # Destination IP address
                        else:
                            match.nw_dst = IPAddr(dstip)    # Destination IP address
			message.priority = 65535 # Set priority (between 0 and 65535)
                        match.dl_type = ethernet.IP_TYPE
			message.match = match			
                        #message.actions.append(None)
			event.connection.send(message) # Send instruction to the switch

		log.debug("Firewall rules installed on %s", dpidToStr(event.dpid))

        def addRuleToCSV(self, srcmac='any', srcip='any', dstip='any'):
            
            log.debug("Entered addRuleToCSV")

            # Check if the rule is not already saved
            # If not, add to firewall rules in memory and then in the CSV file

            to_add = True
            for spoofmac, spoofvalues in self.BlockedTable.items():
                if spoofmac == str(srcmac) and spoofvalues[0] == str(srcip) and spoofvalues[1] == str(dstip):
                    log.debug("No need to write log file - entry already present")
                    to_add = False
                    break

            if to_add: 
                self.BlockedTable [str(srcmac)] = [str(srcip), str(dstip)]
                # Open in append mode
                with open(l3config, 'a') as csvfile:
                    log.debug("Writing log file !")

                    csvwriter = csv.DictWriter(csvfile, fieldnames=[
                        'priority','src_mac','dst_mac','src_ip','dst_ip','src_port','dst_port','nw_proto',])
                    log.debug("Saving individual rule parameters in rule dict !")
                    csvwriter.writerow({
                        'priority': 32768,
                        'src_mac' : str(srcmac),
                        'dst_mac' : 'any',
                        'src_ip'  : str(srcip),
                        'dst_ip'  : str(dstip),
                        'src_port': 'any',
                        'dst_port': 'any',
                        'nw_proto': 'any',
                        })
                    log.debug("Saved: srcip=%s dstip=%s srcmac=%s" % (str(srcip), str(dstip), str(srcmac)))

        def portTable(self, p, match=None, event=None):

            log.debug("portTable")
           
            srcmac = None
            srcip = None
            dstip = None

            if p.type == p.IP_TYPE:
                pack = p.payload

                if pack.srcip == None or pack.dstip == None:
                    return True
                
                # Mac address not in the iptable:
                if p.src not in self.SpoofingTable:
                    # MAC spoofing case
                    for spoofmac, spoofvalues in self.SpoofingTable.items():
                        if str(spoofvalues[0]) == str(pack.srcip):
                            (str(pack.srcip), str(spoofmac), str(spoofvalues[1]), str(p.src), str(event.port)))
                            
                            # Block src/dst IP for MAC:
                            srcmac = None
                            srcip = str(pack.srcip)
                            dstip = str(pack.dstip)
                            self.addRuleToCSV ('any', srcip, dstip)

                    
                    self.SpoofingTable [p.src] = [pack.srcip, pack.dstip, event.port]
                    log.debug("Adding Port Security entry: %s, %s, %s, %s" %
                        (str(p.src), str(pack.srcip), str(pack.dstip), str(event.port)))
                    return True
                
                # It is in spoofing table:
                else:                                          
                    if self.SpoofingTable.get(p.src) == [pack.srcip, pack.dstip, event.port]:
                        (str(p.src), str(pack.srcip), str(pack.dstip), str(event.port)))
                        return True
                    else:
                        # IP/Port different:

                        newip = self.SpoofingTable.get(p.src)[0]
                        newport = self.SpoofingTable.get(p.src)[1]

                        # Attack - IP Spoofing:
                        if newip != pack.srcip:
                            (str(p.src), str(newip), str(newport), str(pack.dstip), str(event.port)))
                            
                            # Block the MAC address
                            srcmac = str(p.src)
                            srcip = None
                            dstip = str(pack.dstip)
                            self.addRuleToCSV (srcmac, 'any', dstip)
                          
                        # Port change - allow
                        if newport != event.port:
                            (str(newport), str(p.src), str(pack.srcip), str(event.port), str(pack.dstip)))
                            return True

                        return True

            if p.ARP_TYPE == p.type:
                return True

            srcmac = srcmac
            dstmac = None
            sport = None
            dport = None
            nwproto = str(match.nw_proto)

            log.debug("iflow")
            self.installFlow(event, 32768, srcmac, None, srcip, dstip, None, None, nw_proto)

            return False


	def _handle_PacketIn(self, event):

		packet = event.parsed
		match = of.ofp_match.from_packet(packet)

		if(match.dl_type == packet.ARP_TYPE and match.nw_proto == arp.REQUEST):
		    self.replyToARP(packet, match, event)

        if(match.dl_type == packet.IP_TYPE):
		    if self.portTable(packet, match, event):
		        # No attack
		    else:
			    log.debug("Attack detected - flow to be blocked")

			    #ip_packet = packet.payload
			    #print "Ip_packet.protocol = ", ip_packet.protocol
			    #if ip_packet.protocol == ip_packet.TCP_PROTOCOL:
			#	log.debug("TCP it is !")

			    self.replyToIP(packet, match, event)


def launch (l2config="l2firewall.config",l3config="l3firewall.config"):
	'''
	Starting the Firewall module
	'''
	parser = argparse.ArgumentParser()
	parser.add_argument('--l2config', action='store', dest='l2config',
					help='Layer 2 config file', default='l2firewall.config')
	parser.add_argument('--l3config', action='store', dest='l3config',
					help='Layer 3 config file', default='l3firewall.config')
	core.registerNew(Firewall,l2config,l3config)