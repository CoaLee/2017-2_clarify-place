import java.io.*;
import java.util.Date;
import java.util.HashMap;
import java.util.Locale;
import java.util.ArrayList;
import java.text.ParseException;
import java.text.SimpleDateFormat;

public class LogParser {
	enum logType{search, click};
	static ArrayList<Search> searchList = new ArrayList<>();
	static int currentSearchIndex = 0;
	public static void main(String[] args) throws IOException, ParseException {
		parseLog(logType.search, false);
		parseLog(logType.click, false);
	}
	public static void parseLog(logType type, boolean isDebug) throws IOException, ParseException{
		String logFileName, outputFileName;
		if(type == logType.click){
			logFileName = "../../../ClarifyPlace/data/cr.log";
			outputFileName = "../../../ClarifyPlace/data/cr.csv";
		}
		else{
			logFileName = "../../../ClarifyPlace/data/sr.log";
			outputFileName = "../../../ClarifyPlace/data/sr.csv";
		}
		BufferedReader br = new BufferedReader(new InputStreamReader(new FileInputStream(logFileName), "UTF8"));
		BufferedWriter out = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(outputFileName), "UTF8"));
		String line;
		
		if(isDebug){
			for(int i = 0; i < 10 ; i++){
				line = br.readLine();
				String[] words = line.split("\\s+");
				for(int j = 0; j < words.length; j++){
					System.out.println(j + " : " + words[j]);
				}
			}
		}
		else{
			while((line = br.readLine())!=null){
				if(type == logType.search){
					Search search = new Search(line);
					searchList.add(search);
					out.write(search.toString() + "\n");
				}
				if(type == logType.click){
					Click click = new Click(line);
					int i;
					for(i = currentSearchIndex; i < searchList.size(); i++){
						Search search = searchList.get(i);
						if(click.getSession() == search.getSession()){
							click.setSearch(search);
							currentSearchIndex = i;
							break;
						}
					}
					if(i == searchList.size()){
						System.out.println("There is no corresponding search for " + click.toString());
					}
					out.write(click.toString() + "\n");
				}
			}
		}
	}
}

class Search{
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
	
	public Search(String log) throws ParseException{
		String[] words = log.split("[()]");
		
		String[] basicInfo = words[0].split("\\s+");
		IP = basicInfo[1];
		SimpleDateFormat dateFormat = new SimpleDateFormat("[dd/MMM/yyyy:HH:mm:ss", Locale.US);
		date = dateFormat.parse(basicInfo[4]);
		url = basicInfo[0] + basicInfo[7];
		
		String deviceOSInfo = "";
		try{
			deviceOSInfo = words[1];
		}
		catch(ArrayIndexOutOfBoundsException e){
			
		}
		if(deviceOSInfo != ""){
			String[] deviceOS = getDeviceAndOSFrom(deviceOSInfo);
			device = deviceOS[0];
			OS = deviceOS[1];
			if(device == "" || OS == ""){
				System.out.println(deviceOSInfo);
			}
		}
		
		String[] lastInfo = words[words.length - 1].split("\\s+");
		int sessionIndex = -1;
		for(int i = 0 ; i < lastInfo.length; i++){
			if(lastInfo[i].startsWith("Tk")){
				sessionIndex = i;
				break;
			}
		}
		try{
			String[] numStrings = lastInfo[sessionIndex - 4].split(":");
			for(int i = 3; i < numStrings.length; i+=2){
				numResults.put(numStrings[i], numStrings[i+1]);
			}
			session = lastInfo[sessionIndex];
			word = lastInfo[sessionIndex+2];
		}
		catch(ArrayIndexOutOfBoundsException e){
			for(int i = 0; i < lastInfo.length; i++)
				System.out.println(i + " : " + lastInfo[i]);
		}
	}
	
	public String toString(){
		return session + "," + word + "," + date + "," + IP + "," + url + "," + device + "," + OS + "," + 
				browser + "," + numResults;
	}
	
	private static String[] getDeviceAndOSFrom(String info){
		String device = "";
		String OS = "";
		for(int i = 0; i < DeviceList.length; i++){
			String str = DeviceList[i];
			if(info.contains(str)){
				device = str;
				break;
			}
		}
		for(int i = 0; i < OSList.length; i++){
			String str = OSList[i];
			if(info.contains(str)){
				OS = str;
				break;
			}
		}
		String[] result = {device, OS};
		return result;
	}
	public String getSession(){	return session;}
}

class Click{
	String session;
	Search search;
	Date date;
	String action;
	HashMap<String, String> values = new HashMap<>();
	String url;
	
	public Click(String log) throws ParseException{
		String[] words = log.split("\\s+");
		SimpleDateFormat dateFormat = new SimpleDateFormat("[dd/MMM/yyyy:HH:mm:ss", Locale.US);
		date = dateFormat.parse(words[3]);
		
		String[] valueWords = words[6].split("&");
		for(int i = 0; i < valueWords.length; i++){
			String[] valueWord = valueWords[i].split("=");
			if(valueWord.length == 1)
				values.put(valueWord[0], "");
			else values.put(valueWord[0], valueWord[1]);
		}
		session = values.get("p");
		url = values.get("u");
		action = values.get("a");
	}
	public String toString(){
		return session + ","  + date + "," + action + "," + url + "," + values;
	}
	public String getSession(){	return session;	}
	public void setSearch(Search search){	this.search = search;}
}