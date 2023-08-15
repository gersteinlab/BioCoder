def parse_requirements(requirements):
    """Parse a requirement into a module and version parts."""
    reqs = {}
    for req in requirements.splitlines():
        match = re.match('^([^>=<]+)([>=<]+)([^>=<]+)$', req)
        module = match.group(1)
        compare = match.group(2)
        version = LooseVersion(match.group(3))
        reqs[module] = {'compare': compare, 'version': version}
    return reqs