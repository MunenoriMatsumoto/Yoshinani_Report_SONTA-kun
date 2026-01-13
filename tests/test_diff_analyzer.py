"""差分分析モジュールのテスト"""

import pytest

from sonta_kun.diff_analyzer import DiffAnalyzer, DiffResult, TaskChange
from sonta_kun.excel_reader import TodoItem, TodoList


def test_task_change_dataclass():
    """TaskChangeのテスト"""
    change = TaskChange(
        task_name="タスクA",
        change_type="completed",
        previous_status="進行中",
        current_status="完了",
    )

    assert change.task_name == "タスクA"
    assert change.change_type == "completed"


def test_diff_result_to_text():
    """DiffResultのテキスト変換テスト"""
    result = DiffResult(
        completed_tasks=[TaskChange("タスクA", "completed")],
        new_tasks=[TaskChange("タスクB", "new", current_status="未着手")],
    )
    text = result.to_text()

    assert "完了したタスク" in text
    assert "タスクA" in text
    assert "新規タスク" in text
    assert "タスクB" in text


def test_diff_result_get_summary():
    """DiffResultのサマリテスト"""
    result = DiffResult(
        completed_tasks=[TaskChange("A", "completed"), TaskChange("B", "completed")],
        new_tasks=[TaskChange("C", "new")],
    )
    summary = result.get_summary()

    assert "完了: 2件" in summary
    assert "新規: 1件" in summary


def test_diff_analyzer_no_previous():
    """前回データなしの場合のテスト"""
    analyzer = DiffAnalyzer()
    current = TodoList(
        items=[
            TodoItem(task="タスク1", status="進行中"),
            TodoItem(task="タスク2", status="未着手"),
        ]
    )

    result = analyzer.analyze(current, None)

    assert len(result.new_tasks) == 2
    assert len(result.completed_tasks) == 0


def test_diff_analyzer_completed_task():
    """タスク完了検出テスト"""
    analyzer = DiffAnalyzer()

    previous = TodoList(
        items=[
            TodoItem(task="タスクA", status="進行中"),
            TodoItem(task="タスクB", status="未着手"),
        ]
    )
    current = TodoList(
        items=[
            TodoItem(task="タスクA", status="完了"),
            TodoItem(task="タスクB", status="進行中"),
        ]
    )

    result = analyzer.analyze(current, previous)

    assert len(result.completed_tasks) == 1
    assert result.completed_tasks[0].task_name == "タスクA"
    assert len(result.modified_tasks) == 1
    assert result.modified_tasks[0].task_name == "タスクB"


def test_diff_analyzer_new_task():
    """新規タスク検出テスト"""
    analyzer = DiffAnalyzer()

    previous = TodoList(items=[TodoItem(task="既存タスク", status="進行中")])
    current = TodoList(
        items=[
            TodoItem(task="既存タスク", status="進行中"),
            TodoItem(task="新規タスク", status="未着手"),
        ]
    )

    result = analyzer.analyze(current, previous)

    assert len(result.new_tasks) == 1
    assert result.new_tasks[0].task_name == "新規タスク"


def test_diff_analyzer_removed_task():
    """削除タスク検出テスト"""
    analyzer = DiffAnalyzer()

    previous = TodoList(
        items=[
            TodoItem(task="タスクA", status="進行中"),
            TodoItem(task="タスクB", status="未着手"),
        ]
    )
    current = TodoList(items=[TodoItem(task="タスクA", status="進行中")])

    result = analyzer.analyze(current, previous)

    assert len(result.removed_tasks) == 1
    assert result.removed_tasks[0].task_name == "タスクB"


def test_diff_analyzer_similar_task():
    """類似タスクのマッチングテスト"""
    analyzer = DiffAnalyzer()

    previous = TodoList(items=[TodoItem(task="機能Aの実装", status="進行中")])
    current = TodoList(items=[TodoItem(task="機能Aの実装（修正版）", status="進行中")])

    result = analyzer.analyze(current, previous)

    # 類似タスクとして認識される
    assert len(result.new_tasks) == 0
    assert len(result.removed_tasks) == 0


def test_diff_analyzer_completed_statuses():
    """完了ステータスのバリエーションテスト"""
    analyzer = DiffAnalyzer()

    test_cases = ["完了", "done", "Done", "DONE", "finished", "完", "済"]

    for status in test_cases:
        previous = TodoList(items=[TodoItem(task="テスト", status="進行中")])
        current = TodoList(items=[TodoItem(task="テスト", status=status)])

        result = analyzer.analyze(current, previous)
        assert (
            len(result.completed_tasks) == 1
        ), f"ステータス '{status}' が完了として認識されません"
