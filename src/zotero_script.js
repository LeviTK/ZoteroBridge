var item = new Zotero.Item('book');
item.setField('title', {{title}});
item.setField('ISBN', {{isbn}});

var creatorsData = {{creators}};
var creators = [];
for (let c of creatorsData) {
    creators.push({
        creatorType: 'author',
        firstName: c.firstName || '',
        lastName: c.lastName || ''
    });
}
item.setCreators(creators);
item.addTag({{zotero_tag}});

await item.saveTx();
var itemKey = item.key;

await Zotero.Attachments.linkFromFile({
    file: {{file_path}},
    parentItemID: item.id
});

var libID = item.libraryID;
var collections = await Zotero.Collections.getByLibrary(libID);
var targetCol = null;
for (let col of collections) {
    if (col.name === {{zotero_collection}}) {
        targetCol = col;
        break;
    }
}
if (!targetCol) {
    targetCol = new Zotero.Collection();
    targetCol.name = {{zotero_collection}};
    targetCol.libraryID = libID;
    await targetCol.saveTx();
}
item.addToCollection(targetCol.id);
await item.saveTx();

return itemKey;
