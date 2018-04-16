import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;

// File defining Interface class for DB.

enum Classification{Place, Brand, None};

// DataTable with training examples in it
class DataTable{
	ArrayList<Search> searchList;
}

// A single training example
class Search{
	Query x;
	Classification y;
}

// 1-1 corresponds with a session
// Parser for Query from sr.log is in LogParser.java
// Query can be obtained by re-parsing sr.csv, which is a result of LogParser.java (or convert LogParser.java into Python)
class Query{
	String session;
	String word;
	Date date = new Date();
	String IP = "";
	String url;
	String device;
	String OS;
	String browser;
	HashMap<String, String> numResults = new HashMap<>();
	static final String[] DeviceList = {"iPhone", "Android", "Windows", "iPad", "Macintosh"};
	static final String[] OSList = {"Linux", "Mac", "Windows"};
}