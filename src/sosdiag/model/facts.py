from typing import Literal

from pydantic import BaseModel

SelinuxMode = Literal["Disabled", "Permissive", "Enforcing"]


class SelinuxFacts(BaseModel):
    rhel_major: int | None = None
    runtime_mode: SelinuxMode | None = None
    configured_mode: SelinuxMode | None = None
    runtime_config_mismatch: bool | None = None
    runtime_source: str | None = None
    configured_source: str | None = None
    kernel_cmdline: str | None = None
    kernel_selinux_disabled: bool | None = None
    kernel_cmdline_source: str | None = None

    @property
    def has_usable_state(self) -> bool:
        if self.rhel_major is not None and self.rhel_major >= 9:
            return self.kernel_selinux_disabled is not None
        return self.runtime_mode is not None or self.configured_mode is not None
