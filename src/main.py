import urllib.request
import urllib.error
import json
import os
from calibre.gui2.actions import InterfaceAction
from calibre.gui2 import error_dialog, info_dialog
from calibre_plugins.zotero_bridge.config import prefs

class ZoteroAction(InterfaceAction):
    name = 'Send to Zotero Bridge'
    
    action_spec = ('Send to Zotero', None, 'Link Book to Zotero Locally', None)

    def genesis(self):
        self.qaction.triggered.connect(self.run)

    def _get_js_template(self):
        # 优先使用 Calibre 的 get_resources 从 zip 中读取资源
        try:
            from calibre_plugins.zotero_bridge import get_resources
            return get_resources('zotero_script.js').decode('utf-8')
        except Exception:
            # 回退到本地文件系统读取 (供开发调试时使用)
            js_path = os.path.join(os.path.dirname(__file__), 'zotero_script.js')
            with open(js_path, 'r', encoding='utf-8') as f:
                return f.read()

    def run(self):
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows:
            return info_dialog(self.gui, '提示', '请选择一本书', show=True)

        db = self.gui.current_db
        errors = []
        
        for row in rows:
            book_id = db.id(row.row())
            
            mi = db.get_metadata(book_id, index_is_id=True)
            title = mi.title
            isbn = mi.isbn if mi.isbn else ""
            authors = mi.authors

            # 支持的格式列表，按优先级排序
            supported_formats = ['PDF', 'EPUB', 'AZW3', 'MOBI']
            file_path = None
            
            for fmt in supported_formats:
                if db.has_format(book_id, fmt, index_is_id=True):
                    file_path = db.format_abspath(book_id, fmt, index_is_id=True)
                    break

            if not file_path:
                msg = f"书籍 '{title}' 没有找到支持的文件格式 ({', '.join(supported_formats)})，跳过"
                print(msg)
                errors.append(msg)
                continue

            try:
                item_key = self.send_command(title, authors, isbn, file_path)
                print(f"成功发送: {title}, Zotero Key: {item_key}")
                
                if item_key:
                    self.update_calibre_metadata(db, book_id, mi, title, item_key)
                    
            except Exception as e:
                msg = f"处理 '{title}' 时发生错误: {str(e)}"
                print(msg)
                errors.append(msg)
                continue

        self.gui.library_view.model().refresh()
        
        if errors:
            error_msg = "\n".join(errors)
            error_dialog(self.gui, '部分完成(有错误)', error_msg, show=True)
        else:
            info_dialog(self.gui, '完成', '处理完毕', show=True)

    def update_calibre_metadata(self, db, book_id, mi, title, item_key):
        """更新 Calibre 书籍元数据：添加 Zotero 链接和标签"""
        zotero_url = f"zotero://select/library/items/{item_key}"
        zotero_link_html = f'<p><strong>Zotero:</strong> <a href="{zotero_url}">{title}</a></p>'
        
        current_comments = mi.comments or ""
        if zotero_url not in current_comments:
            if current_comments:
                new_comments = f"{zotero_link_html}\n{current_comments}"
            else:
                new_comments = zotero_link_html
            mi.comments = new_comments
        
        current_tags = list(mi.tags) if mi.tags else []
        calibre_tag = prefs['CALIBRE_TAG']
        if calibre_tag not in current_tags:
            current_tags.append(calibre_tag)
            # Calibre API 要求修改元数据时最好赋值为 tuple 或者直接更新，但对于 tags 列表来说，标准做法是这样
            mi.tags = current_tags
        
        db.set_metadata(book_id, mi, set_title=False, set_authors=False)

    def send_command(self, title, authors, isbn, file_path):
        """构建 JS 并发送给 Zotero"""
        
        # 处理作者列表，尝试拆分 firstName 和 lastName
        creators_list = []
        for author in authors:
            parts = author.split(' ', 1)
            if len(parts) > 1:
                creators_list.append({"firstName": parts[0], "lastName": parts[1]})
            else:
                creators_list.append({"firstName": "", "lastName": author})
                
        js_creators_json = json.dumps(creators_list)
        # 将 title, isbn 和 file_path 也用 json 转义，生成完整的带双引号字符串，避免注入漏洞或语法错误
        js_title = json.dumps(title)
        js_isbn = json.dumps(isbn)
        js_file_path = json.dumps(file_path)
        
        js_zotero_tag = json.dumps(prefs['ZOTERO_TAG'])
        js_zotero_collection = json.dumps(prefs['ZOTERO_COLLECTION'])

        # 读取模板并替换占位符
        js_template = self._get_js_template()
        js_code = js_template.replace('{{title}}', js_title) \
                             .replace('{{isbn}}', js_isbn) \
                             .replace('{{creators}}', js_creators_json) \
                             .replace('{{zotero_tag}}', js_zotero_tag) \
                             .replace('{{file_path}}', js_file_path) \
                             .replace('{{zotero_collection}}', js_zotero_collection)

        # 3. 发送 HTTP 请求
        headers = {'Content-Type': 'text/plain'}
        zotero_pass = prefs['ZOTERO_PASS']
        if zotero_pass:
            headers['Authorization'] = f'Bearer {zotero_pass}'
        req = urllib.request.Request(
            prefs['BRIDGE_URL'], 
            data=js_code.encode('utf-8'), 
            headers=headers,
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req) as res:
                response_body = res.read().decode('utf-8', errors='replace')
                if not (200 <= res.status < 300):
                    raise Exception(f"Zotero 返回错误码: {res.status}\n响应内容: {response_body}")
                item_key = response_body.strip().strip('"')
                return item_key
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8', errors='replace')
            raise Exception(f"HTTP 错误 {e.code}: {e.reason}\n\n响应内容:\n{error_body}")

