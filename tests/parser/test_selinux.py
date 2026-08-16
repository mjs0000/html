from sosdiag.parser.selinux import parse_selinux


def test_parse_disabled_runtime_and_config():
    facts = parse_selinux(
        {
            "os_release": "Red Hat Enterprise Linux release 8.10 (Ootpa)\n",
            "getenforce": "Disabled\n",
            "config": "SELINUX=disabled\nSELINUXTYPE=targeted\n",
        }
    )

    assert facts.rhel_major == 8
    assert facts.runtime_mode == "Disabled"
    assert facts.configured_mode == "Disabled"
    assert facts.runtime_config_mismatch is False


def test_parse_enforcing_with_disabled_config_reports_mismatch():
    facts = parse_selinux(
        {
            "os_release": "Red Hat Enterprise Linux release 8.10 (Ootpa)\n",
            "sestatus": "SELinux status: enabled\nCurrent mode: enforcing\n",
            "config": "# comment\nSELINUX=disabled\n",
        }
    )

    assert facts.runtime_mode == "Enforcing"
    assert facts.configured_mode == "Disabled"
    assert facts.runtime_config_mismatch is True


def test_parse_rhel9_cmdline_with_selinux_zero():
    facts = parse_selinux(
        {
            "os_release": "Red Hat Enterprise Linux release 9.6 (Plow)\n",
            "cmdline": "BOOT_IMAGE=/vmlinuz root=/dev/mapper/root ro selinux=0 quiet\n",
            "getenforce": "Disabled\n",
            "config": "SELINUX=disabled\n",
        }
    )

    assert facts.rhel_major == 9
    assert facts.kernel_selinux_disabled is True
    assert facts.kernel_cmdline_source == "/proc/cmdline"


def test_parse_rhel9_cmdline_without_selinux_zero():
    facts = parse_selinux(
        {
            "os_release": 'NAME="Red Hat Enterprise Linux"\nVERSION_ID="9.6"\n',
            "cmdline": "BOOT_IMAGE=/vmlinuz root=/dev/mapper/root ro quiet\n",
        }
    )

    assert facts.rhel_major == 9
    assert facts.kernel_selinux_disabled is False


def test_command_error_is_rejected():
    facts = parse_selinux(
        {
            "os_release": "Red Hat Enterprise Linux release 9.6 (Plow)\n",
            "getenforce": "bash: getenforce: command not found\n",
            "sestatus": "",
            "config": None,
            "cmdline": None,
        }
    )

    assert facts.runtime_mode is None
    assert facts.configured_mode is None
    assert facts.kernel_selinux_disabled is None
