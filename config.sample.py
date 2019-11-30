from ipaddress import ip_network

from dnsecho import DNSEchoAuthority
from dnswords import DNSWordsAuthority, WordsController

# Example config, copy to config.py and adapt to your needs.
# This is terrible though, please consider adding a PR :-D
#
# That being said, only required keys in config are:
#   zones: a list of Authorities (e.g. DNSEchoAutority and DNSWordsAuthority)
#   verbose: verbosity level for the DNS bits of twisted (e.g. 2)
#   apiendpoint: only required when a zone is registered to WordsController
#     See Twisted Endpoints:
#       https://twistedmatrix.com/documents/current/api/twisted.internet.endpoints.html
#
# TODO: Make configuration prettier

config = {
    "zones": [
        DNSEchoAuthority(b"echo4.dnslab.evilham.com", b"yggdrasil.evilham.com"),
        DNSWordsAuthority(b"yggdrasil.ungleich.cloud", b"yggdrasil.ungleich.cloud"),
    ],
    "apiendpoint": b"tcp6:8080",
    "verbose": 2,
}

# Notice as well that you must register any zones to WordsController yourself
WordsController.register_zone(b"yggdrasil.ungleich.cloud", ip_network("::/0"))
