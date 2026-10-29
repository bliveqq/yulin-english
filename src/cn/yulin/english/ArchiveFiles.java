package cn.yulin.english;
import android.content.*;
import android.database.Cursor;
import android.net.Uri;
import android.provider.DocumentsContract;
import java.io.IOException;
/** Resolve only relative paths beneath the user-selected document tree. */
public final class ArchiveFiles {
 public static Uri resolve(Context context,Uri tree,String relative)throws Exception{
  if(relative.length()>1500||relative.startsWith("/")||relative.contains("\\"))throw new IOException("Invalid path");
  String id=DocumentsContract.getTreeDocumentId(tree);
  for(String part:relative.split("/")){
   if(part.isEmpty()||part.equals(".")||part.equals(".."))throw new IOException("Invalid path");
   Uri children=DocumentsContract.buildChildDocumentsUriUsingTree(tree,id);String next=null;
   try(Cursor c=context.getContentResolver().query(children,new String[]{DocumentsContract.Document.COLUMN_DOCUMENT_ID,DocumentsContract.Document.COLUMN_DISPLAY_NAME},null,null,null)){
    if(c!=null)while(c.moveToNext())if(part.equals(c.getString(1))){next=c.getString(0);break;}
   }
   if(next==null)throw new IOException("File not found");id=next;
  }
  return DocumentsContract.buildDocumentUriUsingTree(tree,id);
 }
}
