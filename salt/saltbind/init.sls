saltbind.bind-packages:
  pkg.installed:
    - pkgs:
      - bind
      - bind-utils

{% set public_routes = salt['mine.get']('*','public_route') %}
{% set ip_db = salt['ip_db.manifest'](public_routes) %}
{% set reverse_zones = salt['ip_db.manifest_reverse_zones'](ip_db) %}

saltbind.bind-service:
  service.running:
    - name: named
    - enable: True
    - reload: True
    - watch: {% for view in salt['pillar.get']('saltbind:views',{}).keys() %}{% set zone = salt['pillar.get']('saltbind:views:{0}:zone'.format(view),"salt.local") %}
      - file: /var/named/data/{{ zone }}.zone-{{ view }}-view{% for reverse_zone in reverse_zones %}
      - file: /var/named/data/{{ reverse_zone }}.in-addr.arpa-{{ view }}-view{% endfor %}
      - file: /var/named/data/local.zone-{{ view }}-view{% endfor %}
      - file: /etc/named.conf

saltbind.bind-data:
  file.directory:
    - name: /var/named
    - user: named
    - group: named
    - mode: 755

saltbind.bind-config:
  file.managed:
    - name: /etc/named.conf
    - template: jinja
    - source: salt://roles/saltbind/templates/named.conf.jinja
    - user: root
    - group: root
    - mode: 644

{% for view in salt['pillar.get']('saltbind:views',{}).keys() -%}
{% set zone = salt['pillar.get']('saltbind:views:{0}:zone'.format(view),"salt.local") %}
saltbind.local-zone:
  file.managed:
    - name: /var/named/data/local.zone-{{ view }}-view
    - template: jinja
    - source: salt://roles/saltbind/templates/local.zone.jinja
    - user: named
    - group: named
    - mode: 644
    - defaults:
        view: "{{ view }}"

saltbind.{{ zone }}-{{ view }}-view.zone:
  file.managed:
    - name: /var/named/data/{{ zone }}.zone-{{ view }}-view
    - template: jinja
    - source: salt://roles/saltbind/templates/zone.jinja
    - user: named
    - group: named
    - mode: 644
    - defaults:
        zone: "{{ zone }}"
        view: "{{ view }}"

{% for reverse_zone in reverse_zones -%}
saltbind.{{ reverse_zone }}.in-addr.arpa-{{ view }}-view:
  file.managed:
    - name: /var/named/data/{{ reverse_zone }}.in-addr.arpa-{{ view }}-view
    - template: jinja
    - source: salt://roles/saltbind/templates/reverse_zone.jinja
    - user: named
    - group: named
    - mode: 644
    - defaults:
        zone: "{{ zone }}"
        reverse_zone: "{{ reverse_zone }}"
        view: "{{ view }}"
{% endfor -%}
{% endfor -%}
