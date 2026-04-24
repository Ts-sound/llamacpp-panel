from src.models.monitor import GPUStats, MemoryStats


class TestMemoryStats:
    def test_instantiation_all_fields(self):
        s = MemoryStats(total=16000000000, available=8000000000, percent=50.0, used=8000000000)
        assert s.total == 16000000000
        assert s.available == 8000000000
        assert s.percent == 50.0
        assert s.used == 8000000000

    def test_dataclass_equality(self):
        a = MemoryStats(total=100, available=50, percent=50.0, used=50)
        b = MemoryStats(total=100, available=50, percent=50.0, used=50)
        assert a == b

    def test_zero_values(self):
        s = MemoryStats(total=0, available=0, percent=0.0, used=0)
        assert s.total == 0
        assert s.percent == 0.0

    def test_full_usage(self):
        s = MemoryStats(total=1000, available=0, percent=100.0, used=1000)
        assert s.percent == 100.0
        assert s.available == 0

    def test_dataclass_repr(self):
        s = MemoryStats(total=100, available=80, percent=20.0, used=20)
        r = repr(s)
        assert "MemoryStats" in r
        assert "total" in r

    def test_dataclass_fields_mutable(self):
        s = MemoryStats(total=100, available=80, percent=20.0, used=20)
        s.percent = 40.0
        assert s.percent == 40.0

    def test_replace(self):
        from dataclasses import replace

        s = MemoryStats(total=100, available=80, percent=20.0, used=20)
        s2 = replace(s, percent=80.0, available=20, used=80)
        assert s2.percent == 80.0
        assert s2.total == 100


class TestGPUStats:
    def test_default_values(self):
        s = GPUStats()
        assert s.total is None
        assert s.used is None
        assert s.percent is None

    def test_instantiation_with_values(self):
        s = GPUStats(total=8589934592, used=4294967296, percent=50.0)
        assert s.total == 8589934592
        assert s.used == 4294967296
        assert s.percent == 50.0

    def test_partial_values(self):
        s = GPUStats(total=8589934592)
        assert s.total == 8589934592
        assert s.used is None
        assert s.percent is None

    def test_zero_gpu(self):
        s = GPUStats(total=0, used=0, percent=0.0)
        assert s.total == 0
        assert s.percent == 0.0

    def test_dataclass_equality(self):
        a = GPUStats(total=100, used=50, percent=50.0)
        b = GPUStats(total=100, used=50, percent=50.0)
        assert a == b

    def test_none_inequality(self):
        a = GPUStats()
        b = GPUStats(total=100)
        assert a != b

    def test_dataclass_repr(self):
        s = GPUStats(total=100, used=50, percent=50.0)
        r = repr(s)
        assert "GPUStats" in r

    def test_replace_defaults(self):
        from dataclasses import replace

        s = GPUStats()
        s2 = replace(s, total=1024, used=512, percent=50.0)
        assert s2.total == 1024
        assert s.used is None
