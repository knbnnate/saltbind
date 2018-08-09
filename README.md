# saltbind
SaltStack managing a bind instance to resolve all minions to a local zone.

To get started:

* Install salt/\_modules/ip\_db.py in an appropriate \_modules directory in your salt instance
* Add the mine\_functions call from pillar/base.sls to the pillar available to any minions that should be in dns
* salt '\*' saltutil.refresh\_pillar
* salt '\*' saltutil.sync\_modules
* salt '\*' mine.update
* Build DNS servers and add them to the pillar for saltbind based on the pillar.example
* Apply the saltbind state to those servers

Caveats/known issues:
* This relies on an assumption that all minions that require a salt-managed DNS entry have a route to the public internet through the interface that is bound to the ip address you want in DNS
