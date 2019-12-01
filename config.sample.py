from ipaddress import ip_network

from dnsecho import DNSEchoAuthority
from dnswords import DNSWordsAuthority, WordsController
from twisted.names import dns

# Example config, copy to config.py and adapt to your needs.
# This is terrible though, please consider adding a PR :-D
#
# That being said, only required keys in config are:
#   zones: a list of Authorities (e.g. DNSEchoAutority and DNSWordsAuthority)
#   dnsport: a TCP/UDP port to listen to for DNS requests
#   dnsinterface: binding addresses to listen to for DNS requests
#   verbose: verbosity level for the DNS bits of twisted (e.g. 2)
#   apiendpoint: only required when a zone is registered to WordsController
#     See Twisted Endpoints:
#       https://twistedmatrix.com/documents/current/api/twisted.internet.endpoints.html
#
# TODO: Make configuration prettier

config = {
    "zones": [
        DNSEchoAuthority(b"echo4.dnslab.evilham.com", b"yggdrasil.evilham.com"),
        DNSWordsAuthority(
            b"yggdrasil.ungleich.cloud",
            b"ns1-yggdrasil.ungleich.cloud",
            extra_records=(dns.Record_AAAA("2a0a:e5c0:0:5:0:78ff:fe11:d762"),),
        ),
    ],
    "apiendpoint": b"tcp6:8080",
    "verbose": 2,
    "dnsport": 5353,
    "dnsinterface": "::",
}

# Notice as well that you must register any zones to WordsController yourself
WordsController.register_zone(b"yggdrasil.ungleich.cloud", ip_network("0200::/7"))

# If you are proxying this service, uncomment following in order to trust
# X-Forwarded-For headers.
# WordsController.proxied = True
