import pkg_resources

lcwc_version = None

def get_lcwc_version():
    global lcwc_version
    if not lcwc_version:
        lcwc_version = pkg_resources.get_distribution("lcwc").version
    return lcwc_version