package cn.yulin.english;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import org.json.*;
import java.io.*;
import java.util.*;

public final class LibraryStore {
 private final Context context;private SQLiteDatabase db;
 private static final Set<String> KINDS=new HashSet<>(Arrays.asList("words","grammar","points","questions","papers"));
 public LibraryStore(Context context){this.context=context;}
 private synchronized SQLiteDatabase database()throws Exception{
  if(db!=null&&db.isOpen())return db;
  File dir=context.getDatabasePath("library-v110.sqlite").getParentFile();if(!dir.exists())dir.mkdirs();
  File file=new File(dir,"library-v110.sqlite");
  if(!file.exists()){File tmp=new File(dir,"library-v110.tmp");try(InputStream in=context.getAssets().open("library-v110.sqlite");FileOutputStream out=new FileOutputStream(tmp)){byte[] buffer=new byte[16384];int n;while((n=in.read(buffer))!=-1)out.write(buffer,0,n);out.getFD().sync();}if(!tmp.renameTo(file))throw new IOException("Cannot install library");}
  db=SQLiteDatabase.openDatabase(file.getPath(),null,SQLiteDatabase.OPEN_READONLY);return db;
 }
 private static String escaped(String s){return s.toLowerCase(Locale.ROOT).replace("\\","\\\\").replace("%","\\%").replace("_","\\_");}
 private JSONObject summary(Cursor c)throws JSONException{JSONObject r=new JSONObject();for(int i=0;i<c.getColumnCount();i++){String name=c.getColumnName(i);if(c.isNull(i))r.put(name,JSONObject.NULL);else if(c.getType(i)==Cursor.FIELD_TYPE_INTEGER)r.put(name,c.getLong(i));else r.put(name,c.getString(i));}return r;}
 private JSONArray list(String sql,List<String> args)throws Exception{JSONArray result=new JSONArray();try(Cursor c=database().rawQuery(sql,args.toArray(new String[0]))){while(c.moveToNext())result.put(summary(c));}return result;}
 public JSONObject handle(String path,JSONObject body)throws Exception{
  SQLiteDatabase d=database();
  if(path.equals("/api/library/meta")){try(Cursor c=d.rawQuery("SELECT value FROM meta WHERE key='manifest'",null)){if(!c.moveToFirst())throw new IOException("Missing metadata");return new JSONObject(c.getString(0));}}
  String kind=body.optString("kind","words");if(!KINDS.contains(kind))throw new IllegalArgumentException("Invalid kind");
  if(path.equals("/api/library/detail")){
   String id=body.optString("id");if(id.length()>150)throw new IllegalArgumentException();JSONObject payload;
   try(Cursor c=d.rawQuery("SELECT payload FROM records WHERE kind=? AND id=?",new String[]{kind,id})){if(!c.moveToFirst())return new JSONObject().put("error","没有找到这条资料。");payload=new JSONObject(c.getString(0));}
   List<String> relatedArgs=Arrays.asList(kind,id,kind,id);
   String relation="SELECT r.kind,r.id,r.title,r.subtitle,r.grade,r.difficulty,r.status FROM records r JOIN (SELECT to_kind AS kind,to_id AS id FROM links WHERE from_kind=? AND from_id=? UNION SELECT from_kind AS kind,from_id AS id FROM links WHERE to_kind=? AND to_id=?) l ON r.kind=l.kind AND r.id=l.id ORDER BY r.kind,r.title LIMIT 60";
   return new JSONObject().put("record",payload).put("related",list(relation,relatedArgs)).put("children",list("SELECT kind,id,title,subtitle,grade,difficulty,status FROM records WHERE kind=? AND parent=? ORDER BY id LIMIT 100",Arrays.asList(kind,id)));
  }
  if(!path.equals("/api/library/query"))throw new IllegalArgumentException("Invalid route");
  String q=body.optString("query","").trim();if(q.length()>100)q=q.substring(0,100);
  List<String> args=new ArrayList<>();StringBuilder where=new StringBuilder("r.kind=?");args.add(kind);
  if(!q.isEmpty()){where.append(" AND (r.search LIKE ? ESCAPE '\\'");args.add("%"+escaped(q)+"%");if(kind.equals("words")){where.append(" OR r.id IN (SELECT record_id FROM word_lookup WHERE term=? COLLATE NOCASE)");args.add(q);}where.append(")");}
  for(String field:new String[]{"grade","status","parent","category"}){String value=body.optString(field,"");if(!value.isEmpty()&&!value.equals("all")){where.append(" AND r.").append(field).append("=?");args.add(value);}}
  String relatedKind=body.optString("relatedKind",""),relatedId=body.optString("relatedId","");
  if(KINDS.contains(relatedKind)&&!relatedId.isEmpty()){where.append(" AND EXISTS(SELECT 1 FROM links l WHERE (l.from_kind=r.kind AND l.from_id=r.id AND l.to_kind=? AND l.to_id=?) OR (l.to_kind=r.kind AND l.to_id=r.id AND l.from_kind=? AND l.from_id=?))");args.addAll(Arrays.asList(relatedKind,relatedId,relatedKind,relatedId));}
  long total;try(Cursor c=d.rawQuery("SELECT count(*) FROM records r WHERE "+where,args.toArray(new String[0]))){c.moveToFirst();total=c.getLong(0);}
  int offset=Math.max(0,body.optInt("offset",0)),limit=Math.min(40,Math.max(1,body.optInt("limit",24)));
  List<String> pageArgs=new ArrayList<>(args);String order="r.title COLLATE NOCASE,r.id";
  if(!q.isEmpty()&&kind.equals("words")){order="CASE WHEN r.title=? COLLATE NOCASE THEN 0 WHEN r.id IN (SELECT record_id FROM word_lookup WHERE term=? COLLATE NOCASE) THEN 1 ELSE 2 END,"+order;pageArgs.add(q);pageArgs.add(q);}
  pageArgs.add(String.valueOf(limit));pageArgs.add(String.valueOf(offset));
  return new JSONObject().put("total",total).put("offset",offset).put("limit",limit).put("items",list("SELECT r.kind,r.id,r.title,r.subtitle,r.grade,r.difficulty,r.status FROM records r WHERE "+where+" ORDER BY "+order+" LIMIT ? OFFSET ?",pageArgs));
 }
 public synchronized void close(){if(db!=null)db.close();}
}
