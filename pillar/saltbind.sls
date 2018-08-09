saltbind:
  options:
    dnssec-enable: no
    forwarders:
      - 168.63.129.16
  logging:
    channel: debug
    file: data/named.run
    severity: dynamic
  acls:
    azure-internal-platform:
      - 168.63.129.16/32
  views:
    default:
      acl: any
      zone: salt.local
      forward_zones:
        app-production.local:
          - 10.40.30.20
          - 10.40.30.21
      nameservers:
        - dns001
        - dns002
