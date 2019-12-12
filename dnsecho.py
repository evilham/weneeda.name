import sys
from ipaddress import ip_address

import twisted.logger as logger
from twisted.names import authority, dns


log = logger.Logger(observer=logger.textFileLogObserver(sys.stdout))


class DNSEchoRecordProducer(object):
    def __init__(self, base, ns_name, extra_records):
        self.base = base
        self.ns_name = ns_name
        self.extra_records = extra_records

    def get(self, name, default=tuple()):
        # Return NS entries
        log.info("Original '{name}'", name=name)
        if name == self.base:
            return (dns.Record_NS(self.base, ttl=604800),) + self.extra_records

        if not name.endswith(self.base):
            return default

        try:
            # Remove base name and trailing dot
            local_name = name[:-len(self.base) - 1]
            # ip_address handles bytes as a big integer, need str
            _name = local_name.decode('utf-8')
            # Try to handle other representations for IPv6
            if "-" in _name or _name.count(".") > 3:
                _name = _name.replace("-", ":").replace(".", ":")
            # Try to read an IP address out of this
            ip = ip_address(_name)
        except:
            # If any of that goes wrong, return NX
            return default

        try:
            if ip.version == 6:
                record = dns.Record_AAAA(address=ip.exploded, ttl=604800)
            elif ip.version == 4:
                record = dns.Record_A(address=ip.exploded, ttl=604800)
            else:
                raise NotImplementedError("What's dis? v8?")
        except:
            return default

        return (record,)


# TODO: Open ticket for twisted.names: this is not generic enough
class DNSEchoAuthority(authority.FileAuthority):
    _ADDITIONAL_PROCESSING_TYPES = tuple()
    _ADDRESS_TYPES = (dns.A, dns.AAAA)

    def __init__(self, base, ns_name, extra_records=tuple()):
        self.ns_name = ns_name
        self.extra_records = extra_records
        super().__init__(base)

    def loadFile(self, base):
        self.base = base

        self.soa = (
            base,
            dns.Record_SOA(
                base,
                # mname = self.ns_name,
                # rname = '???',
                serial="1970010100",
                refresh="7D",
                expire="7D",
                minimum="7D",
                ttl="7D",
            ),
        )

        self.records = DNSEchoRecordProducer(
            self.base, self.ns_name, self.extra_records
        )
