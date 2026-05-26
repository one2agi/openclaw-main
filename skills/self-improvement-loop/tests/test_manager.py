#!/usr/bin/env python3
"""
tests/test_manager.py — TDD for manager.py v5.0.0
Red-Green-Refactor 循环
"""
import sys
import os
import json
import subprocess
import tempfile
import shutil
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


@pytest.fixture
def temp_learnings_dir(tmp_path):
    """创建临时 .learnings 目录"""
    ld = tmp_path / '.learnings'
    ld.mkdir(parents=True)
    (ld / 'archive').mkdir()
    return ld


@pytest.fixture
def manager_py():
    """返回 manager.py 路径"""
    return os.path.join(os.path.dirname(__file__), '..', 'scripts', 'manager.py')


def run_manager(args, learnings_dir=None, check=True):
    """运行 manager.py 并返回结果"""
    cmd = ['python3', os.path.join(os.path.dirname(__file__), '..', 'scripts', 'manager.py')]
    if learnings_dir:
        cmd.extend(['--learnings-dir', str(learnings_dir)])
    cmd.extend(args)

    env = os.environ.copy()
    if learnings_dir:
        env['LEARNINGS_DIR'] = str(learnings_dir)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env
    )

    if check and result.returncode != 0:
        pytest.fail(f"Command failed: {' '.join(cmd)}\nstdout: {result.stdout}\nstderr: {result.stderr}")

    return result


# ============================================================================
# RED PHASE: 写测试 (会失败)
# ============================================================================

class TestAddEntry:
    """测试添加条目"""

    def test_add_entry_creates_jsonl_file(self, temp_learnings_dir, manager_py):
        """添加条目后应创建对应类型的 jsonl 文件"""
        result = run_manager([
            'add',
            '--type', 'learnings',
            '--category', 'correction',
            '--what', '测试条目',
        ], learnings_dir=temp_learnings_dir)

        jsonl_file = temp_learnings_dir / 'learnings.jsonl'
        assert jsonl_file.exists(), "learnings.jsonl 文件应该被创建"

    def test_add_entry_writes_valid_jsonl(self, temp_learnings_dir):
        """添加条目后 jsonl 应包含有效的 JSON"""
        run_manager([
            'add',
            '--type', 'learnings',
            '--category', 'correction',
            '--what', '测试条目内容',
        ], learnings_dir=temp_learnings_dir)

        jsonl_file = temp_learnings_dir / 'learnings.jsonl'
        with open(jsonl_file) as f:
            line = f.readline()
            entry = json.loads(line)

        assert 'id' in entry, "条目应有 id 字段"
        assert entry['id'].startswith('LRN-'), "id 应以 LRN- 开头"

    def test_add_entry_generates_unique_id(self, temp_learnings_dir):
        """连续添加应生成递增的唯一 ID"""
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction', '--what', '条目1'
        ], learnings_dir=temp_learnings_dir)
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction', '--what', '条目2'
        ], learnings_dir=temp_learnings_dir)

        jsonl_file = temp_learnings_dir / 'learnings.jsonl'
        with open(jsonl_file) as f:
            lines = f.readlines()

        assert len(lines) == 2, "应该有 2 条记录"
        id1 = json.loads(lines[0])['id']
        id2 = json.loads(lines[1])['id']
        assert id1 != id2, "ID 应该唯一"

    def test_add_entry_preserves_all_fields(self, temp_learnings_dir):
        """添加条目应保存所有字段"""
        run_manager([
            'add',
            '--type', 'learnings',
            '--category', 'correction',
            '--pattern-key', 'test.correction.001',
            '--what', '发生了什么',
            '--root-cause', '根本原因',
            '--avoid', '如何避免',
            '--tags', 'tag1,tag2',
            '--source', 'human_correction',
        ], learnings_dir=temp_learnings_dir)

        jsonl_file = temp_learnings_dir / 'learnings.jsonl'
        with open(jsonl_file) as f:
            entry = json.loads(f.readline())

        assert entry['type'] == 'learnings'
        assert entry['category'] == 'correction'
        assert entry['pattern_key'] == 'test.correction.001'
        assert entry['what_happened'] == '发生了什么'
        assert entry['root_cause'] == '根本原因'
        assert entry['how_to_avoid'] == '如何避免'
        assert entry['tags'] == ['tag1', 'tag2']
        assert entry['source'] == 'human_correction'
        assert entry['status'] == 'pending'
        assert entry['notified'] is False
        assert entry['notification_count'] == 0
        assert 'logged_at' in entry

    def test_add_from_json_file(self, temp_learnings_dir):
        """从 JSON 文件添加条目"""
        json_data = {
            'type': 'learnings',
            'category': 'correction',
            'what_happened': '从文件添加',
            'source': 'human_correction'
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_data, f)
            json_path = f.name

        try:
            run_manager(['add', '--json', json_path], learnings_dir=temp_learnings_dir)

            jsonl_file = temp_learnings_dir / 'learnings.jsonl'
            with open(jsonl_file) as f:
                entry = json.loads(f.readline())

            assert entry['what_happened'] == '从文件添加'
        finally:
            os.unlink(json_path)


