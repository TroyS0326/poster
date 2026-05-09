import json
from pathlib import Path

from reels import scheduler


def _queue(tmp_path: Path):
    q = tmp_path / 'q.json'
    q.write_text(json.dumps({"output_root":"outputs/queue","runs":[{"run_id":"day_01","items":[{"topic":"A","slug":"a"},{"topic":"B","slug":"b"}]}]}))
    return q


def test_once_processes_one_item(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    calls=[]
    monkeypatch.setattr(scheduler, 'run_autopost', lambda *args, **kwargs: calls.append(kwargs.get('limit')) or {"items":[{"publish":{}}]})
    scheduler.run_scheduler(_queue(tmp_path), 'https://x', once=True, dry_run=True)
    assert len(calls)==1 and calls[0]==1


def test_state_prevents_duplicate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    q=_queue(tmp_path)
    count={"n":0}
    def _auto(*args, **kwargs):
        count['n']+=1
        return {"items":[{"publish":{}}]}
    monkeypatch.setattr(scheduler, 'run_autopost', _auto)
    scheduler.run_scheduler(q, 'https://x', once=True, dry_run=True)
    scheduler.run_scheduler(q, 'https://x', once=True, dry_run=True)
    assert count['n']==2


def test_interval_sleep_called(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(scheduler, 'run_autopost', lambda *args, **kwargs: {"items":[{"publish":{}}]})
    slept={"v":None}
    monkeypatch.setattr(scheduler.time, 'sleep', lambda v: slept.__setitem__('v', v) or (_ for _ in ()).throw(SystemExit()))
    try:
        scheduler.run_scheduler(_queue(tmp_path), 'https://x', once=False, dry_run=True, interval_hours=0.01)
    except SystemExit:
        pass
    assert slept['v'] == 36.0
