package hello;
import java.io.*;
import java.util.Scanner;

public class BufferedlOEx {
public static void main(String[] args) {
	FileReader fin=null;
	int c;
	try {
		fin=new FileReader("C:\\Users\\melon\\Desktop\\12345678.txt");
		BufferedOutputStream out=new BufferedOutputStream(System.out,5);
		while((c=fin.read())!=-1){
			out.write(c);
		}
		new Scanner(System.in).nextLine();
		out.flush();
		fin.close();
		out.close();
		
	}
	catch(IOException e) {
		e.printStackTrace();
		
	}
	
}
}
