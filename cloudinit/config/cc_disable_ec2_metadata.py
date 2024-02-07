# Copyright (C) 2009-2010 Canonical Ltd.
# Copyright (C) 2012 Hewlett-Packard Development Company, L.P.
#
# Author: Scott Moser <scott.moser@canonical.com>
# Author: Juerg Haefliger <juerg.haefliger@hp.com>
#
# This file is part of cloud-init. See LICENSE file for license information.

"""Disable EC2 Metadata: Disable AWS EC2 metadata."""

import logging
from textwrap import dedent

from cloudinit import subp, util
from cloudinit.cloud import Cloud
from cloudinit.config import Config
from cloudinit.config.schema import MetaSchema, get_meta_doc
from cloudinit.distros import ALL_DISTROS
from cloudinit.settings import PER_ALWAYS

REJECT_CMDS_IF = [
    ["route", "add", "-host", "169.254.169.254", "reject"],
    ["route", "-6", "add", "-host", "fd00:ec2::254", "reject"],
]
REJECT_CMDS_IP = [
    ["ip", "route", "add", "prohibit", "169.254.169.254"],
    ["ip", "-6", "route", "add", "prohibit", "fd00:ec2::254"],
]

LOG = logging.getLogger(__name__)

meta: MetaSchema = {
    "id": "cc_disable_ec2_metadata",
    "name": "Disable EC2 Metadata",
    "title": "Disable AWS EC2 Metadata",
    "description": dedent(
        """\
        This module can disable the ec2 datasource by rejecting the routes to
        IPv4 metadata URL ``169.254.169.254`` and
        IPv6 metadata URL ``fd00:ec2::254``, the usual route to the datasource.
        This module is disabled by default."""
    ),
    "distros": [ALL_DISTROS],
    "frequency": PER_ALWAYS,
    "examples": ["disable_ec2_metadata: true"],
    "activate_by_schema_keys": ["disable_ec2_metadata"],
}

__doc__ = get_meta_doc(meta)


def handle(name: str, cfg: Config, cloud: Cloud, args: list) -> None:
    disabled = util.get_cfg_option_bool(cfg, "disable_ec2_metadata", False)
    if disabled:
        reject_cmds = []
        if subp.which("ip"):
            reject_cmds = REJECT_CMDS_IP
        elif subp.which("ifconfig"):
            reject_cmds = REJECT_CMDS_IF
        else:
            LOG.error(
                'Neither "route" nor "ip" command found, unable to '
                "manipulate routing table"
            )
            return
        for reject_cmd in reject_cmds:
            subp.subp(reject_cmd, capture=False)
    else:
        LOG.debug(
            "Skipping module named %s, disabling the ec2 route not enabled",
            name,
        )
