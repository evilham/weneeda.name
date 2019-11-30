import sys
from functools import lru_cache
from ipaddress import IPv4Network, IPv6Network, ip_address, ip_network

import twisted.logger as logger
from klein import Klein
from twisted.names import authority, dns
from twisted.python.filepath import FilePath
from twisted.web.resource import ErrorPage, ForbiddenResource

from hashing import hash_parts_generator


log = logger.Logger(observer=logger.textFileLogObserver(sys.stdout))


class _WordsController(object):
    """
    Basic controller that manages registered zones and manages name assignment
    by filtering on the registered IP subnet.
    """

    def __init__(self, data_dir="data", word_count=3):
        self.data_dir = FilePath(data_dir)
        self.word_count = word_count
        self.separator = b"-"
        self.data = dict()

        self.app = Klein()

        # Routing for the HTTP API
        @self.app.route("/")
        def readme(request):
            """
            Public README page
            """
            return self.get_readme()

        @self.app.route("/register")
        def register(request):
            """
            A GET request from a registered zone's subnet is sufficient to
            trigger a name assignment.
            """
            hostname = request.getRequestHostname()
            ip = request.getClientIP()
            return self.register_ip(hostname, ip)

    @lru_cache(10240)
    def get_readme(self):
        return (
            FilePath(self.data_dir.dirname())
            .child("README.md")
            .getContent()
            .decode("utf-8")
        )

    def register_zone(self, zone, subnet):
        """
        Register a zone with the controller along with its allowed subnet.

        @param zone: the DNS zone without any trailing or leading dots.
        @type  zone: C{bytes}

        @param subnet: the subnet that will be allowed to register names.
        @type  subnet: L{ipaddress.ip_network}
        """
        assert isinstance(
            subnet, (IPv4Network, IPv6Network)
        ), "'{}' is not ipaddress.ip_network".format(ip_network)
        log.debug("Registered Zone {zone} | {subnet}", zone=zone, subnet=subnet)
        self.data[zone] = subnet

    def register_ip(self, zone, ip):
        """
        Actually register a name for a given IP.

        @returns: A resource or a byte-string depending on the action being
          successful or not.
          Possible HTTP codes are:
            200 (OK)
            400 (Bad request --> no such zone)
            403 (Forbidden --> out of subnet)
            507 (Insufficient storage --> somehow the name space is kinda full)
        """
        if zone not in self.data:
            return ErrorPage(
                400, "Bad Request", "No such zone, consider hosting your own!"
            )
        try:
            return self.get_assign_name(zone, ip) + b"." + zone + b"\n"
        except ValueError:
            return ForbiddenResource("Your IP is not allowed to use this resource.")
        except LookupError:
            return ErrorPage(
                507,
                "Insufficient Storage",
                "It looks like this zone is getting full. Consider hosting your own!",
            )
        except Exception as ex:
            log.error("Error registering {zone} | {ip}", zone=zone, ip=ip)
            log.failure(ex)
            return ErrorPage(500, "Internal Error", "Something odd happened!")

    @lru_cache(maxsize=1024)
    def get_assign_name(self, zone, ip):
        ipaddr = ip_address(ip)
        # collisions should be handled by iterator
        it = hash_parts_generator(ip, self.word_count, len(self.all_words))
        for h in it:
            words = self.separator.join([self.all_words[i] for i in h])
            record = self.name_to_record(zone, words)
            if record.exists():
                try:
                    record_addr = ip_address(record.getContent().decode("utf-8"))
                    if record_addr == ipaddr:
                        # Already registered
                        return words
                except:
                    # If it contains invalid data, reuse
                    break
            else:
                break
        else:
            raise LookupError("Can't assign name in '{}' for IP '{}'".format(zone, ip))

        record.parent().makedirs(ignoreExistingDirectory=True)
        record.setContent(ipaddr.compressed.encode("utf-8"))

        return words

    @property
    @lru_cache(maxsize=1024)
    def all_words(self):
        """
        Return a list of '\n' separated byte-strings ignoring those lines
        starting with '#'.
        """
        return [
            i
            for i in self.data_dir.child("word_list").getContent().split(b"\n")
            if b"#" not in i
        ]

    def name_to_record(self, zone, words):
        """
        Helper class that returns a FilePath object to the file that should
        contain the resulting IP.
        """
        parts = [zone] + words.split(b"-")
        return self.data_dir.descendant(parts)

    @lru_cache(maxsize=1024)
    def words_to_IP(self, zone, words):
        """
        Get the IP associated with certain words in a zone if registered.
        """
        assert zone, "Empty zone passed"
        record = self.name_to_record(zone, words)
        if record.exists() and record.isfile():
            return ip_address(record.getContent().decode("utf-8"))
        raise ValueError("Name not registered '{}'".format(words))


WordsController = _WordsController()

# TTL = 604800
TTL = 120


class DNSWordsRecordProducer(object):
    """
    Basic DNS record producer that queries the WordsController for the IP
    addresses.
    """

    def __init__(self, base, ns_name):
        self.base = base
        self.ns_name = ns_name

    def get(self, name, default=tuple()):
        # Return NS entries
        if name == self.base:
            return (dns.Record_NS(self.base, self.ns_name),)

        if not name.endswith(self.base):
            return default

        # Remove base name
        local_name = name[: -len(self.base)]

        # Ensure trailing dot
        if local_name[-1:] != b".":
            return default

        # Remove trailing dot.
        local_name = local_name[:-1]

        try:
            address = WordsController.words_to_IP(self.base, local_name)
            log.debug(
                "Got {address} for {name}", address=address, name=name,
            )
            if address.version == 6:
                record = dns.Record_AAAA(address=address.compressed, ttl=TTL)
            elif address.version == 4:
                record = dns.Record_A(address=address.compressed, ttl=TTL)
            else:
                raise NotImplementedError("Unknown version {}".format(address.version))
        except:
            return default

        return (record,)


# TODO: Open ticket for twisted.names: this is not generic enough
class DNSWordsAuthority(authority.FileAuthority):
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

        self.records = DNSWordsRecordProducer(self.base, self.ns_name)
