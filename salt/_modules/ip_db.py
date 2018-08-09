"""
This module provides utility functions for working with IPv4 addresses in ways convenient for managing DNS servers across aribitrary scopes.

Some example inputs and outputs:

                     reverse("255.128.63.16"):        16.63.128.255
                reverse_zone("255.128.63.16"):           63.128.255
            reverse_zone("255.128.63.16","b"):              128.255
 reverse_zone("255.128.63.16",zone_class="a"):                  255
            reverse_zone("255.128.63.16","C"):           63.128.255
                reverse_zone("0.0.10.20","C"):               10.0.0
                add("10.10.10.0","0.0.10.20"):          10.10.20.20
               sub("10.10.20.20","0.0.10.20"):           10.10.10.0
                 mod("10.10.20.20","0.0.1.0"):             0.0.0.20
               shift("10.10.20.20","0.0.1.0"):           10.10.20.0
                mod("10.10.20.20","0.0.16.0"):             0.0.4.20
              shift("10.10.20.20","0.0.16.0"):           10.10.16.0
                mod("10.10.20.20","0.16.0.0"):           0.10.20.20
              shift("10.10.20.20","0.16.0.0"):             10.0.0.0
                    add("10.10.10.0","10.20"):          10.10.20.20
                      add("10.10.10.0",10.20):           10.10.20.2

Note that when IP segments with trailing zeroes can be interpreted as floats, the integrity of the operations is compromised.
Be explicit that such segments are strings when storing them e.g. in pillar.

"""

from collections import Mapping

# private ipv4 conversion towards int
def _ipv4_2_hex(ipv4_str):
  return "".join(["{0:02x}".format(int(octet)) for octet in ipv4_str.split(".")])
def _hex_2_int(hex_str):
  return int("0x{0}".format(hex_str),16)
def _ipv4_2_int(ipv4_str):
  return _hex_2_int(_ipv4_2_hex(ipv4_str))

# private ipv4 conversion from int
def _int_2_hex(ipv4_int):
  return "{0:08x}".format(ipv4_int)
def _hex_2_ipv4(hex_str):
  return ".".join(["{0:d}".format(int(octet,16)) for octet in [hex_str[x:x+2] for x in [0,2,4,6]]])
def _int_2_ipv4(ipv4_int):
  return _hex_2_ipv4(_int_2_hex(ipv4_int))

# exposed
def manifest(public_routes):
  '''
  A function that takes as input the salt-mined results of `network.get_route 8.8.8.8` 
  to determine the most relevant IP address for each salt minion and its corresponding PTR information.

  Suggestion is to configure mine_functions pillar in base role as follows:

  mine_functions:
    public_route:
      - mine_function: network.get_route
      - 8.8.8.8

  CLI Example::
      salt-call ip_db.manifest \ 
        $(salt-call mine.get '*' 'public_route' --out=json | jq ".[]|tostring" | sed -r -e 's/^"//' -e 's/"$//' | xargs printf) \  
        --out=json

  Should return:

      {"saltmaster":{"ip":"10.1.10.20","reverse_ip":"20.10.1.10","reverse_zone":"10.1.10","reverse_entry":"20"},
       "linux-1":   {"ip":"10.2.10.20","reverse_ip":"20.10.2.10","reverse_zone":"10.2.10","reverse_entry":"20"}}

  '''
  if isinstance(public_routes, Mapping):
    ip_db = {}
    for key in public_routes.keys():
      hostname = key.split(".")[0]
      ip = public_routes.get(key,{}).get('source',"0.0.0.0")
      reverse_ip=reverse(ip)
      reverse_ip_zone=reverse_zone(ip,"C")
      reverse_entry=ip.split(".")[3]
      ip_db[hostname]={"ip": ip, "reverse_ip": reverse_ip, "reverse_zone": reverse_ip_zone, "reverse_entry": reverse_entry}
    return ip_db
  else:
    return {}

def manifest_reverse_zones(ip_db):
  '''
  A function that returns a sorted list of distinct reverse record zones from a dict created by the manifest method

  CLI Example:

      salt-call ip_db.manifest_reverse_zones $(salt-call ip_db.manifest \ 
        $(salt-call mine.get '*' 'public_route' --out=json | jq ".[]|tostring" | sed -r -e 's/^"//' -e 's/"$//' | xargs printf) \  
        | jq ".[]|tostring" | sed -r -e 's/^"//' -e 's/"$//' | xargs printf) \  
        --out=json 

  Should return:
    ["10.1.10","10.2.10"]

  '''
  reverse_zones=[]
  if isinstance(ip_db, Mapping):
    for hostname in ip_db.keys():
      reverse_zone=ip_db.get(hostname).get("reverse_zone",False)
      if reverse_zone and reverse_zone not in reverse_zones:
        reverse_zones.append(reverse_zone)
    reverse_zones.sort()
  return reverse_zones

