import os
import sys
from pathlib import Path

from PySide6.QtCore import QDir, QModelIndex, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QFileSystemModel,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTreeView,
    QVBoxLayout,
    QWidget,
)


class FilterDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Filter")
        self.setModal(True)

        self.pattern_input = QLineEdit(self)
        self.pattern_input.setPlaceholderText("Example: *.py;*.md;*.txt (leave empty to show all)")

        buttons_row = QHBoxLayout()
        ok_btn = QPushButton("Apply", self)
        cancel_btn = QPushButton("Cancel", self)
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        buttons_row.addStretch(1)
        buttons_row.addWidget(ok_btn)
        buttons_row.addWidget(cancel_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self.pattern_input)
        layout.addLayout(buttons_row)

    def patterns(self) -> list[str]:
        raw = self.pattern_input.text().strip()
        if not raw:
            return []
        parts = [p.strip() for p in raw.split(";")]
        return [p for p in parts if p]


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("File Tree Viewer")
        self.resize(1100, 700)

        self.model = QFileSystemModel(self)
        self.model.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot)
        self.model.setRootPath(str(Path.cwd()))
        self.model.setReadOnly(True)

        self.tree = QTreeView(self)
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(str(Path.cwd())))
        self.tree.setSortingEnabled(True)
        self.tree.sortByColumn(0, Qt.AscendingOrder)
        self.tree.setUniformRowHeights(True)
        self.tree.setAnimated(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._open_context_menu)

        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for col in (1, 2, 3):
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)

        self.search = QLineEdit(self)
        self.search.setPlaceholderText("Search in current folder (filters by name, case-insensitive)…")
        self.search.textChanged.connect(self._apply_name_filter)

        choose_btn = QPushButton("Choose folder…", self)
        choose_btn.clicked.connect(self.choose_folder)

        reset_btn = QPushButton("Reset search", self)
        reset_btn.clicked.connect(lambda: self.search.setText(""))

        top_row = QHBoxLayout()
        top_row.addWidget(choose_btn)
        top_row.addWidget(self.search, 1)
        top_row.addWidget(reset_btn)

        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.addLayout(top_row)
        layout.addWidget(self.tree, 1)
        self.setCentralWidget(container)

        self.setStatusBar(QStatusBar(self))
        self._set_status_root(Path.cwd())

        self._create_actions()
        self._create_menus()

        # Index of the “name” column used for filtering
        self.tree.setItemsExpandable(True)
        self.tree.setExpandsOnDoubleClick(True)

    def _create_actions(self) -> None:
        self.open_folder_action = QAction("Choose folder…", self)
        self.open_folder_action.setShortcut(QKeySequence.Open)
        self.open_folder_action.triggered.connect(self.choose_folder)

        self.copy_path_action = QAction("Copy path", self)
        self.copy_path_action.setShortcut(QKeySequence.Copy)
        self.copy_path_action.triggered.connect(self.copy_selected_path)

        self.reveal_action = QAction("Open in Explorer", self)
        self.reveal_action.triggered.connect(self.open_in_explorer)

        self.filter_glob_action = QAction("Filter by file patterns…", self)
        self.filter_glob_action.triggered.connect(self.filter_by_patterns)

        self.clear_filter_glob_action = QAction("Clear file pattern filter", self)
        self.clear_filter_glob_action.triggered.connect(self.clear_pattern_filter)

        self.exit_action = QAction("Exit", self)
        self.exit_action.setShortcut(QKeySequence.Quit)
        self.exit_action.triggered.connect(self.close)

    def _create_menus(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        file_menu.addAction(self.open_folder_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        view_menu = self.menuBar().addMenu("View")
        view_menu.addAction(self.filter_glob_action)
        view_menu.addAction(self.clear_filter_glob_action)

        edit_menu = self.menuBar().addMenu("Edit")
        edit_menu.addAction(self.copy_path_action)
        edit_menu.addAction(self.reveal_action)

    def _set_status_root(self, root: Path) -> None:
        self.statusBar().showMessage(f"Root: {root}")

    def choose_folder(self) -> None:
        start = self.current_root_path()
        chosen = QFileDialog.getExistingDirectory(self, "Choose folder", start)
        if not chosen:
            return
        self.set_root(chosen)

    def current_root_path(self) -> str:
        root_idx = self.tree.rootIndex()
        if root_idx.isValid():
            return self.model.filePath(root_idx)
        return str(Path.cwd())

    def set_root(self, folder: str) -> None:
        folder = os.path.abspath(folder)
        if not os.path.isdir(folder):
            QMessageBox.warning(self, "Not a folder", f"That path is not a directory:\n{folder}")
            return
        root_index = self.model.index(folder)
        self.tree.setRootIndex(root_index)
        self._set_status_root(Path(folder))
        self.search.setText("")

    def _apply_name_filter(self) -> None:
        text = self.search.text().strip().lower()
        self._filter_tree(text)

    def _filter_tree(self, needle: str) -> None:
        # Simple UI-friendly filter: collapse everything, then expand matches.
        # For large trees, a proxy model is better; this keeps the first version minimal.
        self.tree.setUpdatesEnabled(False)
        try:
            self.tree.collapseAll()
            if not needle:
                return
            root = self.tree.rootIndex()
            self._expand_matching_under(root, needle, max_nodes=4000)
        finally:
            self.tree.setUpdatesEnabled(True)

    def _expand_matching_under(self, parent: QModelIndex, needle: str, max_nodes: int) -> int:
        # Depth-first walk with a hard cap to avoid freezing on huge folders.
        remaining = max_nodes
        stack: list[QModelIndex] = [parent]
        while stack and remaining > 0:
            idx = stack.pop()
            remaining -= 1
            if not idx.isValid():
                continue
            name = self.model.fileName(idx).lower()
            if needle in name:
                # Expand the node and its parents so it becomes visible
                p = idx
                while p.isValid():
                    self.tree.expand(p)
                    p = p.parent()
            # Only traverse directories
            if self.model.isDir(idx):
                rows = self.model.rowCount(idx)
                # push children
                for r in range(rows - 1, -1, -1):
                    child = self.model.index(r, 0, idx)
                    if child.isValid():
                        stack.append(child)
        return remaining

    def selected_index(self) -> QModelIndex | None:
        sel = self.tree.selectionModel()
        if not sel:
            return None
        indexes = sel.selectedRows(0)
        if not indexes:
            return None
        return indexes[0]

    def selected_path(self) -> str | None:
        idx = self.selected_index()
        if not idx:
            return None
        return self.model.filePath(idx)

    def copy_selected_path(self) -> None:
        path = self.selected_path()
        if not path:
            return
        QApplication.clipboard().setText(path)
        self.statusBar().showMessage(f"Copied: {path}", 2500)

    def open_in_explorer(self) -> None:
        path = self.selected_path()
        if not path:
            return
        # Open folder or select file in Explorer
        if os.path.isdir(path):
            os.startfile(path)  # noqa: S606 (Windows-only)
        else:
            os.startfile(os.path.dirname(path))  # noqa: S606 (Windows-only)

    def filter_by_patterns(self) -> None:
        dlg = FilterDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return
        patterns = dlg.patterns()
        if not patterns:
            self.clear_pattern_filter()
            return
        self.model.setNameFilters(patterns)
        self.model.setNameFilterDisables(False)
        self.statusBar().showMessage(f"Filter: {';'.join(patterns)}", 4000)

    def clear_pattern_filter(self) -> None:
        self.model.setNameFilters([])
        self.model.setNameFilterDisables(True)
        self.statusBar().showMessage("File pattern filter cleared", 2500)

    def _open_context_menu(self, pos) -> None:
        idx = self.tree.indexAt(pos)
        if idx.isValid():
            self.tree.setCurrentIndex(idx)

        menu = QMenu(self)
        menu.addAction(self.copy_path_action)
        menu.addAction(self.reveal_action)
        menu.addSeparator()
        menu.addAction(self.open_folder_action)
        menu.exec(self.tree.viewport().mapToGlobal(pos))


def main() -> int:
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
