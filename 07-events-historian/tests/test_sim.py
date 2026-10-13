import pytest

from evlab.sim import Sim, SimError


class Fake:
    def __init__(self, fail_serve=False):
        self.calls, self.fail_serve = [], fail_serve

    def __call__(self, method, path, body, token):
        self.calls.append((method, path.split("?")[0], token))
        if path == "/v1/request":
            return {"id": "w-1", "token": "secret", "trace": {"id": body["trace"]},
                    "machines": [{"name": "m1", "endpoint": "opc.tcp://x:1"}]}
        if path.endswith("/serve"):
            if self.fail_serve:
                raise SimError("serve failed")
            return {"state": "serving"}
        if method == "GET" and path.startswith("/v1/workers/"):
            return {"playback": {"state": "playing", "position_s": 3.0}}
        return {}


def test_worker_is_decommissioned_on_normal_exit():
    fake = Fake()
    with Sim(fake).worker("t1") as w:
        assert w.endpoints == {"m1": "opc.tcp://x:1"} and "secret" not in repr(w)
        assert w.playback()["position_s"] == 3.0
    assert fake.calls[-1] == ("DELETE", "/v1/workers/w-1", "secret")


def test_worker_is_decommissioned_on_error_inside_and_on_failed_serve():
    fake = Fake()
    with pytest.raises(RuntimeError):
        with Sim(fake).worker("t1"):
            raise RuntimeError("boom")
    assert fake.calls[-1][0] == "DELETE"
    fake = Fake(fail_serve=True)
    with pytest.raises(SimError):
        with Sim(fake).worker("t1"):
            pass
    assert fake.calls[-1][0] == "DELETE"


def test_missing_url(monkeypatch):
    from evlab.sim import sim_url
    monkeypatch.delenv("ICE_SIM_URL", raising=False)
    with pytest.raises(SimError, match="ICE_SIM_URL"):
        sim_url()
