from calibre.customize import InterfaceActionBase

class SendToZoteroPlugin(InterfaceActionBase):
    # --- 插件元数据 ---
    name                = 'Send to Zotero Bridge'
    description         = '通过本地 Debug Bridge 将书籍链接到 Zotero'
    supported_platforms = ['windows', 'osx', 'linux']
    author              = 'Gemini User'
    version             = (1, 0, 0)
    minimum_calibre_version = (5, 0, 0)

    # --- 关键配置 ---
    # 指向实际执行逻辑的类路径：文件名.类名
    # 注意：这里的 send_to_zotero_bridge 应该是 Calibre 根据插件名称生成的 ID
    actual_plugin       = 'calibre_plugins.zotero_bridge.main:ZoteroAction'

    def is_customizable(self):
        # 如果你想做配置界面（填密码等），这里返回 True
        return False