def manifest_reverse_zone_members(ip_db,reverse_zone):
  '''
  A function that returns a sorted list of distinct members of a reverse zone within an ip_db

  CLI Example:

      salt-call ip_db.manifest_reverse_zone_members $(salt-call ip_db.manifest \ 
        $(salt-call mine.get '*' 'public_route' --out=json | jq ".[]|tostring" | sed -r -e 's/^"//' -e 's/"$//' | xargs printf) \  
        | jq ".[]|tostring" | sed -r -e 's/^"//' -e 's/"$//' | xargs printf) \  
        10.2.10 \   
        --out=json 

  Should return:
    [{"reverse_entry":"20","hostname":"linux-1"}]

  '''
  members=[]
  if isinstance(ip_db, Mapping):
    for hostname in ip_db.keys():
      host_reverse_zone=ip_db.get(hostname).get("reverse_zone",False)
      if host_reverse_zone == reverse_zone:
        members.append({"hostname":hostname,"reverse_entry":ip_db.get(hostname).get("reverse_entry")})
  return members

def reverse(ipv4_str):
  '''
  A function to reverse the octets of an IPv4 address, e.g. to determine an in-addr.arpa zone entry.

  CLI Example::

      salt '*' ip_db.reverse 255.128.63.16
    
  '''
  return ".".join(str(ipv4_str).split(".")[::-1])

def add(ip_a,ip_b):
  '''
  A function to add together two IPv4 addressess as if they were integers.

  CLI Example::

      salt '*' ip_db.add 10.10.10.0 0.0.10.20
  '''
  return _int_2_ipv4(_ipv4_2_int(str(ip_a))+_ipv4_2_int(str(ip_b)))

def sub(ip_a,ip_b):
  '''
  A function to subtract an IPv4 address from another as if they were integers.

  CLI Example::

      salt '*' ip_db.sub 10.10.20.20 0.0.10.20
  '''
  return _int_2_ipv4(_ipv4_2_int(str(ip_a))-_ipv4_2_int(str(ip_b)))

def mod(ip_a,ip_b):
  '''
  A function to modulus one IPv4 address against another as if they were integers.

  CLI Example::
      salt '*' ip_db.mod 10.10.20.20 0.0.1.0
  '''
  return _int_2_ipv4(_ipv4_2_int(str(ip_a))%_ipv4_2_int(str(ip_b)))

def shift(ip_a,ip_b):
  '''
  A function to shift one IPv4 address in terms of another as if they were integers.

  CLI Example::
      salt '*' ip_db.shift 10.10.20.20 0.0.1.0
  '''
  return sub(str(ip_a),mod(str(ip_a),str(ip_b)))

def reverse_zone(ipv4_str,zone_class="C"):
  '''
  A function to reverse the octets of an IPv4 address, e.g. to determine an in-addr.arpa zone name.

  CLI Example::

      salt '*' ip_db.reverse_zone 255.128.63.16
      salt '*' ip_db.reverse_zone 255.128.63.16 zone_class=B
    
  '''
  if zone_class.upper() == "C":
    zone_shift="0.0.1.0"
    fields=3
  elif zone_class.upper() == "B":
    zone_shift="0.1.0.0"
    fields=2
  elif zone_class.upper() == "A":
    zone_shift="1.0.0.0"
    fields=1
  padded = reverse(shift(ipv4_str,zone_shift))
  while padded.split(".")[0] == "0" and len(padded.split(".")) > fields:
    padded = ".".join(padded.split(".")[1:])
  return padded

if False:
  print ""
  for test_case in ['reverse("255.128.63.16")',
                    'reverse_zone("255.128.63.16")',
                    'reverse_zone("255.128.63.16","b")',
                    'reverse_zone("255.128.63.16",zone_class="a")',
                    'reverse_zone("255.128.63.16","C")',
                    'reverse_zone("10.0.0.0","C")',
                    'reverse_zone("10.0.0.0","B")',
                    'reverse_zone("0.10.0.0","C")',
                    'reverse_zone("0.10.0.0","B")',
                    'reverse_zone("0.0.10.20","C")',
                    'add("10.10.10.0","0.0.10.20")',
                    'sub("10.10.20.20","0.0.10.20")',
                    'mod("10.10.20.20","0.0.1.0")',
                    'shift("10.10.20.20","0.0.1.0")',
                    'mod("10.10.20.20","0.0.16.0")',
                    'shift("10.10.20.20","0.0.16.0")',
                    'mod("10.10.20.20","0.16.0.0")',
                    'shift("10.10.20.20","0.16.0.0")',
                    'add("10.10.10.0","10.20")',
                    'add("10.10.10.0",10.20)']:
    print "{0:>45s}: {1:>20s}".format(test_case, eval(test_case))
  print ""
