import urllib.request
import urllib.error
import json
from calibre.gui2.actions import InterfaceAction
from calibre.gui2 import error_dialog, info_dialog

# --- 你的配置 ---
ZOTERO_PASS = 'CTT'  # 必须与 Zotero 配置一致
BRIDGE_URL  = 'http://127.0.0.1:23119/debug-bridge/execute'
ZOTERO_COLLECTION = '书籍'  # Zotero 中的目标文件夹名
ZOTERO_TAG = 'Calibre'  # Zotero 中的标签
CALIBRE_TAG = 'zotero'  # Calibre 中的标签

class ZoteroAction(InterfaceAction):
    name = 'Send to Zotero Bridge'
    
    action_spec = ('Send to Zotero', None, 'Link PDF to Zotero Locally', None)

    def genesis(self):
        self.qaction.triggered.connect(self.run)

    def run(self):
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows:
            return info_dialog(self.gui, '提示', '请选择一本书', show=True)

        db = self.gui.current_db
        
        for row in rows:
            book_id = db.id(row.row())
            
            mi = db.get_metadata(book_id, index_is_id=True)
            title = mi.title
            isbn = mi.isbn if mi.isbn else ""
            authors = mi.authors

            if db.has_format(book_id, 'PDF', index_is_id=True):
                pdf_path = db.format_abspath(book_id, 'PDF', index_is_id=True)
            else:
                print(f"书籍 {title} 没有 PDF，跳过")
                continue

            try:
                item_key = self.send_command(title, authors, isbn, pdf_path)
                print(f"成功发送: {title}, Zotero Key: {item_key}")
                
                if item_key:
                    self.update_calibre_metadata(db, book_id, mi, title, item_key)
                    
            except Exception as e:
                error_dialog(self.gui, '通信错误', str(e), show=True)
                break

        self.gui.library_view.model().refresh()
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
        if CALIBRE_TAG not in current_tags:
            current_tags.append(CALIBRE_TAG)
            mi.tags = current_tags
        
        db.set_metadata(book_id, mi, set_title=False, set_authors=False)

    def send_command(self, title, authors, isbn, pdf_path):
        """构建 JS 并发送给 Zotero"""
        
        # 1. 数据清洗 (非常重要：防止 JS 语法错误)
        # Windows 路径: C:\Book -> C:\\Book
        js_pdf_path = pdf_path.replace('\\', '\\\\')
        
        # Python 中要表示字符串 \' (即 JS 里的转义单引号)，需要写成 "\\'"
        js_title = title.replace("'", "\\'")
        
        # 处理作者列表
        js_authors_list = []
        for a in authors:
            safe_a = a.replace("'", "\\'")
            js_authors_list.append(f"'{safe_a}'")
        js_authors_str = "[" + ",".join(js_authors_list) + "]"

        # 2. 构建 JavaScript Payload (不使用 async IIFE，直接写)
        js_code = f"""
var item = new Zotero.Item('book');
item.setField('title', '{js_title}');
item.setField('ISBN', '{isbn}');

var authorList = {js_authors_str};
var creators = [];
for (let a of authorList) {{
    creators.push({{
        creatorType: 'author', 
        lastName: a
    }});
}}
item.setCreators(creators);
item.addTag('{ZOTERO_TAG}');

await item.saveTx();
var itemKey = item.key;

await Zotero.Attachments.linkFromFile({{
    file: '{js_pdf_path}',
    parentItemID: item.id
}});

var libID = item.libraryID;
var collections = await Zotero.Collections.getByLibrary(libID);
var targetCol = null;
for (let col of collections) {{
    if (col.name === '{ZOTERO_COLLECTION}') {{
        targetCol = col;
        break;
    }}
}}
if (!targetCol) {{
    targetCol = new Zotero.Collection();
    targetCol.name = '{ZOTERO_COLLECTION}';
    targetCol.libraryID = libID;
    await targetCol.saveTx();
}}
item.addToCollection(targetCol.id);
await item.saveTx();

return itemKey;
        """

        # 3. 发送 HTTP 请求
        headers = {'Content-Type': 'text/plain'}
        if ZOTERO_PASS:
            headers['Authorization'] = f'Bearer {ZOTERO_PASS}'
        req = urllib.request.Request(
            BRIDGE_URL, 
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
            raise Exception(f"HTTP 错误 {e.code}: {e.reason}\n\n响应内容:\n{error_body}\n\n发送的JS代码:\n{js_code}")
