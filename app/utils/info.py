import pkg_resources

lcwc_dist = None


def get_lcwc_version():
    if not lcwc_dist:
        get_lcwc_dist()
    return lcwc_dist.version


def get_lcwc_dist():
    global lcwc_dist
    if not lcwc_dist:
        lcwc_dist = pkg_resources.get_distribution("lcwc")
    return lcwc_dist