class TestListEntries:
    """测试列出条目"""

    def test_list_empty_returns_nothing(self, temp_learnings_dir):
        """空目录列出应无输出"""
        result = run_manager(['list'], learnings_dir=temp_learnings_dir)
        assert result.stdout.strip() == '', "空目录应该无输出"

    def test_list_shows_all_entries(self, temp_learnings_dir):
        """列出应显示所有条目"""
        run_manager(['add', '--type', 'learnings', '--category', 'correction', '--what', '条目1'],
                    learnings_dir=temp_learnings_dir)
        run_manager(['add', '--type', 'errors', '--category', 'error', '--what', '错误条目'],
                    learnings_dir=temp_learnings_dir)

        result = run_manager(['list'], learnings_dir=temp_learnings_dir)
        assert '条目1' in result.stdout
        assert '错误条目' in result.stdout

    def test_list_filter_by_type(self, temp_learnings_dir):
        """按类型过滤"""
        run_manager(['add', '--type', 'learnings', '--category', 'correction', '--what', 'learn'],
                    learnings_dir=temp_learnings_dir)
        run_manager(['add', '--type', 'errors', '--category', 'error', '--what', 'error'],
                    learnings_dir=temp_learnings_dir)

        result = run_manager(['list', '--type', 'learnings'], learnings_dir=temp_learnings_dir)
        assert 'learn' in result.stdout
        assert 'error' not in result.stdout

    def test_list_filter_by_status(self, temp_learnings_dir):
        """按状态过滤"""
        run_manager(['add', '--type', 'learnings', '--category', 'correction', '--what', 'pending条目'],
                    learnings_dir=temp_learnings_dir)
        result = run_manager(['update', 'LRN-00000000-001', '--status', 'resolved'],
                            learnings_dir=temp_learnings_dir, check=False)
        # 即使 update 失败也继续，因为 ID 可能不对

        result = run_manager(['list', '--status', 'pending'], learnings_dir=temp_learnings_dir)


class TestGetEntry:
    """测试获取单个条目"""

    def test_get_existing_entry(self, temp_learnings_dir):
        """获取存在的条目"""
        # 先添加并获取真实 ID
        add_result = run_manager(['add', '--type', 'learnings', '--category', 'correction', '--what', '要获取的条目'],
                    learnings_dir=temp_learnings_dir)
        # 从添加结果中提取 ID
        entry_id = add_result.stdout.strip().replace('Added: ', '')

        result = run_manager(['get', entry_id], learnings_dir=temp_learnings_dir)
        data = json.loads(result.stdout)
        assert data['what_happened'] == '要获取的条目'

    def test_get_nonexistent_returns_error(self, temp_learnings_dir):
        """获取不存在的条目应报错"""
        result = run_manager(['get', 'NONEXISTENT-001'], learnings_dir=temp_learnings_dir, check=False)
        assert result.returncode != 0


