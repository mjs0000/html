from __future__ import annotations

from pydantic import BaseModel, Field


class BondSlave(BaseModel):
    name: str
    link_state: str | None = None


class BondFacts(BaseModel):
    bond_name: str
    mode: str | None = None
    miimon: int | None = None
    mii_status: str | None = None
    active_slave: str | None = None
    slaves: list[BondSlave] = Field(default_factory=list)
    lacp_rate: str | None = None
    evidence_path: str | None = None


class BondingFacts(BaseModel):
    bonds: list[BondFacts] = Field(default_factory=list)


class NetworkKernelFacts(BaseModel):
    qualifying_interface: str | None = None
    speed_mbps: int | None = None
    link_up: bool | None = None
    configured: bool | None = None
    values: dict[str, int | list[int] | str | None] = Field(default_factory=dict)
    evidence_paths: list[str] = Field(default_factory=list)


class NetworkInterfaceFacts(BaseModel):
    interface_name: str
    connection_name: str | None = None
    connection_type: str | None = None
    master_interface: str | None = None
    configured: bool | None = None
    active_connection: bool | None = None
    carrier: bool | None = None
    operational_state: str | None = None
    speed_mbps: int | None = None
    ipv4_addresses: list[str] = Field(default_factory=list)
    ipv4_gateway: str | None = None
    dns_servers: list[str] = Field(default_factory=list)
    mtu: int | None = None
    autoconnect: bool | None = None
    rx_errors: int | None = None
    rx_dropped: int | None = None
    tx_errors: int | None = None
    tx_dropped: int | None = None


class NetstateFacts(BaseModel):
    networkmanager_enabled: bool | None = None
    networkmanager_active: bool | None = None
    networkmanager_in_use: bool | None = None
    nmcli_evidence_available: bool = False
    interfaces: list[NetworkInterfaceFacts] = Field(default_factory=list)
    evidence_paths: list[str] = Field(default_factory=list)


class MultipathPath(BaseModel):
    device: str | None = None
    hctl: str | None = None
    path_group: str | None = None
    dm_status: str | None = None
    checker_status: str | None = None
    path_status: str | None = None


class MultipathMap(BaseModel):
    map_name: str
    wwid: str | None = None
    vendor: str | None = None
    product: str | None = None
    dm_state: str | None = None
    paths: list[MultipathPath] = Field(default_factory=list)


class MultipathFacts(BaseModel):
    maps: list[MultipathMap] = Field(default_factory=list)
    effective_config_available: bool | None = None
    evidence_paths: list[str] = Field(default_factory=list)
