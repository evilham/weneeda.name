from twisted.names import authority, dns


class DNSEchoRecordProducer:
    def __init__(self, base, ns_name):
        self.base = base
        self.ns_name = ns_name

    def get(self, name, default=tuple()):
        # Return NS entries
        print("Original", name)
        if name == self.base:
            return (dns.Record_NS(self.base, self.ns_name),)

        if not name.endswith(self.base):
            return default

        # Remove base name
        local_name = name[: -len(self.base)]

        # Ensure trailing dot and 4 "numbers" before
        if local_name[-1:] != b"." or len(local_name.split(b".")) != 5:
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
    _ADDRESS_TYPES = (dns.A,)

    def __init__(self, base, ns_name):
        self.ns_name = ns_name
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

        self.records = DNSEchoRecordProducer(self.base, self.ns_name)