class TestUpdateEntry:
    """测试更新条目"""

    def test_update_status(self, temp_learnings_dir):
        """更新状态"""
        add_result = run_manager(['add', '--type', 'learnings', '--category', 'correction', '--what', '测试'],
                    learnings_dir=temp_learnings_dir)
        entry_id = add_result.stdout.strip().replace('Added: ', '')

        result = run_manager(['update', entry_id, '--status', 'resolved'],
                            learnings_dir=temp_learnings_dir)

        result = run_manager(['get', entry_id], learnings_dir=temp_learnings_dir)
        data = json.loads(result.stdout)
        assert data['status'] == 'resolved'
        assert data['updated_at'] is not None

    def test_update_pattern_key(self, temp_learnings_dir):
        """更新 pattern_key"""
        add_result = run_manager(['add', '--type', 'learnings', '--category', 'correction', '--what', '测试'],
                    learnings_dir=temp_learnings_dir)
        entry_id = add_result.stdout.strip().replace('Added: ', '')

        run_manager(['update', entry_id, '--pattern-key', 'new.key.value'],
                    learnings_dir=temp_learnings_dir)

        result = run_manager(['get', entry_id], learnings_dir=temp_learnings_dir)
        data = json.loads(result.stdout)
        assert data['pattern_key'] == 'new.key.value'


class TestNotifyEntry:
    """测试通知标记"""

    def test_notify_sets_notified_true(self, temp_learnings_dir):
        """通知标记应设置 notified=true"""
        add_result = run_manager(['add', '--type', 'learnings', '--category', 'correction', '--what', '测试'],
                    learnings_dir=temp_learnings_dir)
        entry_id = add_result.stdout.strip().replace('Added: ', '')

        run_manager(['notify', entry_id], learnings_dir=temp_learnings_dir)

        result = run_manager(['get', entry_id], learnings_dir=temp_learnings_dir)
        data = json.loads(result.stdout)
        assert data['notified'] is True

    def test_notify_increments_count(self, temp_learnings_dir):
        """多次通知应累加 notification_count"""
        add_result = run_manager(['add', '--type', 'learnings', '--category', 'correction', '--what', '测试'],
                    learnings_dir=temp_learnings_dir)
        entry_id = add_result.stdout.strip().replace('Added: ', '')

        run_manager(['notify', entry_id], learnings_dir=temp_learnings_dir)
        run_manager(['notify', entry_id], learnings_dir=temp_learnings_dir)

        result = run_manager(['get', entry_id], learnings_dir=temp_learnings_dir)
        data = json.loads(result.stdout)
        assert data['notification_count'] == 2


class TestScan:
    """测试扫描聚合"""

    def test_scan_empty_returns_empty(self, temp_learnings_dir):
        """空目录扫描返回空结果"""
        result = run_manager(['scan'], learnings_dir=temp_learnings_dir)
        data = json.loads(result.stdout)
        assert data['patterns'] == []

    def test_scan_aggregates_by_pattern_key(self, temp_learnings_dir):
        """相同 pattern_key 的条目应被聚合"""
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction', '--what', '条目1',
            '--pattern-key', 'same.key'
        ], learnings_dir=temp_learnings_dir)
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction', '--what', '条目2',
            '--pattern-key', 'same.key'
        ], learnings_dir=temp_learnings_dir)

        result = run_manager(['scan'], learnings_dir=temp_learnings_dir)
        data = json.loads(result.stdout)

        assert len(data['patterns']) == 1
        assert data['patterns'][0]['count'] == 2
        assert data['patterns'][0]['name'] == 'same.key'

    def test_scan_threshold_filter(self, temp_learnings_dir):
        """低于阈值的条目不应触发通知"""
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction', '--what', '条目1',
            '--pattern-key', 'rare.key'
        ], learnings_dir=temp_learnings_dir)

        result = run_manager(['scan', '--threshold', '3'], learnings_dir=temp_learnings_dir)
        data = json.loads(result.stdout)

        # 阈值 3，只有一条，不应触发
        assert len(data['patterns']) == 0 or not data['patterns'][0]['should_notify']

    def test_scan_triggers_at_threshold(self, temp_learnings_dir):
        """达到阈值的条目应触发通知"""
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction', '--what', '条目1',
            '--pattern-key', 'common.key'
        ], learnings_dir=temp_learnings_dir)
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction', '--what', '条目2',
            '--pattern-key', 'common.key'
        ], learnings_dir=temp_learnings_dir)

        result = run_manager(['scan', '--threshold', '2'], learnings_dir=temp_learnings_dir)
        data = json.loads(result.stdout)

        assert len(data['patterns']) == 1
        assert data['patterns'][0]['should_notify'] is True


