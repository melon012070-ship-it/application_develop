package Hellowordl;
import java.util.Scanner;

public class Rectangle {
public static void main(String[] args)
{System.out.println("이름,도시,나이,체중,독신 여부를 빈칸으로 분리하여 입력하세요");
Scanner scanner=new Scanner(System.in);

String name=scanner.next();
System.out.println("이름"+name+",");

String city=scanner.next();
System.out.println("도시"+city+",");

int age=scanner.nextInt();
System.out.println("나이"+age+",");

double weight=scanner.nextDouble();
System.out.println("체중"+weight+",");

boolean isSingle=scanner.nextBoolean();
System.out.println("독신"+isSingle+",");

scanner.close();

}
}
