# This file is part of cloud-init. See LICENSE file for license information.

"""Tests cc_disable_ec2_metadata handler"""


import pytest

import cloudinit.config.cc_disable_ec2_metadata as ec2_meta
from cloudinit.config.schema import (
    SchemaValidationError,
    get_schema,
    validate_cloudconfig_schema,
)
from tests.unittests.helpers import CiTestCase, mock, skipUnlessJsonSchema

DISABLE_CFG = {"disable_ec2_metadata": "true"}


class TestEC2MetadataRoute(CiTestCase):
    @mock.patch("cloudinit.config.cc_disable_ec2_metadata.subp.which")
    @mock.patch("cloudinit.config.cc_disable_ec2_metadata.subp.subp")
    def test_disable_ifconfig(self, m_subp, m_which):
        """Set the route if ifconfig command is available"""
        m_which.side_effect = lambda x: x if x == "ifconfig" else None
        ec2_meta.handle("foo", DISABLE_CFG, None, None)
        REJECT_CMDS_IF = [
            mock.call(
                ["route", "add", "-host", "169.254.169.254", "reject"],
                capture=False,
            ),
            mock.call(
                ["route", "-6", "add", "-host", "fd00:ec2::254", "reject"],
                capture=False,
            ),
        ]
        m_subp.assert_has_calls(REJECT_CMDS_IF, any_order=False)

    @mock.patch("cloudinit.config.cc_disable_ec2_metadata.subp.which")
    @mock.patch("cloudinit.config.cc_disable_ec2_metadata.subp.subp")
    def test_disable_ip(self, m_subp, m_which):
        """Set the route if ip command is available"""
        m_which.side_effect = lambda x: x if x == "ip" else None
        ec2_meta.handle("foo", DISABLE_CFG, None, None)
        REJECT_CMDS_IP = [
            mock.call(
                ["ip", "route", "add", "prohibit", "169.254.169.254"],
                capture=False,
            ),
            mock.call(
                ["ip", "-6", "route", "add", "prohibit", "fd00:ec2::254"],
                capture=False,
            ),
        ]
        m_subp.assert_has_calls(REJECT_CMDS_IP, any_order=False)

    @mock.patch("cloudinit.config.cc_disable_ec2_metadata.subp.which")
    @mock.patch("cloudinit.config.cc_disable_ec2_metadata.subp.subp")
    def test_disable_no_tool(self, m_subp, m_which):
        """Log error when neither route nor ip commands are available"""
        m_which.return_value = None  # Find neither ifconfig nor ip
        ec2_meta.handle("foo", DISABLE_CFG, None, None)
        self.assertEqual(
            [mock.call("ip"), mock.call("ifconfig")], m_which.call_args_list
        )
        m_subp.assert_not_called()


@skipUnlessJsonSchema()
class TestDisableEc2MetadataSchema:
    """Directly test schema rather than through handle."""

    @pytest.mark.parametrize(
        "config, error_msg",
        (
            # Valid schemas tested by meta.examples in test_schema
            # Invalid schemas
            (
                {"disable_ec2_metadata": 1},
                "disable_ec2_metadata: 1 is not of type 'boolean'",
            ),
        ),
    )
    @skipUnlessJsonSchema()
    def test_schema_validation(self, config, error_msg):
        """Assert expected schema validation and error messages."""
        # New-style schema $defs exist in config/cloud-init-schema*.json
        schema = get_schema()
        with pytest.raises(SchemaValidationError, match=error_msg):
            validate_cloudconfig_schema(config, schema, strict=True)
