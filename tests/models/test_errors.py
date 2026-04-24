import pytest

from src.models.errors import ConfigError, ProcessError, SSHError


class TestProcessError:
    def test_basic_message(self):
        err = ProcessError("something failed")
        assert str(err) == "something failed"
        assert err.exit_code is None
        assert err.stderr is None

    def test_with_exit_code(self):
        err = ProcessError("crashed", exit_code=1)
        assert str(err) == "crashed"
        assert err.exit_code == 1
        assert err.stderr is None

    def test_with_stderr(self):
        err = ProcessError("crashed", exit_code=2, stderr="error output")
        assert err.exit_code == 2
        assert err.stderr == "error output"

    def test_is_exception(self):
        err = ProcessError("fail")
        assert isinstance(err, Exception)

    def test_all_none(self):
        err = ProcessError("msg", exit_code=None, stderr=None)
        assert err.exit_code is None
        assert err.stderr is None

    def test_zero_exit_code(self):
        err = ProcessError("exited", exit_code=0)
        assert err.exit_code == 0


class TestSSHError:
    def test_basic(self):
        err = SSHError("connection refused")
        assert str(err) == "connection refused"
        assert err.message == "connection refused"

    def test_is_exception(self):
        err = SSHError("fail")
        assert isinstance(err, Exception)

    def test_empty_message(self):
        err = SSHError("")
        assert err.message == ""

    def test_message_attribute(self):
        msg = "SSH process failed"
        err = SSHError(msg)
        assert err.message is msg


class TestConfigError:
    def test_basic(self):
        err = ConfigError("invalid config")
        assert str(err) == "invalid config"
        assert err.message == "invalid config"

    def test_is_exception(self):
        err = ConfigError("fail")
        assert isinstance(err, Exception)

    def test_detailed_message(self):
        msg = "Failed to save config: Permission denied"
        err = ConfigError(msg)
        assert err.message == msg

    def test_empty_message(self):
        err = ConfigError("")
        assert err.message == ""


class TestExceptionHierarchy:
    def test_all_inherit_exception(self):
        assert issubclass(ProcessError, Exception)
        assert issubclass(SSHError, Exception)
        assert issubclass(ConfigError, Exception)

    def test_can_be_caught_as_exception(self):
        with pytest.raises(Exception):
            raise ProcessError("p")
        with pytest.raises(Exception):
            raise SSHError("s")
        with pytest.raises(Exception):
            raise ConfigError("c")

    def test_can_catch_specific_type(self):
        with pytest.raises(ProcessError):
            raise ProcessError("p")
        with pytest.raises(SSHError):
            raise SSHError("s")
        with pytest.raises(ConfigError):
            raise ConfigError("c")

    def test_errors_are_distinct(self):
        assert ProcessError is not SSHError
        assert SSHError is not ConfigError
        assert ProcessError is not ConfigError
