"""差分分析モジュール"""

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Optional

from .excel_reader import TodoItem, TodoList


@dataclass
class TaskChange:
    """タスクの変更情報"""

    task_name: str
    change_type: str  # "completed", "new", "modified", "unchanged", "removed"
    previous_status: Optional[str] = None
    current_status: Optional[str] = None
    details: str = ""


@dataclass
class DiffResult:
    """差分分析結果"""

    completed_tasks: list[TaskChange] = field(default_factory=list)
    new_tasks: list[TaskChange] = field(default_factory=list)
    modified_tasks: list[TaskChange] = field(default_factory=list)
    unchanged_tasks: list[TaskChange] = field(default_factory=list)
    removed_tasks: list[TaskChange] = field(default_factory=list)

    def to_text(self) -> str:
        """テキスト形式に変換"""
        lines = []

        if self.completed_tasks:
            lines.append("【完了したタスク】")
            for task in self.completed_tasks:
                lines.append(f"  - {task.task_name}")
                if task.details:
                    lines.append(f"    {task.details}")
            lines.append("")

        if self.new_tasks:
            lines.append("【新規タスク】")
            for task in self.new_tasks:
                lines.append(f"  - {task.task_name}")
                if task.current_status:
                    lines.append(f"    ステータス: {task.current_status}")
            lines.append("")

        if self.modified_tasks:
            lines.append("【変更されたタスク】")
            for task in self.modified_tasks:
                lines.append(f"  - {task.task_name}")
                lines.append(f"    {task.previous_status} → {task.current_status}")
            lines.append("")

        if self.removed_tasks:
            lines.append("【削除/中止されたタスク】")
            for task in self.removed_tasks:
                lines.append(f"  - {task.task_name}")
            lines.append("")

        if self.unchanged_tasks:
            lines.append(f"【継続中のタスク】({len(self.unchanged_tasks)}件)")
            for task in self.unchanged_tasks[:5]:  # 最大5件表示
                lines.append(f"  - {task.task_name}")
            if len(self.unchanged_tasks) > 5:
                lines.append(f"  ... 他{len(self.unchanged_tasks) - 5}件")

        return "\n".join(lines)

    def get_summary(self) -> str:
        """サマリを取得"""
        parts = []
        if self.completed_tasks:
            parts.append(f"完了: {len(self.completed_tasks)}件")
        if self.new_tasks:
            parts.append(f"新規: {len(self.new_tasks)}件")
        if self.modified_tasks:
            parts.append(f"変更: {len(self.modified_tasks)}件")
        if self.removed_tasks:
            parts.append(f"削除: {len(self.removed_tasks)}件")
        if self.unchanged_tasks:
            parts.append(f"継続: {len(self.unchanged_tasks)}件")

        return "、".join(parts) if parts else "変更なし"


class DiffAnalyzer:
    """ToDoリストの差分を分析するクラス"""

    # 完了を示すステータス
    COMPLETED_STATUSES = ["完了", "done", "closed", "finished", "完", "済"]

    # 類似度の閾値
    SIMILARITY_THRESHOLD = 0.6

    def analyze(
        self,
        current: TodoList,
        previous: Optional[TodoList] = None,
    ) -> DiffResult:
        """
        ToDoリストの差分を分析する

        Args:
            current: 現在のToDoリスト
            previous: 前回のToDoリスト（Noneの場合は全て新規扱い）

        Returns:
            差分分析結果
        """
        result = DiffResult()

        if previous is None or not previous.items:
            # 前回データなし = 全て新規
            for item in current.items:
                result.new_tasks.append(
                    TaskChange(
                        task_name=item.task,
                        change_type="new",
                        current_status=item.status,
                    )
                )
            return result

        # 前回タスクをマッピング
        previous_tasks = {item.task: item for item in previous.items}
        matched_previous = set()

        for current_item in current.items:
            # 完全一致を探す
            if current_item.task in previous_tasks:
                prev_item = previous_tasks[current_item.task]
                matched_previous.add(current_item.task)

                change = self._compare_items(prev_item, current_item)
                self._add_to_result(result, change)
            else:
                # 類似タスクを探す
                similar_task = self._find_similar_task(
                    current_item.task, previous_tasks.keys(), matched_previous
                )

                if similar_task:
                    prev_item = previous_tasks[similar_task]
                    matched_previous.add(similar_task)

                    change = self._compare_items(
                        prev_item, current_item, task_renamed=True
                    )
                    self._add_to_result(result, change)
                else:
                    # 新規タスク
                    result.new_tasks.append(
                        TaskChange(
                            task_name=current_item.task,
                            change_type="new",
                            current_status=current_item.status,
                        )
                    )

        # 削除されたタスクを検出
        for task_name, prev_item in previous_tasks.items():
            if task_name not in matched_previous:
                result.removed_tasks.append(
                    TaskChange(
                        task_name=task_name,
                        change_type="removed",
                        previous_status=prev_item.status,
                    )
                )

        return result

    def analyze_from_text(
        self,
        current_todos: TodoList,
        previous_report_text: str,
    ) -> str:
        """
        テキスト形式の前回報告から差分を分析する（AI支援用）

        Args:
            current_todos: 現在のToDoリスト
            previous_report_text: 前回の報告テキスト

        Returns:
            差分分析用のコンテキストテキスト
        """
        return f"""## 差分分析コンテキスト

### 現在のToDoリスト
{current_todos.to_text()}

### 前回の報告内容
{previous_report_text}

上記の情報を比較して、進捗状況を分析してください。"""

    def _compare_items(
        self, previous: TodoItem, current: TodoItem, task_renamed: bool = False
    ) -> TaskChange:
        """2つのタスクを比較"""
        prev_completed = self._is_completed(previous.status)
        curr_completed = self._is_completed(current.status)

        if not prev_completed and curr_completed:
            # 完了した
            return TaskChange(
                task_name=current.task,
                change_type="completed",
                previous_status=previous.status,
                current_status=current.status,
                details="前回から完了",
            )
        elif previous.status != current.status:
            # ステータス変更
            return TaskChange(
                task_name=current.task,
                change_type="modified",
                previous_status=previous.status,
                current_status=current.status,
            )
        else:
            # 変更なし
            return TaskChange(
                task_name=current.task,
                change_type="unchanged",
                current_status=current.status,
            )

    def _is_completed(self, status: str) -> bool:
        """ステータスが完了かどうかを判定"""
        if not status:
            return False
        status_lower = status.lower().strip()
        return any(cs in status_lower for cs in self.COMPLETED_STATUSES)

    def _find_similar_task(
        self,
        task_name: str,
        previous_tasks: list[str],
        already_matched: set[str],
    ) -> Optional[str]:
        """類似タスクを探す"""
        best_match = None
        best_ratio = 0.0

        for prev_task in previous_tasks:
            if prev_task in already_matched:
                continue

            ratio = SequenceMatcher(None, task_name, prev_task).ratio()
            if ratio > best_ratio and ratio >= self.SIMILARITY_THRESHOLD:
                best_ratio = ratio
                best_match = prev_task

        return best_match

    def _add_to_result(self, result: DiffResult, change: TaskChange) -> None:
        """変更をresultに追加"""
        if change.change_type == "completed":
            result.completed_tasks.append(change)
        elif change.change_type == "modified":
            result.modified_tasks.append(change)
        elif change.change_type == "unchanged":
            result.unchanged_tasks.append(change)
