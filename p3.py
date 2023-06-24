from mininet.net import Containernet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.cli import CLI

print("----------")
print("Creating mininet instance")
print("----------")
# Create Containernet instance
net = Containernet(controller=RemoteController, switch=OVSKernelSwitch)

# Add switch
s1 = net.addSwitch('s1')

# hosts
host1 = net.addHost('host1', ip='192.168.2.10', mac='00:00:00:00:00:01', )
host2 = net.addHost('host2', ip='192.168.2.20', mac='00:00:00:00:00:02', )
host3 = net.addHost('host3', ip='192.168.2.30', mac='00:00:00:00:00:03', )
host4 = net.addHost('host4', ip='192.168.2.40', mac='00:00:00:00:00:04', )

# links
net.addLink(s1, host1, intfName2='h1-eth0')
net.addLink(s1, host2, intfName2='h2-eth0')
net.addLink(s1, host3, intfName2='h3-eth0')
net.addLink(s1, host4, intfName2='h4-eth0')

# Start the network
net.start()

# Set the default route for the hosts
# host1.setDefaultRoute('via 10.0.0.1')
host1.setDefaultRoute('via 192.168.0.1')
host2.setDefaultRoute('via 192.168.0.1')
host3.setDefaultRoute('via 192.168.0.1')
host4.setDefaultRoute('via 192.168.0.1')

# Assign IP address 10.0.2.10 to container host #1's port connected to Switch 1
# host1.setIP('10.0.2.10/24', intf='host1-eth0')

# Assign IP address 192.168.2.10 to container host #1's port connected to Switch 2
# host1.setIP('192.168.2.10/24', intf='host1-eth1')


# Connect the switches to POX controllers
c1 = net.addController('c1', controller=RemoteController, ip='127.0.0.1', port=6655)
# c1 = net.addController('c1', controller=RemoteController, ip='127.0.0.1', port=6633)
# c2 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6655)
s1.start([c1])
# s2.start([c2])

# Get host objects (TESTING) -------
host1 = net.get('host1')
host3 = net.get('host3')

# Ping host3 from host1
result = host1.cmd('ping -c 4 192.168.2.30')

# Print the result
print(result)
# DONE TEST

# Open CLI for testing and interaction
CLI(net)

# Clean up and stop the network when done
net.stop()
