import os
from qt.core import QWidget, QVBoxLayout, QLabel, QLineEdit, QGroupBox, QFormLayout
from calibre.utils.config import JSONConfig

# 定义持久化配置对象
prefs = JSONConfig('plugins/zotero_bridge')

# 设置默认值
prefs.defaults['ZOTERO_PASS'] = 'CTT'
prefs.defaults['BRIDGE_URL'] = 'http://127.0.0.1:23119/debug-bridge/execute'
prefs.defaults['ZOTERO_COLLECTION'] = '书籍'
prefs.defaults['ZOTERO_TAG'] = 'Calibre'
prefs.defaults['CALIBRE_TAG'] = 'zotero'

class ConfigWidget(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.l = QVBoxLayout()
        self.setLayout(self.l)

        # 1. Zotero API 配置
        self.api_group = QGroupBox('Zotero Debug Bridge 配置')
        self.api_layout = QFormLayout()
        self.api_group.setLayout(self.api_layout)
        
        self.bridge_url_edit = QLineEdit(self)
        self.bridge_url_edit.setText(prefs['BRIDGE_URL'])
        self.api_layout.addRow(QLabel('Bridge URL:'), self.bridge_url_edit)
        
        self.password_edit = QLineEdit(self)
        self.password_edit.setText(prefs['ZOTERO_PASS'])
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.api_layout.addRow(QLabel('Password:'), self.password_edit)

        self.l.addWidget(self.api_group)

        # 2. 同步配置
        self.sync_group = QGroupBox('同步行为配置')
        self.sync_layout = QFormLayout()
        self.sync_group.setLayout(self.sync_layout)

        self.zotero_collection_edit = QLineEdit(self)
        self.zotero_collection_edit.setText(prefs['ZOTERO_COLLECTION'])
        self.sync_layout.addRow(QLabel('目标 Zotero 文件夹 (Collection):'), self.zotero_collection_edit)

        self.zotero_tag_edit = QLineEdit(self)
        self.zotero_tag_edit.setText(prefs['ZOTERO_TAG'])
        self.sync_layout.addRow(QLabel('添加到 Zotero 的标签:'), self.zotero_tag_edit)

        self.calibre_tag_edit = QLineEdit(self)
        self.calibre_tag_edit.setText(prefs['CALIBRE_TAG'])
        self.sync_layout.addRow(QLabel('处理后添加给 Calibre 的标签:'), self.calibre_tag_edit)

        self.l.addWidget(self.sync_group)
        self.l.addStretch(1)

    def save_settings(self):
        """当用户点击保存按钮时被调用"""
        prefs['BRIDGE_URL'] = self.bridge_url_edit.text().strip()
        prefs['ZOTERO_PASS'] = self.password_edit.text()
        prefs['ZOTERO_COLLECTION'] = self.zotero_collection_edit.text().strip()
        prefs['ZOTERO_TAG'] = self.zotero_tag_edit.text().strip()
        prefs['CALIBRE_TAG'] = self.calibre_tag_edit.text().strip()