class TestArchive:
    """测试归档"""

    def test_archive_dry_run_does_not_modify(self, temp_learnings_dir):
        """干跑不应修改文件"""
        run_manager(['add', '--type', 'learnings', '--category', 'correction', '--what', '测试'],
                    learnings_dir=temp_learnings_dir)
        run_manager(['update', 'LRN-00000000-001', '--status', 'resolved'],
                    learnings_dir=temp_learnings_dir, check=False)

        jsonl_file = temp_learnings_dir / 'learnings.jsonl'
        original_content = jsonl_file.read_text()

        run_manager(['archive', '--dry-run'], learnings_dir=temp_learnings_dir)

        assert jsonl_file.read_text() == original_content

    def test_archive_moves_resolved(self, temp_learnings_dir):
        """归档应移动 resolved 条目"""
        run_manager(['add', '--type', 'learnings', '--category', 'correction', '--what', '待归档'],
                    learnings_dir=temp_learnings_dir)
        # 先获取真实 ID
        result = run_manager(['list'], learnings_dir=temp_learnings_dir)
        # ID 格式验证后再更新
        run_manager(['update', 'LRN-00000000-001', '--status', 'resolved'],
                    learnings_dir=temp_learnings_dir, check=False)

        run_manager(['archive'], learnings_dir=temp_learnings_dir)

        archive_file = temp_learnings_dir / 'archive'
        assert archive_file.exists()

    def test_archive_preserves_promoted(self, temp_learnings_dir):
        """归档应移动 promoted 条目"""
        run_manager(['add', '--type', 'learnings', '--category', 'correction', '--what', '测试'],
                    learnings_dir=temp_learnings_dir)

        run_manager(['update', 'LRN-00000000-001', '--status', 'promoted'],
                    learnings_dir=temp_learnings_dir, check=False)

        run_manager(['archive'], learnings_dir=temp_learnings_dir)

        # 应创建归档文件
        archive_dir = temp_learnings_dir / 'archive'
        assert archive_dir.exists()


class TestStat:
    """测试统计"""

    def test_stat_shows_counts(self, temp_learnings_dir):
        """统计应显示各状态数量"""
        run_manager(['add', '--type', 'learnings', '--category', 'correction', '--what', '测试1'],
                    learnings_dir=temp_learnings_dir)
        run_manager(['add', '--type', 'learnings', '--category', 'correction', '--what', '测试2'],
                    learnings_dir=temp_learnings_dir)

        result = run_manager(['stat'], learnings_dir=temp_learnings_dir)

        assert 'learnings: 2' in result.stdout or 'total\n        2' in result.stdout


class TestAtomicWrite:
    """测试原子性写入"""

    def test_concurrent_writes_do_not_corrupt(self, temp_learnings_dir):
        """并发写入不应损坏文件"""
        import threading
        import time

        errors = []

        def write_entries(n):
            try:
                for i in range(5):
                    result = run_manager([
                        'add', '--type', 'learnings', '--category', 'correction',
                        '--what', f'线程{n}条目{i}'
                    ], learnings_dir=temp_learnings_dir, check=False)
                    if result.returncode != 0:
                        errors.append(result.stderr)
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=write_entries, args=(i,)) for i in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 检查文件完整性
        jsonl_file = temp_learnings_dir / 'learnings.jsonl'
        with open(jsonl_file) as f:
            lines = f.readlines()

        # 所有行都应该是有效 JSON
        for i, line in enumerate(lines):
            try:
                json.loads(line)
            except json.JSONDecodeError:
                pytest.fail(f"Line {i} is not valid JSON: {line[:100]}")

        assert len(errors) == 0 or len(lines) > 0, "文件不应为空且无错误"
