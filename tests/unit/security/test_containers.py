"""Tests for container security configuration."""

from shesha.security.containers import DEFAULT_SECURITY, ContainerSecurityConfig


class TestContainerSecurityConfig:
    """Tests for ContainerSecurityConfig."""

    def test_default_drops_all_capabilities(self) -> None:
        """Default config drops all capabilities."""
        config = ContainerSecurityConfig()
        assert config.cap_drop == ["ALL"]

    def test_default_not_privileged(self) -> None:
        """Default config is not privileged."""
        config = ContainerSecurityConfig()
        assert config.privileged is False

    def test_default_network_disabled(self) -> None:
        """Default config has network disabled."""
        config = ContainerSecurityConfig()
        assert config.network_disabled is True

    def test_default_read_only(self) -> None:
        """Default config has read-only root filesystem."""
        config = ContainerSecurityConfig()
        assert config.read_only is True

    def test_default_no_new_privileges(self) -> None:
        """Default config prevents gaining new privileges."""
        config = ContainerSecurityConfig()
        assert "no-new-privileges:true" in config.security_opt

    def test_to_docker_kwargs(self) -> None:
        """Converts to docker-py kwargs correctly."""
        config = ContainerSecurityConfig()
        kwargs = config.to_docker_kwargs()
        assert kwargs["cap_drop"] == ["ALL"]
        assert kwargs["privileged"] is False
        assert kwargs["network_disabled"] is True
        assert kwargs["read_only"] is True
        assert "no-new-privileges:true" in kwargs["security_opt"]

    def test_custom_config(self) -> None:
        """Custom configuration overrides defaults."""
        config = ContainerSecurityConfig(
            cap_drop=["NET_ADMIN"],
            network_disabled=False,
        )
        assert config.cap_drop == ["NET_ADMIN"]
        assert config.network_disabled is False

    def test_default_security_singleton(self) -> None:
        """DEFAULT_SECURITY is a pre-configured instance."""
        assert DEFAULT_SECURITY.cap_drop == ["ALL"]
        assert DEFAULT_SECURITY.privileged is False
