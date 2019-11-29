#!/usr/bin/env python3

from twisted.application import internet
from twisted.names import authority, common, dns, error, server

from twisted.internet import defer, reactor, interfaces


class DNSEchoRecordProducer():
    def __init__(self, base, ns_name):
        self.base = base
        self.ns_name = ns_name

    def get(self, name, default=tuple()):
        # Return NS entries
        print('Original', name)
        if name == self.base:
            return (dns.Record_NS(self.base, self.ns_name), )

        if not name.endswith(self.base):
            return default

        # Remove base name
        local_name = name[:-len(self.base)]

        # Ensure trailing dot and 4 "numbers" before
        if local_name[-1:] != b'.' or len(local_name.split(b'.')) != 5:
            return default

        # Remove trailing dot.
        local_name = local_name[:-1]

        try:
            record = dns.Record_A(address=local_name, ttl=604800)
        except:
            return default

        return (record,)


# TODO: Open ticket for twisted.names: this is not generic enough
class DNSEchoAuthority(authority.FileAuthority):
    _ADDITIONAL_PROCESSING_TYPES = tuple()
    _ADDRESS_TYPES = (dns.A, )

    def __init__(self, base, ns_name):
        self.ns_name = ns_name
        super().__init__(base)

    def loadFile(self, base):
        self.base = base

        self.soa = (base, dns.Record_SOA(
            base,
            # mname = self.ns_name,
            # rname = '???',
            serial = '1970010100',
            refresh = '7D',
            expire = '7D',
            minimum = '7D',
            ttl = '7D',
        ))

        self.records = DNSEchoRecordProducer(self.base, self.ns_name)

# TODO: env vars
config = {
    'zones': [DNSEchoAuthority(b'echo4.dnslab.evilham.com', b'yggdrasil.evilham.com')],
    'verbose': 2,
    'resolv-conf': '../resolv.conf',
}

def main():
    from twisted.names import cache, client
    dns_cache   = [cache.CacheResolver(verbose=config['verbose'])]
    #dns_clients = [client.createResolver(resolvconf=config['resolv-conf'])]
    dns_clients = []

    tcp_f = server.DNSServerFactory(
        config['zones'],
        dns_cache,
        dns_clients,
        config['verbose']
    )
    udp_f = dns.DNSDatagramProtocol(tcp_f)

    tcp_s = internet.TCPServer(53, tcp_f, interface='::')
    udp_s = internet.UDPServer(53, udp_f, interface='::')

    tcp_s.startService()
    udp_s.startService()
    print('Starting reactor')

    reactor.run()

if __name__ == '__main__':
    main()
