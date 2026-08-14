from sosdiag.parser.selinux import parse_selinux


def test_parse_disabled_runtime_and_config():
    facts = parse_selinux(
        {
            "getenforce": "Disabled\n",
            "config": "SELINUX=disabled\nSELINUXTYPE=targeted\n",
        }
    )

    assert facts.runtime_mode == "Disabled"
    assert facts.configured_mode == "Disabled"
    assert facts.runtime_config_mismatch is False


def test_parse_enforcing_with_disabled_config_reports_mismatch():
    facts = parse_selinux(
        {
            "sestatus": "SELinux status: enabled\nCurrent mode: enforcing\n",
            "config": "# comment\nSELINUX=disabled\n",
        }
    )

    assert facts.runtime_mode == "Enforcing"
    assert facts.configured_mode == "Disabled"
    assert facts.runtime_config_mismatch is True


def test_command_error_is_rejected():
    facts = parse_selinux(
        {
            "getenforce": "bash: getenforce: command not found\n",
            "sestatus": "",
            "config": None,
        }
    )

    assert facts.runtime_mode is None
    assert facts.configured_mode is None
    assert facts.has_usable_state is False
