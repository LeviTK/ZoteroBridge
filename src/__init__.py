from calibre.customize import InterfaceActionBase

class SendToZoteroPlugin(InterfaceActionBase):
    # --- 插件元数据 ---
    name                = 'Send to Zotero Bridge'
    description         = '通过本地 Debug Bridge 将书籍链接到 Zotero'
    supported_platforms = ['windows', 'osx', 'linux']
    author              = 'Gemini User'
    version             = (1, 1, 1)
    minimum_calibre_version = (5, 0, 0)

    # --- 关键配置 ---
    # 指向实际执行逻辑的类路径：文件名.类名
    # 注意：这里的 send_to_zotero_bridge 应该是 Calibre 根据插件名称生成的 ID
    actual_plugin       = 'calibre_plugins.zotero_bridge.main:ZoteroAction'

    def is_customizable(self):
        # 启用配置界面
        return True

    def config_widget(self):
        '''
        返回一个 QWidget 用于用户自定义配置。
        '''
        from calibre_plugins.zotero_bridge.config import ConfigWidget
        return ConfigWidget()

    def save_settings(self, config_widget):
        '''
        保存用户在配置界面中做的更改。
        '''
        config_widget.save_settings()

